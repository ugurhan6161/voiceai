"""
VoiceAI Platform — SIP Provision Servisi
Yeni firma eklenince otomatik dahili hat oluşturur.
pjsip.conf'a endpoint ekler ve Asterisk'i reload eder.
"""
import os
import secrets
import string
import subprocess
import logging
import asyncpg
from typing import Optional

logger = logging.getLogger(__name__)

PJSIP_CONF = "/etc/asterisk/pjsip.conf"
PJSIP_CONF_BACKUP = "/opt/voiceai/asterisk/pjsip.conf"
DB_URL = os.getenv("DATABASE_URL", "postgresql://voiceai_user:voiceai_pass@voiceai-postgres:5432/voiceai")

DAHILI_BASLANGIC = 101  # İlk dahili numarası


def guclu_sifre_uret(uzunluk: int = 16) -> str:
    """Güvenli rastgele şifre üret"""
    alfabe = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(alfabe) for _ in range(uzunluk))


def sonraki_dahili_no(mevcut_dahililer: list) -> str:
    """Mevcut dahililerden sonraki boş numarayı bul"""
    if not mevcut_dahililer:
        return str(DAHILI_BASLANGIC)
    max_no = max(int(d) for d in mevcut_dahililer if d.isdigit())
    return str(max_no + 1)


def pjsip_endpoint_ekle(firma_id: int, kullanici_adi: str, sifre: str, dahili_no: str):
    """pjsip.conf'a yeni endpoint ekle"""
    blok = f"""
; ── FİRMA {firma_id} DAHİLİ ──────────────────────────────────
[{kullanici_adi}]
type=endpoint
context=voiceai-transfer
disallow=all
allow=ulaw
allow=alaw
auth={kullanici_adi}-auth
aors={kullanici_adi}-aor
direct_media=no
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes

[{kullanici_adi}-auth]
type=auth
auth_type=userpass
username={kullanici_adi}
password={sifre}

[{kullanici_adi}-aor]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=30
"""
    # /etc/asterisk/pjsip.conf'a ekle
    try:
        with open(PJSIP_CONF, "a") as f:
            f.write(blok)
        logger.info(f"✅ pjsip.conf güncellendi: {kullanici_adi}")
    except Exception as e:
        logger.error(f"pjsip.conf yazma hatası: {e}")
        raise

    # Yedek dosyaya da ekle
    try:
        with open(PJSIP_CONF_BACKUP, "a") as f:
            f.write(blok)
    except Exception as e:
        logger.warning(f"Yedek pjsip.conf yazma hatası: {e}")


def asterisk_reload():
    """Asterisk'i yeniden yükle"""
    try:
        result = subprocess.run(
            ["asterisk", "-rx", "core reload"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            logger.info("✅ Asterisk reload edildi")
        else:
            logger.warning(f"Asterisk reload uyarı: {result.stderr}")
    except Exception as e:
        logger.error(f"Asterisk reload hatası: {e}")


async def firma_dahili_olustur(firma_id: int) -> dict:
    """
    Yeni firma için SIP dahili hat oluştur.
    
    Returns:
        {
            "dahili_no": "101",
            "kullanici_adi": "firma_1_dahili",
            "sifre": "...",
            "sunucu": "31.57.77.166",
            "port": "5060"
        }
    """
    try:
        conn = await asyncpg.connect(DB_URL)

        # Mevcut dahili numaralarını al
        rows = await conn.fetch("SELECT dahili_no FROM shared.sip_dahilileri")
        mevcut = [r["dahili_no"] for r in rows]

        # Yeni dahili no ve kullanıcı adı
        dahili_no = sonraki_dahili_no(mevcut)
        kullanici_adi = f"firma_{firma_id}_dahili"
        sifre = guclu_sifre_uret()

        # DB'ye kaydet
        await conn.execute("""
            INSERT INTO shared.sip_dahilileri
                (firma_id, dahili_no, kullanici_adi, sifre_hash, yonlendirme_turu)
            VALUES ($1, $2, $3, $4, 'uygulama')
            ON CONFLICT (kullanici_adi) DO UPDATE
            SET sifre_hash = $4, updated_at = NOW()
        """, firma_id, dahili_no, kullanici_adi, sifre)

        # Yönlendirme ayarı oluştur
        await conn.execute("""
            INSERT INTO shared.yonlendirme_ayarlari (firma_id, aktif_tur)
            VALUES ($1, 'uygulama')
            ON CONFLICT (firma_id) DO NOTHING
        """, firma_id)

        await conn.close()

        # pjsip.conf'a ekle
        pjsip_endpoint_ekle(firma_id, kullanici_adi, sifre, dahili_no)

        # Asterisk reload
        asterisk_reload()

        bilgi = {
            "dahili_no": dahili_no,
            "kullanici_adi": kullanici_adi,
            "sifre": sifre,
            "sunucu": os.getenv("VPS_IP", "31.57.77.166"),
            "port": "5060",
            "domain": os.getenv("VPS_IP", "31.57.77.166"),
        }

        logger.info(f"✅ Firma {firma_id} dahili oluşturuldu: {dahili_no} / {kullanici_adi}")
        return bilgi

    except Exception as e:
        logger.error(f"Dahili oluşturma hatası: {e}")
        raise


async def firma_dahili_sil(firma_id: int):
    """Firma dahilisini sil (firma silinince)"""
    try:
        conn = await asyncpg.connect(DB_URL)
        row = await conn.fetchrow(
            "SELECT kullanici_adi FROM shared.sip_dahilileri WHERE firma_id = $1",
            firma_id
        )
        if row:
            kullanici_adi = row["kullanici_adi"]
            await conn.execute(
                "DELETE FROM shared.sip_dahilileri WHERE firma_id = $1", firma_id
            )
            logger.info(f"✅ Firma {firma_id} dahili silindi: {kullanici_adi}")
            # pjsip.conf'tan silmek için reload yeterli (DB'den okuma yapılmıyor)
            asterisk_reload()
        await conn.close()
    except Exception as e:
        logger.error(f"Dahili silme hatası: {e}")


async def firma_dahili_bilgi(firma_id: int) -> Optional[dict]:
    """Firma dahili bilgilerini getir"""
    try:
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

        if row:
            return {
                "dahili_no": row["dahili_no"],
                "kullanici_adi": row["kullanici_adi"],
                "yonlendirme_turu": row["yonlendirme_turu"],
                "telefon_no": row["telefon_no"],
                "aktif": row["aktif"],
                "son_kayit": row["son_kayit"].isoformat() if row["son_kayit"] else None,
                "sunucu": os.getenv("VPS_IP", "31.57.77.166"),
                "port": "5060",
            }
        return None
    except Exception as e:
        logger.error(f"Dahili bilgi hatası: {e}")
        return None
