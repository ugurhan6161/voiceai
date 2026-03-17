"""VoiceAI — Kafe Şablonu"""
from ..base_template import BaseTemplate
class KafeTemplate(BaseTemplate):
    template_id = "kafe"
    template_adi = "Kafe"
    sektor = "yiyecek_icecek"
    aciklama = "Kafe için rezervasyon asistanı"
    sistem_prompt_tr = "Sen {firma_adi} kafesinin sesli asistanisın. Masa rezervasyonu ve bilgi ver."
    karsilama_tr = "Merhaba, {firma_adi} Kafe. Nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"rezervasyon_al","description":"Kafe masa rezervasyonu","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"kisi_sayisi":{"type":"integer"},"tarih":{"type":"string"},"saat":{"type":"string"}},"required":["musteri_adi","telefon","kisi_sayisi","tarih","saat"]}}]
    slot_filling_config = {"rezervasyon_al":{"slots":["musteri_adi","telefon","kisi_sayisi","tarih","saat"],"sorular":{"musteri_adi":"Adınız?","telefon":"Telefon?","kisi_sayisi":"Kaç kişilik?","tarih":"Tarih?","saat":"Saat?"}}}
