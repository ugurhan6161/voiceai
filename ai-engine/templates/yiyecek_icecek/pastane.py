"""VoiceAI — Pastane Şablonu"""
from ..base_template import BaseTemplate
class PastaneTemplate(BaseTemplate):
    template_id = "pastane"
    template_adi = "Pastane / Fırın"
    sektor = "yiyecek_icecek"
    aciklama = "Pastane için sipariş asistanı"
    sistem_prompt_tr = "Sen {firma_adi} pastanesi/firınının sesli asistanisın. Özel sipariş al."
    karsilama_tr = "Merhaba, {firma_adi} Pastane. Nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"siparis_al","description":"Özel sipariş","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"urun_turu":{"type":"string"},"teslim_tarihi":{"type":"string"},"ozel_not":{"type":"string"}},"required":["musteri_adi","telefon","urun_turu","teslim_tarihi"]}}]
    slot_filling_config = {"siparis_al":{"slots":["musteri_adi","telefon","urun_turu","teslim_tarihi"],"sorular":{"musteri_adi":"Adınız?","telefon":"Telefon?","urun_turu":"Ne sipariş etmek istiyorsunuz?","teslim_tarihi":"Teslim tarihi?"}}}
