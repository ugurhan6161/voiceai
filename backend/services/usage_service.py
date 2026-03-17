"""
VoiceAI Platform — Kullanım Sayacı Servisi
Her çağrı ve SMS'de Redis sayacını artırır, gün sonu PostgreSQL'e kaydeder.
"""
import os
import logging
from datetime import datetime
import redis

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "voiceai-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")


def _get_redis():
    if REDIS_PASSWORD:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def cagri_sayaci_artir(firma_id: int):
    """Her çağrıda Redis sayacını artır"""
    try:
        r = _get_redis()
        now = datetime.now()
        key = f"voiceai:kullanim:{firma_id}:cagri:{now.year}:{now.month}"
        r.incr(key)
        r.expire(key, 86400 * 35)  # 35 gün TTL
        r.close()
    except Exception as e:
        logger.error(f"Çağrı sayacı artırma hatası: {e}")


def sms_sayaci_artir(firma_id: int):
    """Her SMS'de Redis sayacını artır"""
    try:
        r = _get_redis()
        now = datetime.now()
        key = f"voiceai:kullanim:{firma_id}:sms:{now.year}:{now.month}"
        r.incr(key)
        r.expire(key, 86400 * 35)
        r.close()
    except Exception as e:
        logger.error(f"SMS sayacı artırma hatası: {e}")


def kullanim_getir(firma_id: int) -> dict:
    """Firma'nın bu ayki kullanımını Redis'ten getir"""
    try:
        r = _get_redis()
        now = datetime.now()
        cagri_key = f"voiceai:kullanim:{firma_id}:cagri:{now.year}:{now.month}"
        sms_key = f"voiceai:kullanim:{firma_id}:sms:{now.year}:{now.month}"
        cagri = int(r.get(cagri_key) or 0)
        sms = int(r.get(sms_key) or 0)
        r.close()
        return {"cagri_sayisi": cagri, "sms_sayisi": sms, "ay": now.month, "yil": now.year}
    except Exception as e:
        logger.error(f"Kullanım getirme hatası: {e}")
        return {"cagri_sayisi": 0, "sms_sayisi": 0}


async def asim_kontrol(firma_id: int, paket_cagri_limiti: int, paket_sms_limiti: int) -> dict:
    """Paket limitini kontrol et, aşım varsa bildir"""
    kullanim = kullanim_getir(firma_id)
    cagri = kullanim["cagri_sayisi"]
    sms = kullanim["sms_sayisi"]

    cagri_oran = (cagri / paket_cagri_limiti * 100) if paket_cagri_limiti > 0 else 0
    sms_oran = (sms / paket_sms_limiti * 100) if paket_sms_limiti > 0 else 0

    uyari = None
    if cagri_oran >= 100 or sms_oran >= 100:
        uyari = "limit_asimi"
    elif cagri_oran >= 95 or sms_oran >= 95:
        uyari = "yuzde_95"
    elif cagri_oran >= 85 or sms_oran >= 85:
        uyari = "yuzde_85"
    elif cagri_oran >= 70 or sms_oran >= 70:
        uyari = "yuzde_70"

    return {
        "cagri_sayisi": cagri,
        "sms_sayisi": sms,
        "cagri_oran": round(cagri_oran, 1),
        "sms_oran": round(sms_oran, 1),
        "uyari": uyari,
    }
