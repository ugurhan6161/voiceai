"""
VoiceAI Platform — Geri Arama Kuyruğu Servisi
Meşgul çağrıları kaydeder, Celery task ile geri arar,
başarısız aramalarda SMS bildirir.
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "voiceai-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
CALLBACK_QUEUE_KEY = "voiceai:geri_arama_kuyrugu"
MAX_DENEME = int(os.getenv("CALLBACK_MAX_DENEME", "3"))


async def _get_redis():
    """Redis bağlantısı"""
    if REDIS_PASSWORD:
        return await aioredis.from_url(
            f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
        )
    return await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/0")


async def _get_db_conn():
    """PostgreSQL bağlantısı"""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "voiceai-postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
    )


class CallbackService:
    """
    Geri arama kuyruğu yöneticisi.
    Redis'te kuyruk tutar, PostgreSQL'e loglar.
    """

    async def mesgul_kaydet(
        self,
        telefon: str,
        firma_id: int,
        schema: str,
        musteri_ad: Optional[str] = None,
        notlar: Optional[str] = None,
    ) -> dict:
        """
        Meşgul çağrıyı geri arama kuyruğuna ekle.

        Args:
            telefon: Arayan telefon numarası
            firma_id: Firma ID
            schema: Firma schema adı
            musteri_ad: Müşteri adı (biliniyorsa)
            notlar: Ek notlar

        Returns:
            {"success": bool, "kuyruk_id": str}
        """
        import json
        import uuid

        kuyruk_id = str(uuid.uuid4())[:8]
        kayit = {
            "id": kuyruk_id,
            "telefon": telefon,
            "firma_id": firma_id,
            "schema": schema,
            "musteri_ad": musteri_ad or "",
            "notlar": notlar or "",
            "deneme_sayisi": 0,
            "olusturma_zamani": datetime.now().isoformat(),
            "sonraki_deneme": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "durum": "bekliyor",  # bekliyor, deneniyor, tamamlandi, basarisiz
        }

        try:
            # Redis kuyruğuna ekle
            r = await _get_redis()
            await r.lpush(CALLBACK_QUEUE_KEY, json.dumps(kayit))
            await r.close()

            # PostgreSQL'e de kaydet
            conn = await _get_db_conn()
            try:
                await conn.execute(
                    """
                    INSERT INTO shared.geri_arama_kuyrugu
                    (kuyruk_id, telefon, firma_id, musteri_ad, notlar, durum, olusturma_zamani)
                    VALUES ($1, $2, $3, $4, $5, 'bekliyor', NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    kuyruk_id, telefon, firma_id, musteri_ad, notlar
                )
            except Exception as db_err:
                logger.warning(f"DB kayıt hatası (Redis'e kaydedildi): {db_err}")
            finally:
                await conn.close()

            logger.info(f"Geri arama kuyruğuna eklendi: {telefon} (ID: {kuyruk_id})")
            return {"success": True, "kuyruk_id": kuyruk_id}

        except Exception as e:
            logger.error(f"Geri arama kayıt hatası: {e}")
            return {"success": False, "error": str(e)}

    async def kuyruktan_al(self) -> Optional[dict]:
        """
        Kuyruktaki bir sonraki geri aramayı al.
        Zamanı gelmiş kayıtları döndürür.
        """
        import json

        try:
            r = await _get_redis()
            # Kuyruktaki tüm kayıtları kontrol et
            kuyruk_uzunlugu = await r.llen(CALLBACK_QUEUE_KEY)

            for _ in range(kuyruk_uzunlugu):
                kayit_json = await r.rpop(CALLBACK_QUEUE_KEY)
                if not kayit_json:
                    break

                kayit = json.loads(kayit_json)

                # Zamanı geldi mi?
                sonraki = datetime.fromisoformat(kayit["sonraki_deneme"])
                if datetime.now() >= sonraki and kayit["durum"] == "bekliyor":
                    await r.close()
                    return kayit
                else:
                    # Zamanı gelmemiş, geri koy
                    await r.lpush(CALLBACK_QUEUE_KEY, kayit_json)

            await r.close()
            return None

        except Exception as e:
            logger.error(f"Kuyruktan alma hatası: {e}")
            return None

    async def geri_ara(self, kayit: dict) -> dict:
        """
        Asterisk ARI üzerinden geri arama yap.

        Args:
            kayit: Kuyruk kaydı

        Returns:
            {"success": bool, "message": str}
        """
        import aiohttp

        telefon = kayit["telefon"]
        firma_id = kayit["firma_id"]

        ari_base = os.getenv("ARI_BASE_URL", "http://172.17.0.1:8088")
        ari_user = os.getenv("ARI_USERNAME", "voiceai")
        ari_pass = os.getenv("ARI_PASSWORD", "voiceai123")

        try:
            async with aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(ari_user, ari_pass)
            ) as session:
                # Outbound çağrı başlat
                url = f"{ari_base}/ari/channels"
                payload = {
                    "endpoint": f"PJSIP/{telefon}@trunk",
                    "app": "voiceai",
                    "appArgs": f"callback,{firma_id}",
                    "callerId": os.getenv("CALLBACK_CALLER_ID", "VoiceAI"),
                    "timeout": 30,
                }
                async with session.post(url, json=payload) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Geri arama başlatıldı: {telefon}")
                        return {"success": True, "message": "Geri arama başlatıldı"}
                    else:
                        body = await resp.text()
                        logger.error(f"Geri arama başlatılamadı: {resp.status} {body}")
                        return {"success": False, "message": f"ARI hatası: {resp.status}"}

        except Exception as e:
            logger.error(f"Geri arama hatası: {e}")
            return {"success": False, "message": str(e)}

    async def basarisiz_isle(self, kayit: dict):
        """
        Maksimum deneme sayısına ulaşıldığında SMS bildir.
        """
        from services.sms_service import NetgsmSMSService

        telefon = kayit["telefon"]
        firma_id = kayit["firma_id"]

        # Firma adını al
        try:
            conn = await _get_db_conn()
            firma_adi = await conn.fetchval(
                "SELECT ad FROM shared.firmalar WHERE id = $1", firma_id
            )
            await conn.close()
        except Exception:
            firma_adi = "VoiceAI"

        mesaj = (
            f"Sayın müşterimiz, sizi {MAX_DENEME} kez aradık ancak ulaşamadık. "
            f"Lütfen bizi arayın. {firma_adi}"
        )

        sms = NetgsmSMSService()
        await sms.send_sms(telefon, mesaj)
        logger.info(f"Başarısız geri arama SMS gönderildi: {telefon}")

        # DB'de durumu güncelle
        try:
            conn = await _get_db_conn()
            await conn.execute(
                """
                UPDATE shared.geri_arama_kuyrugu
                SET durum = 'basarisiz', updated_at = NOW()
                WHERE kuyruk_id = $1
                """,
                kayit.get("id", "")
            )
            await conn.close()
        except Exception as e:
            logger.warning(f"DB güncelleme hatası: {e}")


# ── Singleton ─────────────────────────────────────────────────
_callback_service: Optional[CallbackService] = None


def get_callback_service() -> CallbackService:
    global _callback_service
    if _callback_service is None:
        _callback_service = CallbackService()
    return _callback_service
