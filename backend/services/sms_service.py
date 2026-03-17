"""
Netgsm SMS Servisi — Rezervasyon ve Bildirim SMS'leri
"""
import os
import httpx
from typing import Dict, Optional, Any
from datetime import datetime
from celery_app import celery


class NetgsmSMSService:
    """
    Netgsm HTTP API ile SMS gönderimi
    """
    
    def __init__(self):
        self.username = os.getenv("NETGSM_SMS_USERNAME", "")
        self.password = os.getenv("NETGSM_SMS_PASSWORD", "")
        self.api_url = "https://api.netgsm.com.tr/sms/send/get"
        self.header = "VOICEAI"  # SMS başlığı (Netgsm'de tanımlı olmalı)
    
    def _validate_phone(self, phone: str) -> str:
        """
        Telefon numarasını temizle ve doğrula
        
        Args:
            phone: Telefon numarası
        
        Returns:
            Temizlenmiş telefon (5XXXXXXXXX formatında)
        """
        # Boşluk, tire, parantez temizle
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # +90 veya 90 ile başlıyorsa kaldır
        if phone.startswith("+90"):
            phone = phone[3:]
        elif phone.startswith("90"):
            phone = phone[2:]
        
        # 0 ile başlıyorsa kaldır
        if phone.startswith("0"):
            phone = phone[1:]
        
        # 10 haneli olmalı ve 5 ile başlamalı
        if len(phone) != 10 or not phone.startswith("5"):
            raise ValueError(f"Geçersiz telefon numarası: {phone}")
        
        return phone
    
    async def send_sms(
        self,
        phone: str,
        message: str,
        header: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        SMS gönder
        
        Args:
            phone: Alıcı telefon numarası
            message: SMS metni
            header: SMS başlığı (opsiyonel, varsayılan: VOICEAI)
        
        Returns:
            Gönderim sonucu
        """
        try:
            # Telefon doğrula
            clean_phone = self._validate_phone(phone)
            
            # API parametreleri
            params = {
                "usercode": self.username,
                "password": self.password,
                "gsmno": clean_phone,
                "message": message,
                "msgheader": header or self.header,
                "dil": "TR"
            }
            
            # API'ye istek gönder
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.api_url, params=params)
                
                # Yanıt kontrolü
                response_text = response.text.strip()
                
                # Netgsm yanıt kodları:
                # 00 veya 01 = Başarılı
                # 20 = Mesaj metni boş
                # 30 = Geçersiz kullanıcı adı/şifre
                # 40 = Mesaj başlığı tanımsız
                # 50 = Geçersiz numara
                # 51 = Kara listede
                # 70 = Hatalı sorgu
                # 85 = Başlık kullanıcıya tanımlı değil
                
                if response_text.startswith("00") or response_text.startswith("01"):
                    # Başarılı
                    message_id = response_text.split(" ")[1] if " " in response_text else response_text
                    return {
                        "success": True,
                        "message_id": message_id,
                        "phone": clean_phone,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Hata
                    error_messages = {
                        "20": "Mesaj metni boş",
                        "30": "Geçersiz kullanıcı adı veya şifre",
                        "40": "Mesaj başlığı tanımsız",
                        "50": "Geçersiz telefon numarası",
                        "51": "Numara kara listede",
                        "70": "Hatalı sorgu",
                        "85": "Başlık kullanıcıya tanımlı değil"
                    }
                    
                    error_code = response_text[:2]
                    error_msg = error_messages.get(error_code, f"Bilinmeyen hata: {response_text}")
                    
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error": error_msg,
                        "phone": clean_phone
                    }
        
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SMS gönderim hatası: {str(e)}"
            }
    
    async def send_reservation_confirmation(
        self,
        phone: str,
        customer_name: str,
        reservation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rezervasyon onay SMS'i gönder
        
        Args:
            phone: Müşteri telefonu
            customer_name: Müşteri adı
            reservation_details: Rezervasyon detayları
        
        Returns:
            Gönderim sonucu
        """
        # SMS metnini oluştur
        check_in = reservation_details.get("check_in_date", "")
        check_out = reservation_details.get("check_out_date", "")
        room_type = reservation_details.get("room_type", "")
        guest_count = reservation_details.get("guest_count", "")
        
        message = f"""Sayın {customer_name},

Rezervasyonunuz onaylandı!

Giriş: {check_in}
Çıkış: {check_out}
Oda: {room_type}
Kişi: {guest_count}

İyi günler dileriz.
"""
        
        return await self.send_sms(phone, message)
    
    async def send_appointment_confirmation(
        self,
        phone: str,
        customer_name: str,
        appointment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Randevu onay SMS'i gönder
        
        Args:
            phone: Müşteri telefonu
            customer_name: Müşteri adı
            appointment_details: Randevu detayları
        
        Returns:
            Gönderim sonucu
        """
        date = appointment_details.get("date", "")
        time = appointment_details.get("time", "")
        service = appointment_details.get("service", "")
        
        message = f"""Sayın {customer_name},

Randevunuz onaylandı!

Tarih: {date}
Saat: {time}
Hizmet: {service}

Görüşmek üzere.
"""
        
        return await self.send_sms(phone, message)
    
    async def send_order_confirmation(
        self,
        phone: str,
        customer_name: str,
        order_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sipariş onay SMS'i gönder
        
        Args:
            phone: Müşteri telefonu
            customer_name: Müşteri adı
            order_details: Sipariş detayları
        
        Returns:
            Gönderim sonucu
        """
        service = order_details.get("service", "")
        date = order_details.get("pickup_date", "")
        address = order_details.get("address", "")
        
        message = f"""Sayın {customer_name},

Siparişiniz alındı!

Hizmet: {service}
Tarih: {date}
Adres: {address}

Teşekkür ederiz.
"""
        
        return await self.send_sms(phone, message)


# Celery task olarak SMS gönderimi
@celery.task(name="sms.send_sms", queue="sms")
def send_sms_task(phone: str, message: str, header: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task: SMS gönder (async wrapper)
    """
    import asyncio
    
    service = NetgsmSMSService()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(service.send_sms(phone, message, header))
    
    return result


@celery.task(name="sms.send_reservation_confirmation", queue="sms")
def send_reservation_confirmation_task(
    phone: str,
    customer_name: str,
    reservation_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Rezervasyon onay SMS'i gönder
    """
    import asyncio
    
    service = NetgsmSMSService()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        service.send_reservation_confirmation(phone, customer_name, reservation_details)
    )
    
    return result


@celery.task(name="sms.send_appointment_confirmation", queue="sms")
def send_appointment_confirmation_task(
    phone: str,
    customer_name: str,
    appointment_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Randevu onay SMS'i gönder
    """
    import asyncio
    
    service = NetgsmSMSService()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        service.send_appointment_confirmation(phone, customer_name, appointment_details)
    )
    
    return result


@celery.task(name="sms.send_order_confirmation", queue="sms")
def send_order_confirmation_task(
    phone: str,
    customer_name: str,
    order_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Sipariş onay SMS'i gönder
    """
    import asyncio
    
    service = NetgsmSMSService()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        service.send_order_confirmation(phone, customer_name, order_details)
    )
    
    return result


# Singleton instance
_sms_service: Optional[NetgsmSMSService] = None


def get_sms_service() -> NetgsmSMSService:
    """Global SMS service instance döndür"""
    global _sms_service
    if _sms_service is None:
        _sms_service = NetgsmSMSService()
    return _sms_service
