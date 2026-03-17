"""
VoiceAI — Klinik / Özel Muayenehane Şablonu
Randevu alma, doktor bilgisi, hizmetler
"""
from ..base_template import BaseTemplate


class KlinikTemplate(BaseTemplate):
    template_id = "klinik"
    template_adi = "Klinik / Muayenehane"
    sektor = "saglik"
    aciklama = "Özel klinik ve muayenehane için randevu ve bilgi asistanı"

    sistem_prompt_tr = """Sen {firma_adi} kliniğinin sesli resepsiyonistisin.
Görevlerin:
1. Randevu almak (ad, telefon, doktor tercihi, tarih/saat)
2. Doktorlar ve uzmanlık alanları hakkında bilgi vermek
3. Hizmetler ve fiyatlar hakkında bilgi vermek
4. Sigorta ve ödeme seçenekleri hakkında bilgi vermek
5. Acil durumlarda 112'ye yönlendirmek

Randevu alırken şunları sor:
- Hasta adı soyadı
- Telefon numarası
- Hangi doktor veya bölüm
- Tercih edilen tarih ve saat
- Şikayet/neden (kısaca)

Önemli: Tıbbi teşhis veya tedavi önerme. Sadece randevu ve bilgi ver.
Acil durumlarda: "Lütfen hemen 112'yi arayın veya en yakın acil servise gidin."
"""

    sistem_prompt_en = """You are the voice receptionist of {firma_adi} clinic.
Your duties:
1. Schedule appointments (name, phone, doctor preference, date/time)
2. Provide information about doctors and specialties
3. Provide information about services and prices
4. Guide about insurance and payment options
5. Direct emergencies to 112

Important: Do not provide medical diagnosis or treatment advice.
For emergencies: "Please call 112 immediately or go to the nearest emergency room."
"""

    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Size nasıl yardımcı olabilirim?"
    karsilama_en = "Hello, welcome to {firma_adi}. How can I help you?"

    fonksiyonlar = [
        {
            "name": "randevu_al",
            "description": "Hasta için randevu oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "hasta_adi": {"type": "string", "description": "Hasta adı soyadı"},
                    "telefon": {"type": "string", "description": "Telefon numarası"},
                    "doktor": {"type": "string", "description": "Doktor adı veya bölüm"},
                    "tarih": {"type": "string", "description": "Randevu tarihi (GG/AA/YYYY)"},
                    "saat": {"type": "string", "description": "Randevu saati (SS:DD)"},
                    "sikayet": {"type": "string", "description": "Kısa şikayet açıklaması"},
                },
                "required": ["hasta_adi", "telefon", "doktor", "tarih", "saat"],
            },
        },
        {
            "name": "randevu_iptal",
            "description": "Mevcut randevuyu iptal et",
            "parameters": {
                "type": "object",
                "properties": {
                    "hasta_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "tarih": {"type": "string"},
                },
                "required": ["telefon"],
            },
        },
        {
            "name": "doktor_listesi",
            "description": "Klinikte çalışan doktorları listele",
            "parameters": {"type": "object", "properties": {}},
        },
    ]

    slot_filling_config = {
        "randevu_al": {
            "slots": ["hasta_adi", "telefon", "doktor", "tarih", "saat"],
            "sorular": {
                "hasta_adi": "Hastanın adı soyadı nedir?",
                "telefon": "Telefon numaranızı alabilir miyim?",
                "doktor": "Hangi doktorumuza veya hangi bölüme randevu almak istiyorsunuz?",
                "tarih": "Hangi tarih için randevu almak istiyorsunuz?",
                "saat": "Saat tercihiniz nedir?",
            },
        }
    }

    def get_db_schema(self) -> str:
        return "klinik_schema.sql"
