"""
VoiceAI Platform — SMS Celery Tasks
Otomatik SMS tetikleyicileri: rezervasyon onayı, randevu hatırlatma, sipariş onayı
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
from celery_app import celery
from services.sms_service import NetgsmSMSService

logger = logging.getLogger(__name__)


async def _get_db_conn():
    """PostgreSQL bağlantısı"""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "voiceai-postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
    )


# ── REZERVASYON SMS ───────────────────────────────────────────

@celery.task(name="sms.rezervasyon_onay", queue="sms", bind=True, max_retries=3)
def rezervasyon_onay_sms(self, firma_id: int, rezervasyon_id: int, schema: str):
    """
    Rezervasyon onaylandığında otomatik SMS gönder.
    Otel, pansiyon, kamp vb. için kullanılır.
    """
    import asyncio

    async def _gonder():
        conn = await _get_db_conn()
        try:
            row = await conn.fetchrow(
                f"""
                SELECT r.musteri_ad, r.telefon, r.tarih, r.saat,
                       r.kisi_sayisi, o.tip as oda_tipi, r.sure,
                       f.ad as firma_adi
                FROM {schema}.rezervasyonlar r
                LEFT JOIN {schema}.odalar o ON r.oda_id = o.id
                JOIN shared.firmalar f ON f.id = $1
                WHERE r.id = $2
                """,
                firma_id, rezervasyon_id
            )
            if not row:
                logger.warning(f"Rezervasyon bulunamadı: {rezervasyon_id}")
                return

            mesaj = (
                f"Sayın {row['musteri_ad']},\n"
                f"Rezervasyonunuz onaylandı!\n"
                f"Tarih: {row['tarih'].strftime('%d.%m.%Y')}\n"
                f"Saat: {row['saat']}\n"
                f"Kişi: {row['kisi_sayisi']}\n"
                f"Teşekkürler, {row['firma_adi']}"
            )

            sms = NetgsmSMSService()
            sonuc = await sms.send_sms(row['telefon'], mesaj)

            if sonuc.get("success"):
                await conn.execute(
                    f"UPDATE {schema}.rezervasyonlar SET sms_gonderildi = TRUE WHERE id = $1",
                    rezervasyon_id
                )
                logger.info(f"Rezervasyon onay SMS gönderildi: {rezervasyon_id}")
            else:
                logger.error(f"SMS gönderilemedi: {sonuc.get('error')}")

        finally:
            await conn.close()

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_gonder())
        loop.close()
    except Exception as exc:
        logger.error(f"rezervasyon_onay_sms hatası: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ── RANDEVU SMS ───────────────────────────────────────────────

@celery.task(name="sms.randevu_onay", queue="sms", bind=True, max_retries=3)
def randevu_onay_sms(self, firma_id: int, randevu_id: int, schema: str):
    """
    Randevu onaylandığında otomatik SMS gönder.
    Klinik, kuaför, spa vb. için kullanılır.
    """
    import asyncio

    async def _gonder():
        conn = await _get_db_conn()
        try:
            row = await conn.fetchrow(
                f"""
                SELECT r.hasta_ad, r.hasta_telefon, r.tarih, r.saat,
                       d.ad as doktor_ad, d.uzmanlik,
                       f.ad as firma_adi
                FROM {schema}.randevular r
                LEFT JOIN {schema}.doktorlar d ON r.doktor_id = d.id
                JOIN shared.firmalar f ON f.id = $1
                WHERE r.id = $2
                """,
                firma_id, randevu_id
            )
            if not row:
                logger.warning(f"Randevu bulunamadı: {randevu_id}")
                return

            doktor_bilgi = f"\nDoktor: {row['doktor_ad']}" if row.get('doktor_ad') else ""
            mesaj = (
                f"Sayın {row['hasta_ad']},\n"
                f"Randevunuz onaylandı!\n"
                f"Tarih: {row['tarih'].strftime('%d.%m.%Y')}\n"
                f"Saat: {row['saat']}"
                f"{doktor_bilgi}\n"
                f"Teşekkürler, {row['firma_adi']}"
            )

            sms = NetgsmSMSService()
            sonuc = await sms.send_sms(row['hasta_telefon'], mesaj)

            if sonuc.get("success"):
                await conn.execute(
                    f"UPDATE {schema}.randevular SET sms_gonderildi = TRUE WHERE id = $1",
                    randevu_id
                )
                logger.info(f"Randevu onay SMS gönderildi: {randevu_id}")
            else:
                logger.error(f"SMS gönderilemedi: {sonuc.get('error')}")

        finally:
            await conn.close()

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_gonder())
        loop.close()
    except Exception as exc:
        logger.error(f"randevu_onay_sms hatası: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery.task(name="sms.randevu_hatirlatma", queue="sms")
def randevu_hatirlatma_gonder():
    """
    Celery Beat task: Her saat çalışır.
    24 saat sonraki randevular için hatırlatma SMS'i gönderir.
    """
    import asyncio

    async def _gonder():
        conn = await _get_db_conn()
        try:
            # Tüm aktif firmaları al
            firmalar = await conn.fetch(
                "SELECT id, schema_adi FROM shared.firmalar WHERE durum = 'aktif' AND is_deleted = FALSE"
            )

            toplam = 0
            for firma in firmalar:
                schema = firma['schema_adi']
                firma_id = firma['id']

                # Bu schema'da randevular tablosu var mı kontrol et
                tablo_var = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = $1 AND table_name = 'randevular'
                    )
                    """,
                    schema
                )
                if not tablo_var:
                    continue

                # 24 saat sonraki randevuları bul (hatırlatma gönderilmemiş)
                yarin = datetime.now() + timedelta(hours=24)
                randevular = await conn.fetch(
                    f"""
                    SELECT r.id, r.hasta_ad, r.hasta_telefon, r.tarih, r.saat,
                           d.ad as doktor_ad, f.ad as firma_adi
                    FROM {schema}.randevular r
                    LEFT JOIN {schema}.doktorlar d ON r.doktor_id = d.id
                    JOIN shared.firmalar f ON f.id = $1
                    WHERE r.durum = 'onaylandi'
                    AND r.hatirlatma_gonderildi = FALSE
                    AND r.tarih = $2::date
                    """,
                    firma_id, yarin.date()
                )

                sms = NetgsmSMSService()
                for r in randevular:
                    doktor_bilgi = f"\nDoktor: {r['doktor_ad']}" if r.get('doktor_ad') else ""
                    mesaj = (
                        f"Sayın {r['hasta_ad']},\n"
                        f"Yarın {r['tarih'].strftime('%d.%m.%Y')} saat {r['saat']} "
                        f"randevunuzu hatırlatırız.{doktor_bilgi}\n"
                        f"{r['firma_adi']}"
                    )

                    sonuc = await sms.send_sms(r['hasta_telefon'], mesaj)
                    if sonuc.get("success"):
                        await conn.execute(
                            f"UPDATE {schema}.randevular SET hatirlatma_gonderildi = TRUE WHERE id = $1",
                            r['id']
                        )
                        toplam += 1

            logger.info(f"Randevu hatırlatma: {toplam} SMS gönderildi")

        finally:
            await conn.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_gonder())
    loop.close()


# ── SİPARİŞ SMS ───────────────────────────────────────────────

@celery.task(name="sms.siparis_onay", queue="sms", bind=True, max_retries=3)
def siparis_onay_sms(self, firma_id: int, siparis_id: int, schema: str):
    """
    Sipariş onaylandığında otomatik SMS gönder.
    Su bayii, tüp bayii, halı yıkama vb. için kullanılır.
    """
    import asyncio

    async def _gonder():
        conn = await _get_db_conn()
        try:
            # Önce is_emirleri tablosunu dene (halı yıkama)
            tablo = None
            for t in ['is_emirleri', 'siparisler']:
                var = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = $1 AND table_name = $2
                    )
                    """,
                    schema, t
                )
                if var:
                    tablo = t
                    break

            if not tablo:
                logger.warning(f"Sipariş tablosu bulunamadı: {schema}")
                return

            # Müşteri ve sipariş bilgilerini al
            if tablo == 'is_emirleri':
                row = await conn.fetchrow(
                    f"""
                    SELECT ie.musteri_ad, ie.musteri_telefon, ie.urun_turu,
                           ie.miktar, ie.birim, ie.tahmini_fiyat,
                           ie.teslim_alma_tarihi, f.ad as firma_adi
                    FROM {schema}.is_emirleri ie
                    JOIN shared.firmalar f ON f.id = $1
                    WHERE ie.id = $2
                    """,
                    firma_id, siparis_id
                )
                if row:
                    tarih_str = row['teslim_alma_tarihi'].strftime('%d.%m.%Y') if row.get('teslim_alma_tarihi') else "Belirtilmedi"
                    mesaj = (
                        f"Sayın {row['musteri_ad']},\n"
                        f"Siparişiniz alındı!\n"
                        f"Ürün: {row['urun_turu']} ({row['miktar']} {row['birim']})\n"
                        f"Teslim: {tarih_str}\n"
                        f"Tutar: {row['tahmini_fiyat']} TL\n"
                        f"Teşekkürler, {row['firma_adi']}"
                    )
                    telefon = row['musteri_telefon']
            else:
                row = await conn.fetchrow(
                    f"""
                    SELECT s.musteri_ad, s.musteri_telefon, u.ad as urun_adi,
                           s.adet, s.toplam_fiyat, s.teslimat_saati, f.ad as firma_adi
                    FROM {schema}.siparisler s
                    LEFT JOIN {schema}.urunler u ON s.urun_id = u.id
                    JOIN shared.firmalar f ON f.id = $1
                    WHERE s.id = $2
                    """,
                    firma_id, siparis_id
                )
                if row:
                    mesaj = (
                        f"Sayın {row['musteri_ad']},\n"
                        f"Siparişiniz alındı!\n"
                        f"Ürün: {row['urun_adi']} x{row['adet']}\n"
                        f"Tutar: {row['toplam_fiyat']} TL\n"
                        f"Teslimat: {row.get('teslimat_saati', 'Bugün')}\n"
                        f"Teşekkürler, {row['firma_adi']}"
                    )
                    telefon = row['musteri_telefon']

            if not row:
                logger.warning(f"Sipariş bulunamadı: {siparis_id}")
                return

            sms = NetgsmSMSService()
            sonuc = await sms.send_sms(telefon, mesaj)

            if sonuc.get("success"):
                await conn.execute(
                    f"UPDATE {schema}.{tablo} SET sms_gonderildi = TRUE WHERE id = $1",
                    siparis_id
                )
                logger.info(f"Sipariş onay SMS gönderildi: {siparis_id}")
            else:
                logger.error(f"SMS gönderilemedi: {sonuc.get('error')}")

        finally:
            await conn.close()

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_gonder())
        loop.close()
    except Exception as exc:
        logger.error(f"siparis_onay_sms hatası: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ── GENEL SMS TASK ────────────────────────────────────────────

@celery.task(name="sms.genel_gonder", queue="sms", bind=True, max_retries=3)
def genel_sms_gonder(self, telefon: str, mesaj: str, firma_id: Optional[int] = None):
    """
    Genel amaçlı SMS gönderme task'ı.
    Herhangi bir yerden çağrılabilir.
    """
    import asyncio

    async def _gonder():
        sms = NetgsmSMSService()
        sonuc = await sms.send_sms(telefon, mesaj)

        if sonuc.get("success"):
            # SMS sayacını artır
            if firma_id:
                conn = await _get_db_conn()
                try:
                    now = datetime.now()
                    await conn.execute(
                        """
                        INSERT INTO shared.kullanim_sayaclari (firma_id, ay, yil, sms_sayisi)
                        VALUES ($1, $2, $3, 1)
                        ON CONFLICT (firma_id, ay, yil)
                        DO UPDATE SET sms_sayisi = shared.kullanim_sayaclari.sms_sayisi + 1,
                                      updated_at = NOW()
                        """,
                        firma_id, now.month, now.year
                    )
                finally:
                    await conn.close()
            logger.info(f"SMS gönderildi: {telefon}")
        else:
            logger.error(f"SMS gönderilemedi: {sonuc.get('error')}")

        return sonuc

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_gonder())
        loop.close()
        return result
    except Exception as exc:
        logger.error(f"genel_sms_gonder hatası: {exc}")
        raise self.retry(exc=exc, countdown=60)
