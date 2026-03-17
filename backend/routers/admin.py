"""
VoiceAI Platform — Admin Dashboard API

Super admin için firma yönetimi, sistem istatistikleri ve raporlar.
"""
import os
from typing import Optional, List, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, field_validator
import asyncpg
from asyncpg.pool import Pool

from .auth import get_current_active_user, require_role, User

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Pydantic Modeller ────────────────────────────────────────
class DashboardStats(BaseModel):
    toplam_firma: int
    aktif_firma: int
    durdurulmus_firma: int
    toplam_kullanici: int
    bugun_cagri: int
    bu_ay_cagri: int
    sistem_saglik: str


class FirmaListItem(BaseModel):
    id: int
    ad: str
    sektor: Optional[str] = None
    paket_ad: Optional[str] = None
    durum: Optional[str] = None
    email: Optional[str] = None
    telefon: Optional[str] = None
    created_at: Optional[datetime] = None
    son_cagri: Optional[datetime] = None
    bu_ay_cagri: int = 0
    bu_ay_sms: int = 0

    class Config:
        from_attributes = True


class FirmaCreate(BaseModel):
    ad: str
    sektor: str
    paket_id: Optional[int] = None
    email: EmailStr
    telefon: Optional[str] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None
    admin_email: EmailStr
    admin_ad: str
    admin_sifre: str


# ── Database Connection ──────────────────────────────────────
async def get_db_pool() -> Pool:
    return await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
        min_size=2,
        max_size=10
    )


# ── API Endpoints ────────────────────────────────────────────
@router.get("/dashboard")
async def get_dashboard_stats(
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        # Firma sayıları
        try:
            firma_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as toplam,
                    COUNT(*) FILTER (WHERE durum = 'aktif') as aktif,
                    COUNT(*) FILTER (WHERE durum = 'durduruldu') as durdurulmus
                FROM shared.firmalar
                WHERE is_deleted = FALSE
                """
            )
            toplam = int(firma_stats["toplam"] or 0)
            aktif = int(firma_stats["aktif"] or 0)
            durdurulmus = int(firma_stats["durdurulmus"] or 0)
        except Exception:
            toplam = aktif = durdurulmus = 0

        # Kullanıcı sayısı
        try:
            kullanici_count = await conn.fetchval(
                "SELECT COUNT(*) FROM shared.kullanicilar WHERE is_deleted = FALSE"
            ) or 0
        except Exception:
            kullanici_count = 0

        # Çağrı sayıları (tablo yoksa 0 döner)
        bugun_cagri = 0
        bu_ay_cagri = 0
        try:
            bugun_cagri = await conn.fetchval(
                "SELECT COUNT(*) FROM shared.cagri_loglari WHERE DATE(baslangic) = CURRENT_DATE"
            ) or 0
        except Exception:
            pass

        try:
            bu_ay_cagri = await conn.fetchval(
                """
                SELECT COALESCE(SUM(cagri_sayisi), 0) FROM shared.kullanim_sayaclari
                WHERE yil = EXTRACT(YEAR FROM CURRENT_DATE)
                AND ay = EXTRACT(MONTH FROM CURRENT_DATE)
                """
            ) or 0
        except Exception:
            pass

        sistem_saglik = "healthy"
        if durdurulmus > 0:
            sistem_saglik = "warning"

        return {
            "toplam_firma": toplam,
            "aktif_firma": aktif,
            "durdurulmus_firma": durdurulmus,
            "toplam_kullanici": int(kullanici_count),
            "bugun_cagri": int(bugun_cagri),
            "bu_ay_cagri": int(bu_ay_cagri),
            "sistem_saglik": sistem_saglik
        }


@router.get("/firmalar")
async def get_firmalar(
    durum: Optional[str] = None,
    sektor: Optional[str] = None,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        # Paketler tablosu var mı kontrol et
        has_paketler = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shared' AND table_name='paketler')"
        )
        has_cagri = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shared' AND table_name='cagri_loglari')"
        )
        has_kullanim = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shared' AND table_name='kullanim_sayaclari')"
        )

        if has_paketler and has_cagri and has_kullanim:
            query = """
                SELECT 
                    f.id, f.ad, f.sektor, f.durum, f.email, f.telefon, f.created_at,
                    COALESCE(p.ad, 'Temel') as paket_ad,
                    (SELECT MAX(baslangic) FROM shared.cagri_loglari WHERE firma_id = f.id) as son_cagri,
                    COALESCE(k.cagri_sayisi, 0) as bu_ay_cagri,
                    COALESCE(k.sms_sayisi, 0) as bu_ay_sms
                FROM shared.firmalar f
                LEFT JOIN shared.paketler p ON f.paket_id = p.id
                LEFT JOIN shared.kullanim_sayaclari k ON (
                    f.id = k.firma_id 
                    AND k.yil = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND k.ay = EXTRACT(MONTH FROM CURRENT_DATE)
                )
                WHERE f.is_deleted = FALSE
            """
        elif has_paketler:
            query = """
                SELECT 
                    f.id, f.ad, f.sektor, f.durum, f.email, f.telefon, f.created_at,
                    COALESCE(p.ad, 'Temel') as paket_ad,
                    NULL::timestamp as son_cagri,
                    0 as bu_ay_cagri,
                    0 as bu_ay_sms
                FROM shared.firmalar f
                LEFT JOIN shared.paketler p ON f.paket_id = p.id
                WHERE f.is_deleted = FALSE
            """
        else:
            query = """
                SELECT 
                    f.id, f.ad, f.sektor, f.durum, f.email, f.telefon, f.created_at,
                    'Temel'::text as paket_ad,
                    NULL::timestamp as son_cagri,
                    0 as bu_ay_cagri,
                    0 as bu_ay_sms
                FROM shared.firmalar f
                WHERE f.is_deleted = FALSE
            """

        params = []
        if durum:
            query += " AND f.durum = $1"
            params.append(durum)
        if sektor:
            param_num = len(params) + 1
            query += f" AND f.sektor = ${param_num}"
            params.append(sektor)

        query += " ORDER BY f.created_at DESC"

        rows = await conn.fetch(query, *params)

        result = []
        for row in rows:
            d = dict(row)
            result.append({
                "id": d["id"],
                "ad": d["ad"] or "",
                "sektor": d.get("sektor") or "",
                "paket_ad": d.get("paket_ad") or "Temel",
                "durum": d.get("durum") or "aktif",
                "email": d.get("email"),
                "telefon": d.get("telefon"),
                "created_at": d.get("created_at"),
                "son_cagri": d.get("son_cagri"),
                "bu_ay_cagri": int(d.get("bu_ay_cagri") or 0),
                "bu_ay_sms": int(d.get("bu_ay_sms") or 0),
            })
        return result


@router.post("/firmalar", status_code=status.HTTP_201_CREATED)
async def create_firma(
    firma: FirmaCreate,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Firma oluştur
            firma_id = await conn.fetchval(
                """
                INSERT INTO shared.firmalar 
                (ad, sektor, schema_adi, paket_id, email, telefon, adres, vergi_no, durum)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'aktif')
                RETURNING id
                """,
                firma.ad,
                firma.sektor,
                f"firma_{firma.ad.lower().replace(' ', '_')}",
                firma.paket_id,
                str(firma.email),
                firma.telefon,
                firma.adres,
                firma.vergi_no
            )

            # Schema oluştur
            schema_name = f"firma_{firma_id}"
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

            # Admin kullanıcısı oluştur
            await conn.execute(
                """
                INSERT INTO shared.kullanicilar 
                (firma_id, email, sifre_hash, ad, rol, aktif)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), $4, 'firma_admin', true)
                """,
                firma_id, str(firma.admin_email), firma.admin_sifre, firma.admin_ad
            )

            return {
                "id": firma_id,
                "message": "Firma başarıyla oluşturuldu",
                "schema": schema_name,
                "admin_email": str(firma.admin_email)
            }


@router.put("/firmalar/{firma_id}/durdur")
async def durdur_firma(
    firma_id: int,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE shared.firmalar SET durum = 'durduruldu', updated_at = NOW() WHERE id = $1 AND is_deleted = FALSE",
            firma_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return {"message": "Firma durduruldu", "firma_id": firma_id}


@router.put("/firmalar/{firma_id}/aktif")
async def aktif_et_firma(
    firma_id: int,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE shared.firmalar SET durum = 'aktif', updated_at = NOW() WHERE id = $1 AND is_deleted = FALSE",
            firma_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return {"message": "Firma aktif edildi", "firma_id": firma_id}


@router.get("/firmalar/{firma_id}")
async def get_firma_detay(
    firma_id: int,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        firma = await conn.fetchrow(
            "SELECT * FROM shared.firmalar WHERE id = $1 AND is_deleted = FALSE",
            firma_id
        )
        if not firma:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return dict(firma)


@router.delete("/firmalar/{firma_id}")
async def delete_firma(
    firma_id: int,
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE shared.firmalar SET is_deleted = TRUE, updated_at = NOW() WHERE id = $1",
            firma_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        await conn.execute(
            "UPDATE shared.kullanicilar SET aktif = FALSE, is_deleted = TRUE WHERE firma_id = $1",
            firma_id
        )
        return {"message": "Firma silindi", "firma_id": firma_id}


@router.get("/raporlar/gelir")
async def get_gelir_raporu(
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """Gelir raporu"""
    async with pool.acquire() as conn:
        # Faturalar tablosu varsa gerçek veri, yoksa boş döner
        try:
            has_faturalar = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shared' AND table_name='faturalar')"
            )
            if has_faturalar:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE_TRUNC('month', olusturma_tarihi) as ay,
                        SUM(tutar) as toplam,
                        COUNT(*) as fatura_sayisi
                    FROM shared.faturalar
                    WHERE durum = 'odendi'
                    GROUP BY 1
                    ORDER BY 1 DESC
                    LIMIT 12
                    """
                )
                return [dict(r) for r in rows]
        except Exception:
            pass

        # Demo veri
        return [
            {"ay": "2026-03-01", "toplam": 0, "fatura_sayisi": 0},
        ]


@router.get("/raporlar/cagrilar")
async def get_cagri_raporu(
    pool: Pool = Depends(get_db_pool),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """Çağrı raporu"""
    async with pool.acquire() as conn:
        try:
            has_cagri = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shared' AND table_name='cagri_loglari')"
            )
            if has_cagri:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE(baslangic) as tarih,
                        COUNT(*) as toplam_cagri,
                        AVG(EXTRACT(EPOCH FROM (bitis - baslangic))) as ort_sure
                    FROM shared.cagri_loglari
                    WHERE baslangic >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY 1
                    ORDER BY 1 DESC
                    """
                )
                return [dict(r) for r in rows]
        except Exception:
            pass

        return [{"tarih": str(datetime.now().date()), "toplam_cagri": 0, "ort_sure": 0}]


@router.get("/health")
async def admin_health():
    return {"status": "ok", "service": "admin"}
