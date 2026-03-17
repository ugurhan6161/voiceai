"""
VoiceAI Platform — SIP Dahili API
Firma SIP bağlantı bilgilerini yönetir.
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sip", tags=["SIP"])

DB_URL = os.getenv("DATABASE_URL", "postgresql://voiceai_user:voiceai_pass@voiceai-postgres:5432/voiceai")
VPS_IP = os.getenv("VPS_IP", "31.57.77.166")


class YonlendirmeGuncelle(BaseModel):
    aktif_tur: str  # 'uygulama' veya 'telefon'
    telefon_no: Optional[str] = None
    mesai_baslangic: Optional[str] = "09:00"
    mesai_bitis: Optional[str] = "18:00"


async def get_db():
    import asyncpg
    conn = await asyncpg.connect(DB_URL)
    try:
        yield conn
    finally:
        await conn.close()


@router.get("/bilgi")
async def sip_bilgi_al(firma_id: int = 1):
    """Firma SIP bağlantı bilgilerini getir"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        row = await conn.fetchrow("""
            SELECT d.dahili_no, d.kullanici_adi, d.yonlendirme_turu,
                   d.telefon_no, d.aktif, d.son_kayit,
                   y.aktif_tur, y.mesai_baslangic, y.mesai_bitis
            FROM shared.sip_dahilileri d
            LEFT JOIN shared.yonlendirme_ayarlari y ON y.firma_id = d.firma_id
            WHERE d.firma_id = $1
        """, firma_id)
        await conn.close()

        if not row:
            # Dahili yoksa oluştur
            from services.sip_provision_service import firma_dahili_olustur
            bilgi = await firma_dahili_olustur(firma_id)
            return bilgi

        return {
            "dahili_no": row["dahili_no"],
            "kullanici_adi": row["kullanici_adi"],
            "yonlendirme_turu": row["yonlendirme_turu"],
            "telefon_no": row["telefon_no"],
            "aktif": row["aktif"],
            "son_kayit": row["son_kayit"].isoformat() if row["son_kayit"] else None,
            "sunucu": VPS_IP,
            "port": "5060",
            "domain": VPS_IP,
            "aktif_tur": row["aktif_tur"],
            "mesai_baslangic": str(row["mesai_baslangic"]) if row["mesai_baslangic"] else "09:00",
            "mesai_bitis": str(row["mesai_bitis"]) if row["mesai_bitis"] else "18:00",
        }
    except Exception as e:
        logger.error(f"SIP bilgi hatası: {e}")
        # Fallback
        return {
            "dahili_no": "101",
            "kullanici_adi": f"firma_{firma_id}_dahili",
            "sunucu": VPS_IP,
            "port": "5060",
            "domain": VPS_IP,
            "aktif_tur": "uygulama",
        }


@router.put("/yonlendirme")
async def yonlendirme_guncelle(data: YonlendirmeGuncelle, firma_id: int = 1):
    """Çağrı yönlendirme ayarını güncelle"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)

        if data.aktif_tur == "telefon" and not data.telefon_no:
            raise HTTPException(status_code=400, detail="Telefon numarası gerekli")

        await conn.execute("""
            INSERT INTO shared.yonlendirme_ayarlari
                (firma_id, aktif_tur, telefon_no, mesai_baslangic, mesai_bitis)
            VALUES ($1, $2, $3, $4::time, $5::time)
            ON CONFLICT (firma_id) DO UPDATE
            SET aktif_tur = $2, telefon_no = $3,
                mesai_baslangic = $4::time, mesai_bitis = $5::time,
                updated_at = NOW()
        """, firma_id, data.aktif_tur, data.telefon_no,
             data.mesai_baslangic, data.mesai_bitis)

        # Dahili tablosunu da güncelle
        await conn.execute("""
            UPDATE shared.sip_dahilileri
            SET yonlendirme_turu = $2, telefon_no = $3, updated_at = NOW()
            WHERE firma_id = $1
        """, firma_id, data.aktif_tur, data.telefon_no)

        await conn.close()
        return {"status": "ok", "mesaj": "Yönlendirme güncellendi"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Yönlendirme güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/yenile")
async def sip_sifre_yenile(firma_id: int = 1):
    """SIP şifresini yenile"""
    try:
        from services.sip_provision_service import firma_dahili_olustur
        bilgi = await firma_dahili_olustur(firma_id)
        return {"status": "ok", "mesaj": "SIP şifresi yenilendi", "yeni_sifre": bilgi.get("sifre")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── ADMIN ENDPOINT'LERİ ───────────────────────────────────────
@router.get("/admin/dahililer")
async def admin_dahililer_listele():
    """Admin: Tüm firma dahililerini listele"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        rows = await conn.fetch("""
            SELECT d.id, d.firma_id, f.ad as firma_adi,
                   d.dahili_no, d.kullanici_adi, d.yonlendirme_turu,
                   d.aktif, d.son_kayit
            FROM shared.sip_dahilileri d
            LEFT JOIN shared.firmalar f ON f.id = d.firma_id
            ORDER BY d.firma_id
        """)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Admin dahili listesi hatası: {e}")
        return []


@router.delete("/admin/dahililer/{dahili_id}")
async def admin_dahili_sil(dahili_id: int):
    """Admin: Dahili sil"""
    try:
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("DELETE FROM shared.sip_dahilileri WHERE id = $1", dahili_id)
        await conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
