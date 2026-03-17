"""
Slot Filling Engine
Eksik bilgileri tespit eder ve kullanıcıdan sorar.
Tüm slotlar dolunca fonksiyonu çağırır.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class SlotFillingEngine:
    """Slot filling ve konuşma akışı yönetimi."""
    
    def __init__(self):
        # Fonksiyon başına gerekli slotlar
        self.function_slots = {
            "rezervasyon_al": {
                "required": ["tarih", "saat", "kisi_sayisi", "isim", "telefon"],
                "optional": ["notlar"],
                "prompts": {
                    "tarih": "Hangi tarih için rezervasyon yapmak istiyorsunuz?",
                    "saat": "Saat kaçta gelmeyi planlıyorsunuz?",
                    "kisi_sayisi": "Kaç kişilik rezervasyon yapacaksınız?",
                    "isim": "Adınız nedir?",
                    "telefon": "İletişim için telefon numaranızı alabilir miyim?"
                }
            },
            "rezervasyon_sorgula": {
                "required": ["telefon"],
                "optional": [],
                "prompts": {
                    "telefon": "Rezervasyonunuzu sorgulamak için telefon numaranızı alabilir miyim?"
                }
            },
            "rezervasyon_iptal": {
                "required": ["rezervasyon_id"],
                "optional": [],
                "prompts": {
                    "rezervasyon_id": "İptal etmek istediğiniz rezervasyon numaranız nedir?"
                }
            },
            "fiyat_sor": {
                "required": [],
                "optional": ["hizmet_turu"],
                "prompts": {
                    "hizmet_turu": "Hangi hizmet için fiyat öğrenmek istiyorsunuz?"
                }
            },
            "musaitlik_kontrol": {
                "required": ["tarih"],
                "optional": ["saat"],
                "prompts": {
                    "tarih": "Hangi tarih için müsaitlik kontrol etmek istiyorsunuz?",
                    "saat": "Belirli bir saat var mı?"
                }
            }
        }
        
        # Aktif konuşma durumları (call_id -> state)
        self.conversation_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("SlotFillingEngine initialized")
    
    def start_conversation(self, call_id: str, intent: str, initial_slots: Dict[str, Any] = None):
        """
        Yeni bir konuşma başlatır.
        
        Args:
            call_id: Çağrı ID
            intent: Tespit edilen niyet (fonksiyon adı)
            initial_slots: İlk tespit edilen slotlar
        """
        self.conversation_states[call_id] = {
            "intent": intent,
            "slots": initial_slots or {},
            "missing_slots": [],
            "current_slot": None,
            "attempts": 0,
            "max_attempts": 3,
            "started_at": datetime.now()
        }
        
        # Eksik slotları belirle
        self._update_missing_slots(call_id)
        
        logger.info(f"📝 Conversation started: call_id={call_id}, intent={intent}")
    
    def _update_missing_slots(self, call_id: str):
        """Eksik slotları günceller."""
        state = self.conversation_states.get(call_id)
        if not state:
            return
        
        intent = state["intent"]
        if intent not in self.function_slots:
            return
        
        required_slots = self.function_slots[intent]["required"]
        filled_slots = state["slots"]
        
        missing = [slot for slot in required_slots if slot not in filled_slots or not filled_slots[slot]]
        state["missing_slots"] = missing
        
        logger.debug(f"Missing slots for {call_id}: {missing}")
    
    def process_user_input(
        self, 
        call_id: str, 
        user_input: str,
        caller_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kullanıcı girdisini işler ve slot doldurma yapar.
        
        Args:
            call_id: Çağrı ID
            user_input: Kullanıcının söylediği metin
            caller_id: Arayan telefon numarası
        
        Returns:
            Sonraki adım bilgisi
        """
        state = self.conversation_states.get(call_id)
        if not state:
            return {
                "status": "error",
                "message": "Konuşma durumu bulunamadı."
            }
        
        # Mevcut slot için değer çıkar
        if state["current_slot"]:
            extracted_value = self._extract_slot_value(
                state["current_slot"], 
                user_input,
                caller_id
            )
            
            if extracted_value:
                state["slots"][state["current_slot"]] = extracted_value
                state["attempts"] = 0
                logger.info(f"✅ Slot filled: {state['current_slot']} = {extracted_value}")
            else:
                state["attempts"] += 1
                logger.warning(f"⚠️ Failed to extract slot: {state['current_slot']}, attempt {state['attempts']}")
                
                if state["attempts"] >= state["max_attempts"]:
                    return {
                        "status": "failed",
                        "message": "Üzgünüm, bilgiyi anlayamadım. Lütfen daha sonra tekrar deneyin."
                    }
                
                return {
                    "status": "retry",
                    "message": f"Üzgünüm, anlayamadım. {self.function_slots[state['intent']]['prompts'][state['current_slot']]}"
                }
        
        # Eksik slotları güncelle
        self._update_missing_slots(call_id)
        
        # Tüm slotlar doldu mu?
        if not state["missing_slots"]:
            return {
                "status": "complete",
                "intent": state["intent"],
                "slots": state["slots"],
                "message": "Tüm bilgiler alındı, işleminiz gerçekleştiriliyor..."
            }
        
        # Sonraki eksik slotu sor
        next_slot = state["missing_slots"][0]
        state["current_slot"] = next_slot
        
        prompt = self.function_slots[state["intent"]]["prompts"].get(
            next_slot,
            f"{next_slot} bilgisini alabilir miyim?"
        )
        
        return {
            "status": "asking",
            "current_slot": next_slot,
            "message": prompt
        }
    
    def _extract_slot_value(
        self, 
        slot_name: str, 
        user_input: str,
        caller_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Kullanıcı girdisinden slot değerini çıkarır.
        
        Args:
            slot_name: Slot adı
            user_input: Kullanıcı girdisi
            caller_id: Arayan telefon numarası
        
        Returns:
            Çıkarılan değer veya None
        """
        user_input = user_input.lower().strip()
        
        # Tarih çıkarma
        if slot_name == "tarih":
            return self._extract_date(user_input)
        
        # Saat çıkarma
        elif slot_name == "saat":
            return self._extract_time(user_input)
        
        # Kişi sayısı çıkarma
        elif slot_name == "kisi_sayisi":
            return self._extract_number(user_input)
        
        # İsim çıkarma
        elif slot_name == "isim":
            return self._extract_name(user_input)
        
        # Telefon çıkarma
        elif slot_name == "telefon":
            # Önce caller_id'yi kullan
            if caller_id:
                return caller_id
            return self._extract_phone(user_input)
        
        # Rezervasyon ID çıkarma
        elif slot_name == "rezervasyon_id":
            return self._extract_number(user_input)
        
        # Hizmet türü
        elif slot_name == "hizmet_turu":
            return user_input
        
        # Genel metin
        else:
            return user_input if user_input else None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Tarih çıkarır (YYYY-MM-DD formatında)."""
        today = datetime.now()
        
        # Bugün, yarın, öbür gün
        if "bugün" in text:
            return today.strftime("%Y-%m-%d")
        elif "yarın" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "öbür gün" in text or "öbürgün" in text:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Gün adları (pazartesi, salı, vb.)
        gun_adlari = {
            "pazartesi": 0, "salı": 1, "çarşamba": 2, "perşembe": 3,
            "cuma": 4, "cumartesi": 5, "pazar": 6
        }
        
        for gun, index in gun_adlari.items():
            if gun in text:
                days_ahead = index - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        # DD/MM/YYYY veya DD.MM.YYYY formatı
        date_pattern = r'(\d{1,2})[/\.](\d{1,2})[/\.](\d{4})'
        match = re.search(date_pattern, text)
        if match:
            day, month, year = match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # DD/MM formatı (bu yıl)
        date_pattern_short = r'(\d{1,2})[/\.](\d{1,2})'
        match = re.search(date_pattern_short, text)
        if match:
            day, month = match.groups()
            try:
                date_obj = datetime(today.year, int(month), int(day))
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Saat çıkarır (HH:MM formatında)."""
        # HH:MM formatı
        time_pattern = r'(\d{1,2})[:\.](\d{2})'
        match = re.search(time_pattern, text)
        if match:
            hour, minute = match.groups()
            try:
                time_obj = datetime.strptime(f"{hour}:{minute}", "%H:%M")
                return time_obj.strftime("%H:%M")
            except ValueError:
                pass
        
        # Sadece saat (örn: "14", "saat 14")
        hour_pattern = r'(?:saat\s+)?(\d{1,2})(?:\s+sularında)?'
        match = re.search(hour_pattern, text)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
        # Öğle, akşam, sabah
        if "öğle" in text or "öğlen" in text:
            return "12:00"
        elif "akşam" in text:
            return "19:00"
        elif "sabah" in text:
            return "09:00"
        
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Sayı çıkarır."""
        # Rakamları bul
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        
        # Yazılı sayılar
        sayi_sozluk = {
            "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5,
            "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10
        }
        
        for kelime, sayi in sayi_sozluk.items():
            if kelime in text:
                return sayi
        
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """İsim çıkarır."""
        # "Adım X" veya "Ben X" kalıpları
        patterns = [
            r'(?:adım|ismim|benim adım)\s+(\w+(?:\s+\w+)?)',
            r'ben\s+(\w+(?:\s+\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        # Sadece kelimeler varsa (kısa cevap)
        words = text.split()
        if 1 <= len(words) <= 3:
            # Yaygın dolgu kelimelerini filtrele
            filler_words = {"evet", "hayır", "tamam", "peki", "efendim", "ben", "benim"}
            filtered = [w for w in words if w.lower() not in filler_words]
            if filtered:
                return " ".join(filtered).title()
        
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Telefon numarası çıkarır."""
        # Rakamları temizle
        digits = re.sub(r'\D', '', text)
        
        # 10 veya 11 haneli telefon
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('0'):
            return digits[1:]  # Başındaki 0'ı kaldır
        
        return None
    
    def get_conversation_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Konuşma durumunu döndürür."""
        return self.conversation_states.get(call_id)
    
    def end_conversation(self, call_id: str):
        """Konuşmayı sonlandırır."""
        if call_id in self.conversation_states:
            del self.conversation_states[call_id]
            logger.info(f"🏁 Conversation ended: call_id={call_id}")
    
    def is_complete(self, call_id: str) -> bool:
        """Tüm slotların dolu olup olmadığını kontrol eder."""
        state = self.conversation_states.get(call_id)
        if not state:
            return False
        
        self._update_missing_slots(call_id)
        return len(state["missing_slots"]) == 0


# Global instance
slot_engine = SlotFillingEngine()
