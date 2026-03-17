"""
VoiceAI Platform — Transfer Handler
AI'dan insana çağrı aktarımını yönetir.
"""
import os
import logging
import httpx
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

ARI_BASE = os.getenv("ARI_BASE_URL", "http://172.17.0.1:8088")
ARI_USER = os.getenv("ARI_USERNAME", "voiceai")
ARI_PASS = os.getenv("ARI_PASSWORD", "voiceai123")

# Aktarım tetikleyicileri (Keyword bazlı)
TRANSFER_KEYWORDS = [
    "yetkili", "insan", "bağla", "aktar", "müşteri temsilcisi",
    "operator", "human", "representative", "transfer"
]

def aktarim_gerekli_mi(text: str) -> Tuple[bool, str]:
    """Metin içinde aktarım isteği var mı kontrol et"""
    text = text.lower()
    for kw in TRANSFER_KEYWORDS:
        if kw in text:
            # Varsayılan olarak firma dahilisine (101) aktar
            return True, "101"
    return False, ""

class TransferHandler:
    """Çağrı aktarım yöneticisi"""

    def __init__(self):
        self.ari_auth = (ARI_USER, ARI_PASS)

    async def aktarim_metni_uret(self, history: List[Dict]) -> str:
        """Yetkiliye gösterilecek AI özetini üret"""
        text_parts = []
        for msg in history[-6:]:
            role = "Müşteri" if msg["role"] == "user" else "AI"
            text_parts.append(f"{role}: {msg['content']}")
        
        return " | ".join(text_parts)

    async def aktarim_yap(self, channel_id: str, hedef: str, ozet: str, firma_id: int):
        """Çağrıyı Asterisk üzerinden aktar"""
        try:
            logger.info(f"🔄 Aktarım başlatılıyor: {channel_id} -> {hedef} (Firma: {firma_id})")
            
            # 1. Özet bilgisini kanal değişkenine yaz (ispat için)
            async with httpx.AsyncClient(auth=self.ari_auth) as client:
                await client.post(
                    f"{ARI_BASE}/ari/channels/{channel_id}/variable",
                    params={"variable": "AI_OZET", "value": ozet[:250]}
                )
                
                # 2. Dialplan'a gönder (voiceai-transfer context)
                await client.post(
                    f"{ARI_BASE}/ari/channels/{channel_id}/continue",
                    params={
                        "context": "voiceai-transfer",
                        "extension": hedef,
                        "priority": "1"
                    }
                )
            
            logger.info(f"✅ Aktarım komutu gönderildi: {hedef}")
            return True
        except Exception as e:
            logger.error(f"Aktarım hatası: {e}")
            return False

# Singleton
_transfer_handler: Optional[TransferHandler] = None

def get_transfer_handler() -> TransferHandler:
    global _transfer_handler
    if _transfer_handler is None:
        _transfer_handler = TransferHandler()
    return _transfer_handler
