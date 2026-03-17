"""VoiceAI — Fotoğrafçı Şablonu"""
from ..base_template import BaseTemplate
class FotografciTemplate(BaseTemplate):
    template_id = "fotografci"
    template_adi = "Fotoğrafçı / Stüdyo"
    sektor = "ozel_hizmetler"
    aciklama = "Fotoğraf stüdyosu için randevu asistanı"
    sistem_prompt_tr = """Sen {firma_adi} fotoğraf stüdyosunun sesli asistanısın.
Görevlerin: çekim randevusu almak, paketler hakkında bilgi vermek.
Randevu için: ad, telefon, çekim türü, tarih/saat."""
    karsilama_tr = "Merhaba, {firma_adi} Fotoğraf Stüdyosu'na hoş geldiniz. Nasıl yardımcı olabilirim?"
    fonksiyonlar = [{"name":"randevu_al","description":"Fotoğraf çekimi randevusu","parameters":{"type":"object","properties":{"musteri_adi":{"type":"string"},"telefon":{"type":"string"},"cekim_turu":{"type":"string"},"tarih":{"type":"string"},"saat":{"type":"string"}},"required":["musteri_adi","telefon","cekim_turu","tarih","saat"]}}]
    slot_filling_config = {"randevu_al":{"slots":["musteri_adi","telefon","cekim_turu","tarih","saat"],"sorular":{"musteri_adi":"Adınız soyadınız?","telefon":"Telefon numaranız?","cekim_turu":"Hangi tür çekim istiyorsunuz? (düğün, bebek, kurumsal vb.)","tarih":"Hangi tarih?","saat":"Saat tercihiniz?"}}}
