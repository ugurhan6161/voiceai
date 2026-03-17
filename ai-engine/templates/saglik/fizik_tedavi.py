"""VoiceAI — Fizik Tedavi ve Rehabilitasyon Şablonu"""
from ..base_template import BaseTemplate

class FizikTedaviTemplate(BaseTemplate):
    template_id = "fizik_tedavi"
    template_adi = "Fizik Tedavi ve Rehabilitasyon"
    sektor = "saglik"
    aciklama = "Fizik tedavi merkezi için randevu asistanı"

    sistem_prompt_tr = """Sen {firma_adi} fizik tedavi merkezinin sesli resepsiyonistisin.
Görevlerin: randevu almak, tedaviler hakkında bilgi vermek.
Randevu için: ad soyad, telefon, şikayet/bölge, doktor sevki var mı, tarih/saat.
"""
    karsilama_tr = "Merhaba, {firma_adi} Fizik Tedavi Merkezi'ne hoş geldiniz. Nasıl yardımcı olabilirim?"

    fonksiyonlar = [
        {
            "name": "randevu_al",
            "description": "Fizik tedavi randevusu oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "hasta_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "sikayet_bolgesi": {"type": "string"},
                    "doktor_sevki": {"type": "boolean"},
                    "tarih": {"type": "string"},
                    "saat": {"type": "string"},
                },
                "required": ["hasta_adi", "telefon", "tarih", "saat"],
            },
        }
    ]

    slot_filling_config = {
        "randevu_al": {
            "slots": ["hasta_adi", "telefon", "sikayet_bolgesi", "tarih", "saat"],
            "sorular": {
                "hasta_adi": "Adınız soyadınız?",
                "telefon": "Telefon numaranız?",
                "sikayet_bolgesi": "Hangi bölgeniz için tedavi almak istiyorsunuz?",
                "tarih": "Hangi tarih uygun?",
                "saat": "Saat tercihiniz?",
            },
        }
    }
