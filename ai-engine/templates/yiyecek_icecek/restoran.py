"""VoiceAI — Restoran Şablonu"""
from ..base_template import BaseTemplate
class RestoranTemplate(BaseTemplate):
    template_id = "restoran"
    template_adi = "Restoran"
    sektor = "yiyecek_icecek"
    aciklama = "Restoran için rezervasyon ve sipariş asistanı"
    sistem_prompt_tr = """Sen {firma_adi} restoraninin sesli asistanisın.
Görevlerin: masa rezervasyonu almak, menü bilgisi vermek, paket sipariş almak.
Rezervasyon için: ad, telefon, kişi sayısı, tarih/saat."""
    karsilama_tr = "Merhaba, {firma_adi} Restoran. Rezervasyon veya sipariş için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"rezervasyon_al","description":"Masa rezervasyonu","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"kisi_sayisi":{"type":"integer"},"tarih":{"type":"string"},"saat":{"type":"string"},"ozel_istek":{"type":"string"}},"required":["musteri_adi","telefon","kisi_sayisi","tarih","saat"]}},{"name":"paket_siparis","description":"Paket sipariş","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"adres":{"type":"string"},"siparis":{"type":"string"}},"required":["musteri_adi","telefon","adres","siparis"]}}]
    slot_filling_config = {"rezervasyon_al":{"slots":["musteri_adi","telefon","kisi_sayisi","tarih","saat"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","kisi_sayisi":"Kaç kişilik rezervasyon?","tarih":"Hangi tarih?","saat":"Saat tercihiniz?"}}}
