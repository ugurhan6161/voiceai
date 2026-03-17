"""
VoiceAI Platform — Faturalama Celery Tasks
Kullanım kaydetme, gecikme kontrolü, otomatik fatura.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
from celery_app import celery

logger = logging.getLogger(__name__)


async def _get_db_conn():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "voiceai-postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
    )


@celery.task(name="billing.kullanim_kaydet", queue="billing")
def kullanim_kaydet():
    """
    Her gece gece yarısı Redis sayaçlarını PostgreSQL'e kaydet.
    """
    import asyncio
    import redis

    async def _kaydet():
        redis_host = os.getenv("REDIS_HOST", "voiceai-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_pass = os.getenv("REDIS_PASSWORD", "")

        if redis_pass:
            r = redis.Redis(host=redis_host, port=redis_port, password=redis_pass, decode_responses=True)
        else:
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

        conn = await _get_db_conn()
        try:
            now = datetime.now()
            # Redis'teki tüm firma sayaçlarını tara
            keys = r.keys("voiceai:kullanim:*")
            for key in keys:
                parts = key.split(":")
                if len(parts) < 4:
                    continue
                firma_id = int(parts[2])
                tip = parts[3]  # cagri veya sms

                deger = int(r.get(key) or 0)
                if deger == 0:
                    continue

                if tip == "cagri":
                    await conn.execute(
                        """
                        INSERT INTO shared.kullanim_sayaclari (firma_id, ay, yil, cagri_sayisi)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (firma_id, ay, yil)
                        DO UPDATE SET cagri_sayisi = shared.kullanim_sayaclari.cagri_sayisi + $4,
                                      updated_at = NOW()
                        """,
                        firma_id, now.month, now.year, deger
                    )
                elif tip == "sms":
                    await conn.execute(
                        """
                        INSERT INTO shared.kullanim_sayaclari (firma_id, ay, yil, sms_sayisi)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (firma_id, ay, yil)
                        DO UPDATE SET sms_sayisi = shared.kullanim_sayaclari.sms_sayisi + $4,
                                      updated_at = NOW()
                        """,
                        firma_id, now.month, now.year, deger
                    )
                # Sayacı sıfırla
                r.delete(key)

            logger.info(f"Kullanım sayaçları kaydedildi: {len(keys)} kayıt")
        finally:
            await conn.close()
            r.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_kaydet())
    loop.close()


@celery.task(name="billing.gecikme_kontrol", queue="billing")
def gecikme_kontrol():
    """
    Her gün gecikmiş ödemeleri kontrol et ve otomatik aksiyon al.
    Gün 3: Hatırlatma SMS
    Gün 7: Uyarı SMS
    Gün 10: Son uyarı SMS
    Gün 15: Firma durdur
    """
    import asyncio

    async def _kontrol():
        from services.sms_service import NetgsmSMSService

        conn = await _get_db_conn()
        sms = NetgsmSMSService()

        try:
            bugun = datetime.now().date()

            # Gecikmiş faturaları al
            faturalar = await conn.fetch(
                """
                SELECT f.id, f.firma_id, f.toplam, f.vade_tarihi,
                       fi.email, fi.telefon, fi.ad as firma_adi,
                       (bugun - f.vade_tarihi) as gecikme_gun
                FROM shared.faturalar f
                JOIN shared.firmalar fi ON f.firma_id = fi.id
                WHERE f.durum = 'bekliyor'
                AND f.vade_tarihi < $1
                AND fi.is_deleted = FALSE
                """,
                bugun
            )

            for fatura in faturalar:
                gecikme = fatura['gecikme_gun'].days if hasattr(fatura['gecikme_gun'], 'days') else int(fatura['gecikme_gun'])
                firma_id = fatura['firma_id']
                telefon = fatura['telefon']
                firma_adi = fatura['firma_adi']
                tutar = fatura['toplam']

                if gecikme == 3:
                    mesaj = (
                        f"Sayın {firma_adi}, {tutar} TL tutarındaki faturanız "
                        f"3 gündür ödenmemiş. Lütfen ödeme yapınız. VoiceAI"
                    )
                    if telefon:
                        await sms.send_sms(telefon, mesaj)
                    logger.info(f"Gecikme hatırlatma (3 gün): firma {firma_id}")

                elif gecikme == 7:
                    mesaj = (
                        f"Sayın {firma_adi}, {tutar} TL tutarındaki faturanız "
                        f"7 gündür ödenmemiş. Hizmetiniz kesilebilir. VoiceAI"
                    )
                    if telefon:
                        await sms.send_sms(telefon, mesaj)
                    logger.info(f"Gecikme uyarı (7 gün): firma {firma_id}")

                elif gecikme == 10:
                    mesaj = (
                        f"Sayın {firma_adi}, SON UYARI: {tutar} TL tutarındaki "
                        f"faturanız 10 gündür ödenmemiş. 5 gün içinde ödenmezse "
                        f"hizmetiniz durdurulacak. VoiceAI"
                    )
                    if telefon:
                        await sms.send_sms(telefon, mesaj)
                    logger.info(f"Gecikme son uyarı (10 gün): firma {firma_id}")

                elif gecikme >= 15:
                    # Firmayı durdur
                    await conn.execute(
                        """
                        UPDATE shared.firmalar
                        SET durum = 'durduruldu', updated_at = NOW()
                        WHERE id = $1 AND durum = 'aktif'
                        """,
                        firma_id
                    )
                    mesaj = (
                        f"Sayın {firma_adi}, ödeme yapılmadığı için hizmetiniz "
                        f"durdurulmuştur. Ödeme sonrası otomatik aktif edilecektir. VoiceAI"
                    )
                    if telefon:
                        await sms.send_sms(telefon, mesaj)
                    logger.warning(f"Firma durduruldu (15 gün gecikme): firma {firma_id}")

        finally:
            await conn.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_kontrol())
    loop.close()


@celery.task(name="billing.odeme_alindi", queue="billing")
def odeme_alindi(firma_id: int, fatura_id: int, tutar: float):
    """
    Ödeme alındığında firmayı otomatik aktif et.
    """
    import asyncio

    async def _isle():
        conn = await _get_db_conn()
        try:
            # Faturayı güncelle
            await conn.execute(
                """
                UPDATE shared.faturalar
                SET durum = 'odendi', odeme_tarihi = NOW()
                WHERE id = $1
                """,
                fatura_id
            )

            # Firmayı aktif et
            await conn.execute(
                """
                UPDATE shared.firmalar
                SET durum = 'aktif', updated_at = NOW()
                WHERE id = $1 AND durum = 'durduruldu'
                """,
                firma_id
            )

            # Firma bilgilerini al
            firma = await conn.fetchrow(
                "SELECT ad, telefon FROM shared.firmalar WHERE id = $1", firma_id
            )

            if firma and firma['telefon']:
                from services.sms_service import NetgsmSMSService
                sms = NetgsmSMSService()
                mesaj = (
                    f"Sayın {firma['ad']}, {tutar} TL ödemeniz alındı. "
                    f"Hizmetiniz aktif edildi. Teşekkürler, VoiceAI"
                )
                await sms.send_sms(firma['telefon'], mesaj)

            logger.info(f"Ödeme işlendi: firma {firma_id}, fatura {fatura_id}")

        finally:
            await conn.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_isle())
    loop.close()


@celery.task(name="callback.geri_arama_isle", queue="callback")
def geri_arama_isle():
    """
    Geri arama kuyruğunu işle.
    Her gün sabah 8'de çalışır.
    """
    import asyncio

    async def _isle():
        from services.callback_service import CallbackService
        import json

        service = CallbackService()

        # Kuyruktaki tüm bekleyen aramaları işle
        islenen = 0
        while True:
            kayit = await service.kuyruktan_al()
            if not kayit:
                break

            kayit["deneme_sayisi"] = kayit.get("deneme_sayisi", 0) + 1

            if kayit["deneme_sayisi"] > int(os.getenv("CALLBACK_MAX_DENEME", "3")):
                await service.basarisiz_isle(kayit)
            else:
                sonuc = await service.geri_ara(kayit)
                if not sonuc.get("success"):
                    # Başarısız, tekrar kuyruğa ekle
                    kayit["durum"] = "bekliyor"
                    kayit["sonraki_deneme"] = (
                        datetime.now() + timedelta(hours=2)
                    ).isoformat()

                    import redis as sync_redis
                    redis_host = os.getenv("REDIS_HOST", "voiceai-redis")
                    redis_port = int(os.getenv("REDIS_PORT", "6379"))
                    redis_pass = os.getenv("REDIS_PASSWORD", "")
                    if redis_pass:
                        r = sync_redis.Redis(host=redis_host, port=redis_port, password=redis_pass)
                    else:
                        r = sync_redis.Redis(host=redis_host, port=redis_port)
                    r.lpush("voiceai:geri_arama_kuyrugu", json.dumps(kayit))
                    r.close()

            islenen += 1

        logger.info(f"Geri arama kuyruğu işlendi: {islenen} kayıt")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_isle())
    loop.close()
