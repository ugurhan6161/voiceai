"""
VoiceAI Platform — Ayarlar API Router
Admin sistem ayarları ve firma entegrasyon ayarları endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from backend.services.settings_service import AyarServisi, EntegrasyonTester
from backend.middleware.auth_middleware import admin_required, firma_required
from backend.database import get_db

router = APIRouter(prefix="/api/ayarlar", tags=["ayarlar"])


# ── Pydantic Modeller ──────────────────────────────────────────

class AyarGuncelle(BaseModel):
    deger: str
    sifirli: bool = False


class SipAyarlari(BaseModel):
    host: str
    kullanici: str
    sifre: Optional[str] = None  # None = değiştirilmedi
    aktif: bool = True


class SmsAyarlari(BaseModel):
    kullanici: str
    sifre: Optional[str] = None
    baslik: str
    aktif: bool = True


class IyzicoAyarlari(BaseModel):
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    mod: str = "sandbox"  # sandbox | production


class SmtpAyarlari(BaseModel):
    host: str
    port: int = 587
    kullanici: str
    sifre: Optional[str] = None
    gonderen_ad: str


class TestIstegi(BaseModel):
    tur: str  # sip_netgsm | sip_verimor | sms_netgsm | iyzico | smtp | pms_api
    ayarlar: dict


class FirmaEntegrasyonAyarlari(BaseModel):
    tur: str
    ayarlar: dict


# ── ADMIN SİSTEM AYARLARI ──────────────────────────────────────

@router.get("/sistem/{kategori}", dependencies=[Depends(admin_required)])
async def sistem_kategori_getir(
    kategori: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Belirli bir kategorinin tüm sistem ayarlarını getirir.
    Şifreli değerler maskelenerek döndürülür (panel için).
    """
    servis = AyarServisi(db)
    return await servis.sistem_kategori_al(kategori)


@router.put("/sistem/sip/{saglayici}", dependencies=[Depends(admin_required)])
async def sip_ayarlarini_kaydet(
    saglayici: str,  # netgsm | verimor | twilio
    ayarlar: SipAyarlari,
    db: AsyncSession = Depends(get_db)
):
    """
    SIP sağlayıcı ayarlarını kaydeder.
    Şifre alanı boşsa mevcut şifre değiştirilmez.
    """
    if saglayici not in ["netgsm", "verimor", "twilio"]:
        raise HTTPException(status_code=400, detail="Geçersiz SIP sağlayıcı.")

    kategori = f"sip_{saglayici}"
    servis = AyarServisi(db)

    await servis.sistem_ayar_kaydet(kategori, "host", ayarlar.host)
    await servis.sistem_ayar_kaydet(kategori, "kullanici", ayarlar.kullanici)
    await servis.sistem_ayar_kaydet(kategori, "aktif", str(ayarlar.aktif).lower())

    if ayarlar.sifre:  # Şifre gönderildiyse güncelle
        await servis.sistem_ayar_kaydet(kategori, "sifre", ayarlar.sifre, sifirli=True)

    return {"mesaj": f"{saglayici.capitalize()} SIP ayarları kaydedildi."}


@router.put("/sistem/sms/netgsm", dependencies=[Depends(admin_required)])
async def sms_ayarlarini_kaydet(
    ayarlar: SmsAyarlari,
    db: AsyncSession = Depends(get_db)
):
    """Netgsm SMS API ayarlarını kaydeder."""
    servis = AyarServisi(db)
    await servis.sistem_ayar_kaydet("sms_netgsm", "kullanici", ayarlar.kullanici)
    await servis.sistem_ayar_kaydet("sms_netgsm", "baslik", ayarlar.baslik)
    await servis.sistem_ayar_kaydet("sms_netgsm", "aktif", str(ayarlar.aktif).lower())
    if ayarlar.sifre:
        await servis.sistem_ayar_kaydet("sms_netgsm", "sifre", ayarlar.sifre, sifirli=True)
    return {"mesaj": "SMS ayarları kaydedildi."}


@router.put("/sistem/iyzico", dependencies=[Depends(admin_required)])
async def iyzico_ayarlarini_kaydet(
    ayarlar: IyzicoAyarlari,
    db: AsyncSession = Depends(get_db)
):
    """iyzico ödeme sistemi ayarlarını kaydeder."""
    servis = AyarServisi(db)
    await servis.sistem_ayar_kaydet("iyzico", "mod", ayarlar.mod)
    if ayarlar.api_key:
        await servis.sistem_ayar_kaydet("iyzico", "api_key", ayarlar.api_key, sifirli=True)
    if ayarlar.secret_key:
        await servis.sistem_ayar_kaydet("iyzico", "secret_key", ayarlar.secret_key, sifirli=True)
    return {"mesaj": "iyzico ayarları kaydedildi."}


@router.put("/sistem/smtp", dependencies=[Depends(admin_required)])
async def smtp_ayarlarini_kaydet(
    ayarlar: SmtpAyarlari,
    db: AsyncSession = Depends(get_db)
):
    """SMTP e-posta ayarlarını kaydeder."""
    servis = AyarServisi(db)
    await servis.sistem_ayar_kaydet("smtp", "host", ayarlar.host)
    await servis.sistem_ayar_kaydet("smtp", "port", str(ayarlar.port))
    await servis.sistem_ayar_kaydet("smtp", "kullanici", ayarlar.kullanici)
    await servis.sistem_ayar_kaydet("smtp", "gonderen_ad", ayarlar.gonderen_ad)
    if ayarlar.sifre:
        await servis.sistem_ayar_kaydet("smtp", "sifre", ayarlar.sifre, sifirli=True)
    return {"mesaj": "SMTP ayarları kaydedildi."}


# ── BAĞLANTI TEST ET ───────────────────────────────────────────

@router.post("/test", dependencies=[Depends(admin_required)])
async def baglantiyi_test_et(istek: TestIstegi):
    """
    Belirli bir entegrasyonun bağlantısını test eder.
    Panel'deki "Test Et" butonunun backend karşılığı.
    """
    tester = EntegrasyonTester()

    if istek.tur == "sip_netgsm":
        return await tester.test_sip(
            istek.ayarlar.get("host", ""),
            istek.ayarlar.get("kullanici", ""),
            istek.ayarlar.get("sifre", "")
        )
    elif istek.tur == "sms_netgsm":
        return await tester.test_sms_netgsm(
            istek.ayarlar.get("kullanici", ""),
            istek.ayarlar.get("sifre", "")
        )
    elif istek.tur == "iyzico":
        return await tester.test_iyzico(
            istek.ayarlar.get("api_key", ""),
            istek.ayarlar.get("secret_key", ""),
            istek.ayarlar.get("mod", "sandbox") == "sandbox"
        )
    elif istek.tur == "smtp":
        return await tester.test_smtp(
            istek.ayarlar.get("host", ""),
            int(istek.ayarlar.get("port", 587)),
            istek.ayarlar.get("kullanici", ""),
            istek.ayarlar.get("sifre", "")
        )
    elif istek.tur == "pms_api":
        return await tester.test_pms_api(
            istek.ayarlar.get("url", ""),
            istek.ayarlar.get("api_key", "")
        )
    else:
        raise HTTPException(status_code=400, detail=f"Bilinmeyen test türü: {istek.tur}")


# ── FİRMA ENTEGRASYON AYARLARI ─────────────────────────────────

@router.get("/firma/entegrasyon", dependencies=[Depends(firma_required)])
async def firma_entegrasyon_getir(
    firma_schema: str = Depends(lambda: None),  # middleware'den gelir
    db: AsyncSession = Depends(get_db)
):
    """Firmanın entegrasyon ayarlarını getirir (maskelenerek)."""
    servis = AyarServisi(db)
    kategoriler = ["sip_numarasi", "pms_api", "crm_api", "webhook"]
    sonuc = {}
    for tur in kategoriler:
        # Her tur için ayarları getir (detaylı implementasyon gerekir)
        sonuc[tur] = {}
    return sonuc


@router.put("/firma/entegrasyon", dependencies=[Depends(firma_required)])
async def firma_entegrasyon_kaydet(
    ayarlar: FirmaEntegrasyonAyarlari,
    firma_schema: str = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """Firmanın entegrasyon ayarını kaydeder."""
    servis = AyarServisi(db)
    for anahtar, deger in ayarlar.ayarlar.items():
        sifirli = anahtar in ["sifre", "api_key", "secret", "token", "webhook_secret"]
        await servis.firma_ayar_kaydet(
            firma_schema, ayarlar.tur, anahtar, str(deger), sifirli
        )
    return {"mesaj": "Entegrasyon ayarları kaydedildi."}


@router.post("/firma/test", dependencies=[Depends(firma_required)])
async def firma_entegrasyon_test(istek: TestIstegi):
    """Firma entegrasyon bağlantısını test eder."""
    tester = EntegrasyonTester()
    if istek.tur == "pms_api":
        return await tester.test_pms_api(
            istek.ayarlar.get("url", ""),
            istek.ayarlar.get("api_key", "")
        )
    raise HTTPException(status_code=400, detail="Desteklenmeyen test türü.")
