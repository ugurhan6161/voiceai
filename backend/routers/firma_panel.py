"""
VoiceAI Platform — Firma Panel API
Firma adminleri için dashboard, ajan ayarları, çağrı geçmişi, faturalar.
"""
import os
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import asyncpg
from asyncpg.pool import Pool

from .auth import get_current_active_user, require_role, User
from middleware.tenant_middleware import get_current_firma_id, set_search_path

router = APIRouter(prefix="/firma", tags=["Firma Panel"])


# ── DB Pool ──────────────────────────────────────────────────
async def get_db_pool() -> Pool:
    return await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "voiceai-postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
        min_size=2, max_size=10
    )


# ── Pydantic Modeller ────────────────────────────────────────
class AjanAyarlari(BaseModel):
    asistan_adi: Optional[str] = None
    karsilama_metni: Optional[str] = None
    ses_turu: Optional[str] = None       # gtts, xtts
    dil: Optional[str] = "tr"
    aktif: Optional[bool] = True


class HizmetGuncelle(BaseModel):
    ad: str
    fiyat: float
    birim: Optional[str] = "adet"
    aktif: bool = True


# ── DASHBOARD ────────────────────────────────────────────────
@router.get("/dashboard")
async def firma_dashboard(
    request: Request,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "firma_kullanici", "super_admin"]))
):
    """Firma dashboard istatistikleri"""
    firma_id = current_user.firma_id
    if not firma_id:
        raise HTTPException(status_code=403, detail="Firma bilgisi bulunamadı")

    async with pool.acquire() as conn:
        # Firma bilgileri
        firma = await conn.fetchrow(
            """
            SELECT f.ad, f.sektor, f.durum, f.schema_adi,
                   p.ad as paket_adi, p.cagri_limiti, p.sms_limiti
            FROM shared.firmalar f
            LEFT JOIN shared.paketler p ON f.paket_id = p.id
            WHERE f.id = $1
            """,
            firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        # Bugünkü çağrılar
        bugun_cagri = await conn.fetchval(
            """
            SELECT COUNT(*) FROM shared.cagri_loglari
            WHERE firma_id = $1 AND DATE(baslangic) = CURRENT_DATE
            """,
            firma_id
        ) or 0

        # Bu ayki kullanım
        now = datetime.now()
        kullanim = await conn.fetchrow(
            """
            SELECT cagri_sayisi, sms_sayisi
            FROM shared.kullanim_sayaclari
            WHERE firma_id = $1 AND ay = $2 AND yil = $3
            """,
            firma_id, now.month, now.year
        )

        # Son 5 çağrı
        son_cagrilar = await conn.fetch(
            """
            SELECT telefon, baslangic, sure_saniye, sonuc, ai_ozet
            FROM shared.cagri_loglari
            WHERE firma_id = $1
            ORDER BY baslangic DESC LIMIT 5
            """,
            firma_id
        )

        return {
            "firma": dict(firma),
            "bugun_cagri": bugun_cagri,
            "bu_ay_cagri": kullanim["cagri_sayisi"] if kullanim else 0,
            "bu_ay_sms": kullanim["sms_sayisi"] if kullanim else 0,
            "son_cagrilar": [dict(r) for r in son_cagrilar],
        }


# ── AJAN AYARLARI ────────────────────────────────────────────
@router.get("/ajan")
async def get_ajan_ayarlari(
    request: Request,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "super_admin"]))
):
    """Firma ajan (asistan) ayarlarını getir"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        firma = await conn.fetchrow(
            "SELECT ad, sektor, schema_adi FROM shared.firmalar WHERE id = $1",
            firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        schema = firma["schema_adi"]
        # Firma schema'sında ajan ayarları tablosu varsa al
        try:
            await conn.execute(f"SET search_path TO {schema}, shared")
            ayarlar = await conn.fetchrow(
                "SELECT * FROM ayarlar LIMIT 1"
            )
        except Exception:
            ayarlar = None

        return {
            "firma_adi": firma["ad"],
            "sektor": firma["sektor"],
            "schema": schema,
            "ayarlar": dict(ayarlar) if ayarlar else {},
        }


@router.put("/ajan")
async def update_ajan_ayarlari(
    ayarlar: AjanAyarlari,
    request: Request,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "super_admin"]))
):
    """Firma ajan ayarlarını güncelle"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        firma = await conn.fetchrow(
            "SELECT schema_adi FROM shared.firmalar WHERE id = $1", firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        schema = firma["schema_adi"]
        try:
            await conn.execute(f"SET search_path TO {schema}, shared")
            await conn.execute(
                """
                UPDATE ayarlar SET
                    updated_at = NOW()
                WHERE id = (SELECT id FROM ayarlar LIMIT 1)
                """
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Güncelleme hatası: {e}")

        return {"message": "Ajan ayarları güncellendi"}


# ── HİZMETLER ────────────────────────────────────────────────
@router.get("/hizmetler")
async def get_hizmetler(
    request: Request,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "firma_kullanici", "super_admin"]))
):
    """Firma hizmet listesini getir"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        firma = await conn.fetchrow(
            "SELECT schema_adi FROM shared.firmalar WHERE id = $1", firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        schema = firma["schema_adi"]
        try:
            await conn.execute(f"SET search_path TO {schema}, shared")
            # Hizmetler veya ürünler tablosunu dene
            for tablo in ["hizmetler", "urunler", "odalar"]:
                try:
                    rows = await conn.fetch(f"SELECT * FROM {tablo} WHERE aktif = TRUE ORDER BY id")
                    return {"tablo": tablo, "hizmetler": [dict(r) for r in rows]}
                except Exception:
                    continue
        except Exception as e:
            pass

        return {"tablo": None, "hizmetler": []}


# ── ÇAĞRI GEÇMİŞİ ────────────────────────────────────────────
@router.get("/cagrilar")
async def get_cagri_gecmisi(
    sayfa: int = 1,
    limit: int = 20,
    baslangic_tarihi: Optional[date] = None,
    bitis_tarihi: Optional[date] = None,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "firma_kullanici", "super_admin"]))
):
    """Firma çağrı geçmişini getir"""
    firma_id = current_user.firma_id
    offset = (sayfa - 1) * limit

    async with pool.acquire() as conn:
        query = """
            SELECT id, telefon, baslangic, bitis, sure_saniye,
                   sonuc, ai_ozet, duygu_skoru, aktarim
            FROM shared.cagri_loglari
            WHERE firma_id = $1
        """
        params = [firma_id]

        if baslangic_tarihi:
            params.append(baslangic_tarihi)
            query += f" AND DATE(baslangic) >= ${len(params)}"
        if bitis_tarihi:
            params.append(bitis_tarihi)
            query += f" AND DATE(baslangic) <= ${len(params)}"

        query += f" ORDER BY baslangic DESC LIMIT {limit} OFFSET {offset}"

        rows = await conn.fetch(query, *params)

        toplam = await conn.fetchval(
            "SELECT COUNT(*) FROM shared.cagri_loglari WHERE firma_id = $1",
            firma_id
        )

        return {
            "cagrilar": [dict(r) for r in rows],
            "toplam": toplam,
            "sayfa": sayfa,
            "limit": limit,
        }


# ── FATURALAR ────────────────────────────────────────────────
@router.get("/faturalar")
async def get_faturalar(
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "super_admin"]))
):
    """Firma fatura listesini getir"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, fatura_no, paket_ucreti, asim_ucreti,
                   toplam, kdv, genel_toplam, durum,
                   vade_tarihi, odeme_tarihi, ay, yil, created_at
            FROM shared.faturalar
            WHERE firma_id = $1
            ORDER BY created_at DESC
            """,
            firma_id
        )
        return {"faturalar": [dict(r) for r in rows]}


# ── ENTEGRASYON ───────────────────────────────────────────────
@router.get("/entegrasyon")
async def get_entegrasyon(
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "super_admin"]))
):
    """Firma entegrasyon ayarlarını getir"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        firma = await conn.fetchrow(
            "SELECT ad, sektor, schema_adi, email, telefon FROM shared.firmalar WHERE id = $1",
            firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        return {
            "firma_id": firma_id,
            "firma_adi": firma["ad"],
            "sektor": firma["sektor"],
            "email": firma["email"],
            "telefon": firma["telefon"],
        }


@router.put("/entegrasyon")
async def update_entegrasyon(
    data: dict,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["firma_admin", "super_admin"]))
):
    """Firma entegrasyon ayarlarını güncelle"""
    firma_id = current_user.firma_id

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE shared.firmalar
            SET email = COALESCE($2, email),
                telefon = COALESCE($3, telefon),
                updated_at = NOW()
            WHERE id = $1
            """,
            firma_id,
            data.get("email"),
            data.get("telefon"),
        )
        return {"message": "Entegrasyon ayarları güncellendi"}
