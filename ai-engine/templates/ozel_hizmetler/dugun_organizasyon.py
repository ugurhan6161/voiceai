"""VoiceAI — Düğün / Organizasyon Şablonu"""
from ..base_template import BaseTemplate

class DugunOrganizasyonTemplate(BaseTemplate):
    template_id = "dugun_organizasyon"
    template_adi = "Düğün / Organizasyon"
    sektor = "ozel_hizmetler"
    aciklama = "Düğün ve özel etkinlik organizasyonu için asistan"

    sistem_prompt_tr = """Sen {firma_adi} organizasyon firmasının sesli asistanısın.
Görevlerin: etkinlik teklifi almak, paketler hakkında bilgi vermek, randevu ayarlamak.
Teklif için: etkinlik türü, tarih, kişi sayısı, mekan tercihi, bütçe, iletişim bilgileri.
"""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Özel gününüz için nasıl yardımcı olabilirim?"

    fonksiyonlar = [
        {
            "name": "teklif_al",
            "description": "Organizasyon teklifi oluştur",
            "parameters": {
                "type": "object",
                "properties": {
                    "musteri_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "etkinlik_turu": {"type": "string", "description": "Düğün, nişan, doğum günü vb."},
                    "tarih": {"type": "string"},
                    "kisi_sayisi": {"type": "integer"},
                    "butce": {"type": "string"},
                    "notlar": {"type": "string"},
                },
                "required": ["musteri_adi", "telefon", "etkinlik_turu", "tarih", "kisi_sayisi"],
            },
        },
        {
            "name": "randevu_al",
            "description": "Görüşme randevusu ayarla",
            "parameters": {
                "type": "object",
                "properties": {
                    "musteri_adi": {"type": "string"},
                    "telefon": {"type": "string"},
                    "tarih": {"type": "string"},
                    "saat": {"type": "string"},
                },
                "required": ["musteri_adi", "telefon", "tarih", "saat"],
            },
        },
    ]

    slot_filling_config = {
        "teklif_al": {
            "slots": ["musteri_adi", "telefon", "etkinlik_turu", "tarih", "kisi_sayisi"],
            "sorular": {
                "musteri_adi": "Adınız soyadınız?",
                "telefon": "Telefon numaranız?",
                "etkinlik_turu": "Hangi tür etkinlik planlıyorsunuz?",
                "tarih": "Etkinlik tarihi?",
                "kisi_sayisi": "Kaç kişilik?",
            },
        }
    }
