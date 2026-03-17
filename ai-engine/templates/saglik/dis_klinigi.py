"""VoiceAI — Diş Kliniği Şablonu"""
from ..base_template import BaseTemplate

class DisKlinigiTemplate(BaseTemplate):
    template_id = "dis_klinigi"
    template_adi = "Diş Kliniği"
    sektor = "saglik"
    aciklama = "Diş kliniği için randevu ve bilgi asistanı"

    sistem_prompt_tr = """Sen {firma_adi} diş kliniğinin sesli resepsiyonistisin.
Görevlerin: randevu almak, tedaviler hakkında bilgi vermek, fiyat bilgisi vermek.
Randevu için: ad soyad, telefon, tedavi türü, tarih/saat bilgilerini al.
Acil diş ağrısı için: "En kısa sürede sizi randevuya alalım, acil durumda kliniğimize gelin."
"""
    karsilama_tr = "Merhaba, {firma_adi} Diş Kliniği'ne hoş geldiniz. Nasıl yardımcı olabilirim?"

    fonksiyonlar = [
        {
            "name": "randevu_al",
            "description": "Diş kliniği randevusu oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "hasta_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "tedavi_turu": {"type": "string", "description": "Muayene, dolgu, kanal, implant vb."},
                    "tarih": {"type": "string"},
                    "saat": {"type": "string"},
                },
                "required": ["hasta_adi", "telefon", "tarih", "saat"],
            },
        }
    ]

    slot_filling_config = {
        "randevu_al": {
            "slots": ["hasta_adi", "telefon", "tedavi_turu", "tarih", "saat"],
            "sorular": {
                "hasta_adi": "Adınız soyadınız nedir?",
                "telefon": "Telefon numaranızı alabilir miyim?",
                "tedavi_turu": "Hangi tedavi için randevu almak istiyorsunuz? (muayene, dolgu, kanal vb.)",
                "tarih": "Hangi tarih uygun?",
                "saat": "Saat tercihiniz?",
            },
        }
    }
