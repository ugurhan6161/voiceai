"""
VoiceAI Platform — KVKK Uyum Modülü
Yeni Akış: Müşteri arayarak KVKK kabul etmiş sayılır.
Bilgilendirme yapılır ve devam edilir.
"""
import os
import logging
import asyncio
import aiohttp
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

ARI_BASE = os.getenv("ARI_BASE_URL", "http://172.17.0.1:8088")
ARI_USER = os.getenv("ARI_USERNAME", "voiceai")
ARI_PASS = os.getenv("ARI_PASSWORD", "voiceai123")

class KVKKHandler:
    """KVKK bilgilendirme yöneticisi"""

    def __init__(self):
        self.ari_auth = aiohttp.BasicAuth(ARI_USER, ARI_PASS)

    async def log_kvkk_bildirim(self, channel_id: str, caller_id: str):
        """KVKK bildirim zamanını ispat için loglar"""
        timestamp = datetime.now().isoformat()
        logger.info(f"[KVKK_LOG] Zaman: {timestamp}, Kanal: {channel_id}, Arayan: {caller_id}, Durum: Otomatik Kabul")
        # İleride burası DB'ye de yazılabilir

    async def kvkk_surecini_islet(self, channel_id: str, caller_id: str):
        """
        Her durumda devam eden yeni KVKK akışı.
        Asterisk dialplan zaten Playback yapıyor, 
        bu handler sadece loglama ve ek kontroller için.
        """
        try:
            await self.log_kvkk_bildirim(channel_id, caller_id)
            return True
        except Exception as e:
            logger.error(f"KVKK loglama hatası: {e}")
            return True

# Singleton
_kvkk_handler: Optional[KVKKHandler] = None

def get_kvkk_handler() -> KVKKHandler:
    global _kvkk_handler
    if _kvkk_handler is None:
        _kvkk_handler = KVKKHandler()
    return _kvkk_handler
