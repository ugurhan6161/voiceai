"""
VoiceAI Platform — Şablon Yönetimi API Router
Şablon listeleme, firma'ya atama ve otomatik DB kurulumu.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from backend.middleware.auth_middleware import admin_required, firma_required
from backend.database import get_db
from ai_engine.templates.registry import SABLON_KAYITLARI, KATEGORILER, get_sablon

router = APIRouter(prefix="/api/sablonlar", tags=["sablonlar"])


# ── Pydantic Modeller ──────────────────────────────────────────

class FirmaSablonAta(BaseModel):
    firma_id: int
    sablon_kodu: str


class SablonGuncelle(BaseModel):
    ad: Optional[str] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None
    sira: Optional[int] = None


# ── ŞABLON LİSTELEME ──────────────────────────────────────────

@router.get("/")
async def tum_sablonlari_listele(
    kategori: Optional[str] = None,
    sadece_aktif: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Tüm şablonları kategori bazında gruplandırarak listeler.
    Firma onboarding sihirbazında kullanılır.
    """
    sorgu = """
        SELECT kod, ad, kategori, ikon, aciklama, aktif, sira
        FROM shared.sablon_tanimlari
        WHERE 1=1
    """
    params = {}
    if sadece_aktif:
        sorgu += " AND aktif = TRUE"
    if kategori:
        sorgu += " AND kategori = :kategori"
        params["kategori"] = kategori
    sorgu += " ORDER BY sira, ad"

    sonuc = await db.execute(text(sorgu), params)
    sablonlar = sonuc.fetchall()

    # Kategori bazında grupla
    gruplu: dict = {}
    for s in sablonlar:
        kat = s.kategori
        if kat not in gruplu:
            gruplu[kat] = {
                "ad": KATEGORILER.get(kat, {}).get("ad", kat),
                "ikon": KATEGORILER.get(kat, {}).get("ikon", "🏢"),
                "sablonlar": []
            }
        gruplu[kat]["sablonlar"].append({
            "kod": s.kod,
            "ad": s.ad,
            "ikon": s.ikon,
            "aciklama": s.aciklama,
            "aktif": s.aktif
        })

    return {"kategoriler": gruplu, "toplam": len(sablonlar)}


@router.get("/{sablon_kodu}")
async def sablon_detay(sablon_kodu: str, db: AsyncSession = Depends(get_db)):
    """Şablon detaylarını ve DB şemasını döndürür."""
    sonuc = await db.execute(
        text("SELECT * FROM shared.sablon_tanimlari WHERE kod = :kod"),
        {"kod": sablon_kodu}
    )
    sablon_db = sonuc.fetchone()
    if not sablon_db:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı.")

    try:
        sablon = get_sablon(sablon_kodu)
        return {
            "kod": sablon_kodu,
            "ad": sablon_db.ad,
            "kategori": sablon_db.kategori,
            "ikon": sablon_db.ikon,
            "fonksiyonlar": [
                {"ad": f.ad, "aciklama": f.aciklama, "tetikleyiciler": f.tetikleyiciler}
                for f in sablon.get_functions()
            ],
            "slotlar": [
                {"ad": s.ad, "soru": s.soru, "zorunlu": s.zorunlu}
                for s in sablon.get_slots()
            ],
            "panel_modulleri": sablon.get_panel_modules(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Şablon yüklenemedi: {e}")


# ── FİRMAYA ŞABLON ATAMA ──────────────────────────────────────

@router.post("/ata", dependencies=[Depends(admin_required)])
async def firmaya_sablon_ata(istek: FirmaSablonAta, db: AsyncSession = Depends(get_db)):
    """
    Firmaya şablon atar ve DB şemasını otomatik oluşturur.
    Onboarding sihirbazının son adımında çağrılır.
    """
    # Firma schema adını bul
    sonuc = await db.execute(
        text("SELECT schema_adi FROM shared.firmalar WHERE id = :id"),
        {"id": istek.firma_id}
    )
    firma = sonuc.fetchone()
    if not firma:
        raise HTTPException(status_code=404, detail="Firma bulunamadı.")

    # Şablonu yükle
    try:
        sablon = get_sablon(istek.sablon_kodu)
    except ValueError:
        raise HTTPException(status_code=404, detail="Şablon kodu geçersiz.")

    # DB şemasını oluştur
    schema_adi = firma.schema_adi
    db_schema_sql = sablon.get_db_schema().replace("{schema}", schema_adi)

    try:
        await db.execute(text(db_schema_sql))

        # Firma kaydını güncelle
        await db.execute(
            text("UPDATE shared.firmalar SET sektor = :sektor WHERE id = :id"),
            {"sektor": istek.sablon_kodu, "id": istek.firma_id}
        )
        await db.commit()

        return {
            "mesaj": f"Şablon '{istek.sablon_kodu}' firmaya başarıyla atandı.",
            "schema": schema_adi,
            "fonksiyon_sayisi": len(sablon.get_functions()),
            "slot_sayisi": len(sablon.get_slots()),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"DB şema hatası: {e}")


# ── ADMIN ŞABLON YÖNETİMİ ────────────────────────────────────

@router.put("/{sablon_kodu}", dependencies=[Depends(admin_required)])
async def sablon_guncelle(
    sablon_kodu: str,
    guncelleme: SablonGuncelle,
    db: AsyncSession = Depends(get_db)
):
    """Şablon meta verilerini günceller (ad, açıklama, aktiflik)."""
    guncelleme_dict = {k: v for k, v in guncelleme.dict().items() if v is not None}
    if not guncelleme_dict:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok.")

    set_clause = ", ".join(f"{k} = :{k}" for k in guncelleme_dict)
    guncelleme_dict["kod"] = sablon_kodu

    await db.execute(
        text(f"UPDATE shared.sablon_tanimlari SET {set_clause} WHERE kod = :kod"),
        guncelleme_dict
    )
    await db.commit()
    return {"mesaj": "Şablon güncellendi."}
