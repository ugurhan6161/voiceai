"""VoiceAI — Nakliyat Şablonu"""
from ..base_template import BaseTemplate
class NakliyatTemplate(BaseTemplate):
    template_id = "nakliyat"
    template_adi = "Nakliyat / Taşımacılık"
    sektor = "ozel_hizmetler"
    aciklama = "Nakliyat firması için teklif ve sipariş asistanı"
    sistem_prompt_tr = """Sen {firma_adi} nakliyat firmasının sesli asistanısın.
Görevlerin: taşıma teklifi almak, fiyat bilgisi vermek.
Teklif için: ad, telefon, mevcut adres, yeni adres, taşıma tarihi, eşya bilgisi."""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Taşıma hizmeti için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"teklif_al","description":"Nakliyat teklifi oluştur","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"mevcut_adres":{"type":"string"},"yeni_adres":{"type":"string"},"tasima_tarihi":{"type":"string"},"esya_bilgisi":{"type":"string"}},"required":["musteri_adi","telefon","mevcut_adres","yeni_adres","tasima_tarihi"]}}]
    slot_filling_config = {"teklif_al":{"slots":["musteri_adi","telefon","mevcut_adres","yeni_adres","tasima_tarihi"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","mevcut_adres":"Taşınacağınız mevcut adres?","yeni_adres":"Yeni adresiniz?","tasima_tarihi":"Taşıma tarihi?"}}}
