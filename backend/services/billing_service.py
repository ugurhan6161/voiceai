"""
VoiceAI Platform — Faturalama Servisi
Aşım hesaplama, fatura oluşturma, ödeme takibi.
"""
import os
import logging
from datetime import datetime, date
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)


async def _get_db_conn():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "voiceai-postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
    )


async def aylik_fatura_olustur(firma_id: int, ay: int, yil: int) -> Optional[dict]:
    """
    Firma için aylık fatura oluşturur.
    Paket ücreti + aşım ücreti hesaplar.
    """
    conn = await _get_db_conn()
    try:
        # Firma ve paket bilgilerini al
        firma = await conn.fetchrow(
            """
            SELECT f.id, f.ad, p.fiyat as paket_fiyat, p.cagri_limiti,
                   p.sms_limiti, p.fazla_cagri_fiyat, p.fazla_sms_fiyat
            FROM shared.firmalar f
            JOIN shared.paketler p ON f.paket_id = p.id
            WHERE f.id = $1 AND f.is_deleted = FALSE
            """,
            firma_id
        )
        if not firma:
            return None

        # Kullanım sayaçlarını al
        kullanim = await conn.fetchrow(
            """
            SELECT cagri_sayisi, sms_sayisi
            FROM shared.kullanim_sayaclari
            WHERE firma_id = $1 AND ay = $2 AND yil = $3
            """,
            firma_id, ay, yil
        )

        cagri_sayisi = kullanim["cagri_sayisi"] if kullanim else 0
        sms_sayisi = kullanim["sms_sayisi"] if kullanim else 0

        # Aşım hesapla
        fazla_cagri = max(0, cagri_sayisi - firma["cagri_limiti"])
        fazla_sms = max(0, sms_sayisi - firma["sms_limiti"])

        cagri_asim = fazla_cagri * float(firma["fazla_cagri_fiyat"])
        sms_asim = fazla_sms * float(firma["fazla_sms_fiyat"])
        asim_ucreti = cagri_asim + sms_asim

        paket_ucreti = float(firma["paket_fiyat"])
        toplam = paket_ucreti + asim_ucreti
        kdv = toplam * 0.20  # %20 KDV
        genel_toplam = toplam + kdv

        # Fatura numarası oluştur
        fatura_no = f"VA-{yil}{ay:02d}-{firma_id:04d}"

        # Vade tarihi (ayın son günü + 15 gün)
        if ay == 12:
            vade = date(yil + 1, 1, 15)
        else:
            vade = date(yil, ay + 1, 15)

        # Fatura kaydet
        fatura_id = await conn.fetchval(
            """
            INSERT INTO shared.faturalar
            (firma_id, fatura_no, paket_ucreti, asim_ucreti, toplam, kdv, genel_toplam,
             durum, vade_tarihi, ay, yil)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'bekliyor', $8, $9, $10)
            ON CONFLICT (fatura_no) DO NOTHING
            RETURNING id
            """,
            firma_id, fatura_no, paket_ucreti, asim_ucreti, toplam, kdv, genel_toplam,
            vade, ay, yil
        )

        logger.info(f"Fatura oluşturuldu: {fatura_no} - {genel_toplam} TL")

        return {
            "fatura_id": fatura_id,
            "fatura_no": fatura_no,
            "paket_ucreti": paket_ucreti,
            "asim_ucreti": asim_ucreti,
            "toplam": toplam,
            "kdv": kdv,
            "genel_toplam": genel_toplam,
            "vade_tarihi": str(vade),
        }

    finally:
        await conn.close()


async def tum_firmalara_fatura_olustur(ay: int, yil: int):
    """Tüm aktif firmalar için aylık fatura oluştur"""
    conn = await _get_db_conn()
    try:
        firmalar = await conn.fetch(
            "SELECT id FROM shared.firmalar WHERE durum = 'aktif' AND is_deleted = FALSE"
        )
        olusturulan = 0
        for firma in firmalar:
            try:
                sonuc = await aylik_fatura_olustur(firma["id"], ay, yil)
                if sonuc:
                    olusturulan += 1
            except Exception as e:
                logger.error(f"Fatura oluşturma hatası (firma {firma['id']}): {e}")

        logger.info(f"Toplam {olusturulan} fatura oluşturuldu ({ay}/{yil})")
        return olusturulan
    finally:
        await conn.close()
