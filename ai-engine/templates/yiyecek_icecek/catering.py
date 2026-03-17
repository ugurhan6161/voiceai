"""VoiceAI — Catering Şablonu"""
from ..base_template import BaseTemplate
class CateringTemplate(BaseTemplate):
    template_id = "catering"
    template_adi = "Catering"
    sektor = "yiyecek_icecek"
    aciklama = "Catering firması için teklif asistanı"
    sistem_prompt_tr = "Sen {firma_adi} catering firmasının sesli asistanisın. Etkinlik için yemek teklifi al."
    karsilama_tr = "Merhaba, {firma_adi} Catering. Etkinliğiniz için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"teklif_al","description":"Catering teklifi","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"etkinlik_turu":{"type":"string"},"tarih":{"type":"string"},"kisi_sayisi":{"type":"integer"}},"required":["musteri_adi","telefon","etkinlik_turu","tarih","kisi_sayisi"]}}]
    slot_filling_config = {"teklif_al":{"slots":["musteri_adi","telefon","etkinlik_turu","tarih","kisi_sayisi"],"sorular":{"musteri_adi":"Adınız?","telefon":"Telefon?","etkinlik_turu":"Etkinlik türü?","tarih":"Tarih?","kisi_sayisi":"Kaç kişilik?"}}}
