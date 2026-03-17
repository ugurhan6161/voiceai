"""VoiceAI — Temizlik Şirketi Şablonu"""
from ..base_template import BaseTemplate
class TemizlikSirketiTemplate(BaseTemplate):
    template_id = "temizlik_sirketi"
    template_adi = "Temizlik Şirketi"
    sektor = "ozel_hizmetler"
    aciklama = "Profesyonel temizlik şirketi için sipariş asistanı"
    sistem_prompt_tr = """Sen {firma_adi} temizlik şirketinin sesli asistanısın.
Görevlerin: temizlik hizmeti siparişi almak, fiyat bilgisi vermek.
Sipariş için: ad, telefon, adres, hizmet türü, tarih/saat, metrekare."""
    karsilama_tr = "Merhaba, {firma_adi}'ne hoş geldiniz. Temizlik hizmeti için nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"siparis_al","description":"Temizlik hizmeti siparişi","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"adres":{"type":"string"},"hizmet_turu":{"type":"string"},"tarih":{"type":"string"},"saat":{"type":"string"},"metrekare":{"type":"integer"}},"required":["musteri_adi","telefon","adres","hizmet_turu","tarih","saat"]}}]
    slot_filling_config = {"siparis_al":{"slots":["musteri_adi","telefon","adres","hizmet_turu","tarih","saat"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","adres":"Temizlik yapılacak adres?","hizmet_turu":"Hangi hizmet? (ev, ofis, inşaat sonrası vb.)","tarih":"Hangi tarih?","saat":"Saat tercihiniz?"}}}
