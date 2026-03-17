"""
VoiceAI Platform — Ayarlar API Router
Admin sistem ayarları ve firma entegrasyon ayarları endpoint'leri.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ayarlar", tags=["ayarlar"])

DB_URL = os.getenv("DATABASE_URL", "postgresql://voiceai_user:voiceai_pass@voiceai-postgres:5432/voiceai")


# ── Pydantic Modeller ──────────────────────────────────────────

class SipAyarlari(BaseModel):
    host: str
    kullanici: str
    sifre: Optional[str] = None
    aktif: bool = True


class SmsAyarlari(BaseModel):
    kullanici: str
    sifre: Optional[str] = None
    baslik: str
    aktif: bool = True


class IyzicoAyarlari(BaseModel):
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    mod: str = "sandbox"


class SmtpAyarlari(BaseModel):
    host: str
    port: int = 587
    kullanici: str
    sifre: Optional[str] = None
    gonderen_ad: str


class TestIstegi(BaseModel):
    tur: str
    ayarlar: dict


async def _db_ayar_kaydet(kategori: str, anahtar: str, deger: str, sifirli: bool = False):
    """DB'ye ayar kaydet"""
    try:
        import asyncpg
        from crypto import encrypt
        conn = await asyncpg.connect(DB_URL)
        kayit_deger = encrypt(deger) if sifirli else deger
        await conn.execute("""
            INSERT INTO shared.sistem_ayarlari (kategori, anahtar, deger, sifirli)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (kategori, anahtar) DO UPDATE
            SET deger = $3, sifirli = $4, updated_at = NOW()
        """, kategori, anahtar, kayit_deger, sifirli)
        await conn.close()
    except Exception as e:
        logger.error(f"Ayar kaydetme hatası: {e}")


async def _db_ayar_getir(kategori: str) -> dict:
    """DB'den kategori ayarlarını getir"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        rows = await conn.fetch(
            "SELECT anahtar, deger, sifirli FROM shared.sistem_ayarlari WHERE kategori = $1",
            kategori
        )
        await conn.close()
        result = {}
        for row in rows:
            if row["sifirli"]:
                result[row["anahtar"]] = "***"
            else:
                result[row["anahtar"]] = row["deger"]
        return result
    except Exception as e:
        logger.error(f"Ayar getirme hatası: {e}")
        return {}


# ── ADMIN SİSTEM AYARLARI ──────────────────────────────────────

@router.get("/sistem/{kategori}")
async def sistem_kategori_getir(kategori: str):
    """Belirli bir kategorinin tüm sistem ayarlarını getirir."""
    return await _db_ayar_getir(kategori)


@router.put("/sistem/sip/{saglayici}")
async def sip_ayarlarini_kaydet(saglayici: str, ayarlar: SipAyarlari):
    """SIP sağlayıcı ayarlarını kaydeder."""
    if saglayici not in ["netgsm", "verimor", "twilio"]:
        raise HTTPException(status_code=400, detail="Geçersiz SIP sağlayıcı.")
    kategori = f"sip_{saglayici}"
    await _db_ayar_kaydet(kategori, "host", ayarlar.host)
    await _db_ayar_kaydet(kategori, "kullanici", ayarlar.kullanici)
    await _db_ayar_kaydet(kategori, "aktif", str(ayarlar.aktif).lower())
    if ayarlar.sifre:
        await _db_ayar_kaydet(kategori, "sifre", ayarlar.sifre, sifirli=True)
    return {"mesaj": f"{saglayici.capitalize()} SIP ayarları kaydedildi."}


@router.put("/sistem/sms/netgsm")
async def sms_ayarlarini_kaydet(ayarlar: SmsAyarlari):
    """Netgsm SMS API ayarlarını kaydeder."""
    await _db_ayar_kaydet("sms_netgsm", "kullanici", ayarlar.kullanici)
    await _db_ayar_kaydet("sms_netgsm", "baslik", ayarlar.baslik)
    await _db_ayar_kaydet("sms_netgsm", "aktif", str(ayarlar.aktif).lower())
    if ayarlar.sifre:
        await _db_ayar_kaydet("sms_netgsm", "sifre", ayarlar.sifre, sifirli=True)
    return {"mesaj": "SMS ayarları kaydedildi."}


@router.put("/sistem/iyzico")
async def iyzico_ayarlarini_kaydet(ayarlar: IyzicoAyarlari):
    """iyzico ödeme sistemi ayarlarını kaydeder."""
    await _db_ayar_kaydet("iyzico", "mod", ayarlar.mod)
    if ayarlar.api_key:
        await _db_ayar_kaydet("iyzico", "api_key", ayarlar.api_key, sifirli=True)
    if ayarlar.secret_key:
        await _db_ayar_kaydet("iyzico", "secret_key", ayarlar.secret_key, sifirli=True)
    return {"mesaj": "iyzico ayarları kaydedildi."}


@router.put("/sistem/smtp")
async def smtp_ayarlarini_kaydet(ayarlar: SmtpAyarlari):
    """SMTP e-posta ayarlarını kaydeder."""
    await _db_ayar_kaydet("smtp", "host", ayarlar.host)
    await _db_ayar_kaydet("smtp", "port", str(ayarlar.port))
    await _db_ayar_kaydet("smtp", "kullanici", ayarlar.kullanici)
    await _db_ayar_kaydet("smtp", "gonderen_ad", ayarlar.gonderen_ad)
    if ayarlar.sifre:
        await _db_ayar_kaydet("smtp", "sifre", ayarlar.sifre, sifirli=True)
    return {"mesaj": "SMTP ayarları kaydedildi."}


@router.post("/test")
async def baglantiyi_test_et(istek: TestIstegi):
    """Entegrasyon bağlantısını test eder."""
    if istek.tur == "sms_netgsm":
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.netgsm.com.tr/sms/send/get/",
                    params={
                        "usercode": istek.ayarlar.get("kullanici", ""),
                        "password": istek.ayarlar.get("sifre", ""),
                        "gsmno": "5000000000",
                        "message": "test",
                        "msgheader": "TEST",
                    }
                )
            return {"basarili": r.status_code == 200, "mesaj": "SMS API bağlantısı test edildi"}
        except Exception as e:
            return {"basarili": False, "mesaj": str(e)}

    elif istek.tur == "smtp":
        try:
            import smtplib
            with smtplib.SMTP(istek.ayarlar.get("host", ""), int(istek.ayarlar.get("port", 587)), timeout=5) as s:
                s.ehlo()
                s.starttls()
            return {"basarili": True, "mesaj": "SMTP bağlantısı başarılı"}
        except Exception as e:
            return {"basarili": False, "mesaj": str(e)}

    elif istek.tur == "pms_api":
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    istek.ayarlar.get("url", ""),
                    headers={"Authorization": f"Bearer {istek.ayarlar.get('api_key', '')}"}
                )
            return {"basarili": r.status_code < 400, "mesaj": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"basarili": False, "mesaj": str(e)}

    return {"basarili": False, "mesaj": f"Bilinmeyen test türü: {istek.tur}"}
