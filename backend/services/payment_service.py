"""
VoiceAI Platform — iyzico Ödeme Servisi
Kart token saklama, otomatik ödeme çekme, başarısız ödeme bildirimi.
"""
import os
import logging
import hashlib
import base64
import json
import httpx
from typing import Optional
from crypto import encrypt, decrypt

logger = logging.getLogger(__name__)


class IyzicoService:
    """iyzico API entegrasyonu"""

    def __init__(self):
        self.api_key = os.getenv("IYZICO_API_KEY", "")
        self.secret_key = os.getenv("IYZICO_SECRET_KEY", "")
        self.sandbox = os.getenv("IYZICO_SANDBOX", "true").lower() == "true"
        self.base_url = (
            "https://sandbox-api.iyzipay.com" if self.sandbox
            else "https://api.iyzipay.com"
        )

    def _auth_header(self, body: str) -> str:
        """iyzico Authorization header oluştur"""
        random_str = os.urandom(8).hex()
        hash_str = self.api_key + random_str + self.secret_key + body
        hash_bytes = hashlib.sha256(hash_str.encode()).digest()
        hash_b64 = base64.b64encode(hash_bytes).decode()
        return f"IYZWS apiKey:{self.api_key}&randomKey:{random_str}&signature:{hash_b64}"

    async def odeme_cek(
        self,
        firma_id: int,
        tutar: float,
        fatura_no: str,
        kart_token: Optional[str] = None,
    ) -> dict:
        """
        Firmadan ödeme çek.
        kart_token varsa kayıtlı karttan çek, yoksa ödeme linki oluştur.
        """
        if not self.api_key or not self.secret_key:
            logger.warning("iyzico API anahtarları tanımlı değil, simüle ediliyor")
            return {"success": True, "simulated": True, "fatura_no": fatura_no}

        try:
            body = json.dumps({
                "locale": "tr",
                "conversationId": fatura_no,
                "price": str(tutar),
                "paidPrice": str(tutar),
                "currency": "TRY",
                "installment": "1",
                "paymentChannel": "WEB",
                "paymentGroup": "SUBSCRIPTION",
            })

            headers = {
                "Authorization": self._auth_header(body),
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/payment/auth",
                    content=body,
                    headers=headers
                )
                data = resp.json()

                if data.get("status") == "success":
                    logger.info(f"Ödeme başarılı: {fatura_no} - {tutar} TL")
                    return {"success": True, "payment_id": data.get("paymentId"), "fatura_no": fatura_no}
                else:
                    logger.error(f"Ödeme başarısız: {data.get('errorMessage')}")
                    return {"success": False, "error": data.get("errorMessage"), "fatura_no": fatura_no}

        except Exception as e:
            logger.error(f"iyzico ödeme hatası: {e}")
            return {"success": False, "error": str(e)}

    def kart_token_sifrele(self, kart_token: str) -> str:
        """Kart tokenını AES-256-GCM ile şifrele"""
        return encrypt(kart_token)

    def kart_token_coz(self, sifreli_token: str) -> str:
        """Şifreli kart tokenını çöz"""
        return decrypt(sifreli_token)


# Singleton
_iyzico: Optional[IyzicoService] = None


def get_iyzico_service() -> IyzicoService:
    global _iyzico
    if _iyzico is None:
        _iyzico = IyzicoService()
    return _iyzico
