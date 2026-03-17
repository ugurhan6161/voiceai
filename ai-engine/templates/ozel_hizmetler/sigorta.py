"""VoiceAI — Sigorta Acentesi Şablonu"""
from ..base_template import BaseTemplate
class SigortaTemplate(BaseTemplate):
    template_id = "sigorta"
    template_adi = "Sigorta Acentesi"
    sektor = "ozel_hizmetler"
    aciklama = "Sigorta acentesi için teklif ve bilgi asistanı"
    sistem_prompt_tr = """Sen {firma_adi} sigorta acentesinin sesli asistanısın.
Görevlerin: sigorta teklifi almak, ürünler hakkında bilgi vermek, randevu ayarlamak.
Teklif için: ad, telefon, sigorta türü, araç/mülk bilgisi."""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Sigorta hizmetleri için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"teklif_al","description":"Sigorta teklifi oluştur","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"sigorta_turu":{"type":"string"},"detay":{"type":"string"}},"required":["musteri_adi","telefon","sigorta_turu"]}}]
    slot_filling_config = {"teklif_al":{"slots":["musteri_adi","telefon","sigorta_turu"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","sigorta_turu":"Hangi sigorta türü? (kasko, konut, sağlık, hayat vb.)"}}}
