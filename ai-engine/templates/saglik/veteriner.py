"""VoiceAI — Veteriner Kliniği Şablonu"""
from ..base_template import BaseTemplate

class VeterinerTemplate(BaseTemplate):
    template_id = "veteriner"
    template_adi = "Veteriner Kliniği"
    sektor = "saglik"
    aciklama = "Veteriner kliniği için randevu ve bilgi asistanı"

    sistem_prompt_tr = """Sen {firma_adi} veteriner kliniğinin sesli resepsiyonistisin.
Görevlerin: randevu almak, hizmetler hakkında bilgi vermek.
Randevu için: sahip adı, telefon, hayvan türü/adı, şikayet, tarih/saat bilgilerini al.
Acil durum (zehirlenme, kaza): "Lütfen hemen kliniğimize gelin veya acil veteriner hattını arayın."
"""
    karsilama_tr = "Merhaba, {firma_adi} Veteriner Kliniği'ne hoş geldiniz. Nasıl yardımcı olabilirim?"

    fonksiyonlar = [
        {
            "name": "randevu_al",
            "description": "Veteriner randevusu oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "sahip_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "hayvan_turu": {"type": "string", "description": "Kedi, köpek, kuş vb."},
                    "hayvan_adi": {"type": "string"},
                    "sikayet": {"type": "string"},
                    "tarih": {"type": "string"},
                    "saat": {"type": "string"},
                },
                "required": ["sahip_adi", "telefon", "hayvan_turu", "tarih", "saat"],
            },
        }
    ]

    slot_filling_config = {
        "randevu_al": {
            "slots": ["sahip_adi", "telefon", "hayvan_turu", "tarih", "saat"],
            "sorular": {
                "sahip_adi": "Adınız soyadınız nedir?",
                "telefon": "Telefon numaranız?",
                "hayvan_turu": "Hangi hayvanınız için randevu almak istiyorsunuz?",
                "tarih": "Hangi tarih uygun?",
                "saat": "Saat tercihiniz?",
            },
        }
    }
