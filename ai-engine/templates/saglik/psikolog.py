"""VoiceAI — Psikolog / Psikolojik Danışmanlık Şablonu"""
from ..base_template import BaseTemplate

class PsikologTemplate(BaseTemplate):
    template_id = "psikolog"
    template_adi = "Psikolog / Psikolojik Danışmanlık"
    sektor = "saglik"
    aciklama = "Psikolojik danışmanlık merkezi için randevu asistanı"

    sistem_prompt_tr = """Sen {firma_adi} psikolojik danışmanlık merkezinin sesli resepsiyonistisin.
Görevlerin: randevu almak, hizmetler hakkında bilgi vermek.
Gizlilik önemlidir. Kişisel bilgileri dikkatli işle.
Acil kriz durumunda: "Lütfen 182 (ALO Psikiyatri Hattı) veya 182'yi arayın."
"""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Size nasıl yardımcı olabilirim?"

    fonksiyonlar = [
        {
            "name": "randevu_al",
            "description": "Danışmanlık seansı randevusu oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "danisan_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "uzman_tercihi": {"type": "string"},
                    "seans_turu": {"type": "string", "description": "Bireysel, çift, aile vb."},
                    "tarih": {"type": "string"},
                    "saat": {"type": "string"},
                },
                "required": ["danisan_adi", "telefon", "tarih", "saat"],
            },
        }
    ]

    slot_filling_config = {
        "randevu_al": {
            "slots": ["danisan_adi", "telefon", "seans_turu", "tarih", "saat"],
            "sorular": {
                "danisan_adi": "Adınız soyadınız nedir?",
                "telefon": "Telefon numaranız?",
                "seans_turu": "Bireysel, çift veya aile seansı mı tercih edersiniz?",
                "tarih": "Hangi tarih uygun?",
                "saat": "Saat tercihiniz?",
            },
        }
    }
