"""VoiceAI — Kamp / Bungalov Şablonu"""
from ..base_template import BaseTemplate
class KampBungalovTemplate(BaseTemplate):
    template_id = "kamp_bungalov"
    template_adi = "Kamp / Bungalov"
    sektor = "konaklama"
    aciklama = "Kamp alanı ve bungalov için rezervasyon asistanı"
    sistem_prompt_tr = """Sen {firma_adi} kamp alanının sesli asistanisın.
Görevlerin: bungalov/kamp yeri rezervasyonu almak, fiyat ve müsaitlik bilgisi vermek.
Rezervasyon için: ad, telefon, giriş/çıkış tarihi, kişi sayısı, konaklama türü."""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Rezervasyon için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"rezervasyon_al","description":"Kamp/bungalov rezervasyonu","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"giris_tarihi":{"type":"string"},"cikis_tarihi":{"type":"string"},"kisi_sayisi":{"type":"integer"},"konaklama_turu":{"type":"string"}},"required":["musteri_adi","telefon","giris_tarihi","cikis_tarihi","kisi_sayisi"]}}]
    slot_filling_config = {"rezervasyon_al":{"slots":["musteri_adi","telefon","giris_tarihi","cikis_tarihi","kisi_sayisi"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","giris_tarihi":"Giriş tarihi?","cikis_tarihi":"Çıkış tarihi?","kisi_sayisi":"Kaç kişilik?"}}}
