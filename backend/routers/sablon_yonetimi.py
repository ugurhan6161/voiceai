"""
VoiceAI Platform — Şablon Yönetimi API Router
Şablon listeleme, firma'ya atama ve otomatik DB kurulumu.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sablonlar", tags=["sablonlar"])

DB_URL = os.getenv("DATABASE_URL", "postgresql://voiceai_user:voiceai_pass@voiceai-postgres:5432/voiceai")

# Şablon listesi (registry'den dinamik yükleme yerine statik - import sorunu yok)
SABLONLAR = {
    "otel": {"ad": "Otel", "sektor": "konaklama", "ikon": "🏨"},
    "pansiyon_apart": {"ad": "Pansiyon / Apart", "sektor": "konaklama", "ikon": "🏨"},
    "kamp_bungalov": {"ad": "Kamp / Bungalov", "sektor": "konaklama", "ikon": "⛺"},
    "klinik": {"ad": "Klinik / Muayenehane", "sektor": "saglik", "ikon": "🏥"},
    "dis_klinigi": {"ad": "Diş Kliniği", "sektor": "saglik", "ikon": "🦷"},
    "veteriner": {"ad": "Veteriner", "sektor": "saglik", "ikon": "🐾"},
    "psikolog": {"ad": "Psikolog", "sektor": "saglik", "ikon": "🧠"},
    "fizik_tedavi": {"ad": "Fizik Tedavi", "sektor": "saglik", "ikon": "💪"},
    "hali_yikama": {"ad": "Halı Yıkama", "sektor": "ev_hizmetleri", "ikon": "🏠"},
    "kuru_temizleme": {"ad": "Kuru Temizleme", "sektor": "ev_hizmetleri", "ikon": "👔"},
    "bahce_bakim": {"ad": "Bahçe Bakım", "sektor": "ev_hizmetleri", "ikon": "🌿"},
    "ev_tamircisi": {"ad": "Ev Tamircisi", "sektor": "ev_hizmetleri", "ikon": "🔧"},
    "mobilya_tamiri": {"ad": "Mobilya Tamiri", "sektor": "ev_hizmetleri", "ikon": "🪑"},
    "pvc_cam_usta": {"ad": "PVC / Cam Usta", "sektor": "ev_hizmetleri", "ikon": "🪟"},
    "su_tup_bayii": {"ad": "Su / Tüp Bayii", "sektor": "enerji_temel", "ikon": "💧"},
    "elektrikci": {"ad": "Elektrikçi", "sektor": "enerji_temel", "ikon": "⚡"},
    "tesisatci": {"ad": "Tesisatçı", "sektor": "enerji_temel", "ikon": "🔩"},
    "isitma_klima": {"ad": "Isıtma / Klima", "sektor": "enerji_temel", "ikon": "❄️"},
    "oto_servis": {"ad": "Oto Servis", "sektor": "arac_tasima", "ikon": "🚗"},
    "arac_kiralama": {"ad": "Araç Kiralama", "sektor": "arac_tasima", "ikon": "🚙"},
    "arac_yikama": {"ad": "Araç Yıkama", "sektor": "arac_tasima", "ikon": "🚿"},
    "lastikci": {"ad": "Lastikçi", "sektor": "arac_tasima", "ikon": "🔄"},
    "ozel_sofor": {"ad": "Özel Şoför", "sektor": "arac_tasima", "ikon": "🚕"},
    "kuafor_berber": {"ad": "Kuaför / Berber", "sektor": "kisisel_bakim", "ikon": "✂️"},
    "guzellik_salonu": {"ad": "Güzellik Salonu", "sektor": "kisisel_bakim", "ikon": "💅"},
    "epilasyon_lazer": {"ad": "Epilasyon / Lazer", "sektor": "kisisel_bakim", "ikon": "✨"},
    "spor_salonu": {"ad": "Spor Salonu", "sektor": "kisisel_bakim", "ikon": "💪"},
    "ozel_ders": {"ad": "Özel Ders", "sektor": "egitim_danismanlik", "ikon": "📚"},
    "muzik_okulu": {"ad": "Müzik Okulu", "sektor": "egitim_danismanlik", "ikon": "🎵"},
    "avukatlik": {"ad": "Avukatlık", "sektor": "egitim_danismanlik", "ikon": "⚖️"},
    "emlak": {"ad": "Emlak", "sektor": "egitim_danismanlik", "ikon": "🏢"},
    "muhasebe": {"ad": "Muhasebe", "sektor": "egitim_danismanlik", "ikon": "📊"},
    "restoran": {"ad": "Restoran", "sektor": "yiyecek_icecek", "ikon": "🍽️"},
    "kafe": {"ad": "Kafe", "sektor": "yiyecek_icecek", "ikon": "☕"},
    "catering": {"ad": "Catering", "sektor": "yiyecek_icecek", "ikon": "🍱"},
    "pastane": {"ad": "Pastane / Fırın", "sektor": "yiyecek_icecek", "ikon": "🎂"},
    "dugun_organizasyon": {"ad": "Düğün / Organizasyon", "sektor": "ozel_hizmetler", "ikon": "💒"},
    "fotografci": {"ad": "Fotoğrafçı", "sektor": "ozel_hizmetler", "ikon": "📷"},
    "temizlik_sirketi": {"ad": "Temizlik Şirketi", "sektor": "ozel_hizmetler", "ikon": "🧹"},
    "nakliyat": {"ad": "Nakliyat", "sektor": "ozel_hizmetler", "ikon": "🚛"},
    "sigorta": {"ad": "Sigorta Acentesi", "sektor": "ozel_hizmetler", "ikon": "🛡️"},
}

SEKTOR_GRUPLARI = {
    "konaklama": {"ad": "Konaklama", "ikon": "🏨"},
    "saglik": {"ad": "Sağlık", "ikon": "🏥"},
    "ev_hizmetleri": {"ad": "Ev Hizmetleri", "ikon": "🏠"},
    "enerji_temel": {"ad": "Enerji & Temel", "ikon": "⚡"},
    "arac_tasima": {"ad": "Araç & Taşıma", "ikon": "🚗"},
    "kisisel_bakim": {"ad": "Kişisel Bakım", "ikon": "💇"},
    "egitim_danismanlik": {"ad": "Eğitim & Danışmanlık", "ikon": "📚"},
    "yiyecek_icecek": {"ad": "Yiyecek & İçecek", "ikon": "🍽️"},
    "ozel_hizmetler": {"ad": "Özel Hizmetler", "ikon": "✨"},
}


class SablonAtama(BaseModel):
    firma_id: int
    sablon_id: str


@router.get("/liste")
async def sablon_listesi():
    """Tüm şablonları listele"""
    return {
        "sablonlar": [
            {"id": k, **v} for k, v in SABLONLAR.items()
        ],
        "toplam": len(SABLONLAR),
    }


@router.get("/sektorler")
async def sektor_listesi():
    """Sektör gruplarını listele"""
    result = []
    for sektor_id, sektor_bilgi in SEKTOR_GRUPLARI.items():
        sablonlar = [
            {"id": k, **v}
            for k, v in SABLONLAR.items()
            if v["sektor"] == sektor_id
        ]
        result.append({
            "id": sektor_id,
            **sektor_bilgi,
            "sablonlar": sablonlar,
        })
    return result


@router.get("/{sablon_id}")
async def sablon_detay(sablon_id: str):
    """Şablon detayını getir"""
    if sablon_id not in SABLONLAR:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    return {"id": sablon_id, **SABLONLAR[sablon_id]}


@router.post("/ata")
async def sablon_ata(atama: SablonAtama):
    """Firmaya şablon ata ve DB şemasını oluştur"""
    if atama.sablon_id not in SABLONLAR:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("""
            UPDATE shared.firmalar
            SET sablon_id = $1, updated_at = NOW()
            WHERE id = $2
        """, atama.sablon_id, atama.firma_id)
        await conn.close()
        return {
            "status": "ok",
            "mesaj": f"Şablon '{atama.sablon_id}' firmaya atandı",
            "firma_id": atama.firma_id,
        }
    except Exception as e:
        logger.error(f"Şablon atama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))
