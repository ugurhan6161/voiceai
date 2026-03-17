"""VoiceAI — Güzellik Salonu Şablonu"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class GuzellikSalonuSablonu(BaseTemplate):
    KOD = "guzelliksalonu"; AD = "Güzellik Salonu"; KATEGORI = "kisisel_bakim"; IKON = "💅"

    def get_db_schema(self) -> str:
        return """

        CREATE TABLE IF NOT EXISTS {{schema}}.randevular (
            id SERIAL PRIMARY KEY, musteri_ad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20) NOT NULL, tarih DATE NOT NULL, saat TIME NOT NULL,
            hizmet VARCHAR(100), durum VARCHAR(20) DEFAULT 'onaylandi',
            notlar TEXT, sms_gonderildi BOOLEAN DEFAULT FALSE,
            olusturma_zamani TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS {{schema}}.hizmetler (
            id SERIAL PRIMARY KEY, ad VARCHAR(100) NOT NULL,
            sure_dakika INTEGER DEFAULT 60, fiyat DECIMAL(10,2), aktif BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS {{schema}}.ayarlar (
            id SERIAL PRIMARY KEY, calisma_saatleri JSONB, aktif BOOLEAN DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_randevu_telefon ON {{schema}}.randevular(telefon);
        CREATE INDEX IF NOT EXISTS idx_randevu_tarih ON {{schema}}.randevular(tarih);
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka asistanısın. Adın {asistan_adi}.
Güzellik salonu randevusu alır.
Müşteriye yardımcı ol, gerekli bilgileri al ve işlemi tamamla.
İşlem sonunda SMS onayı gönder."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon("randevu_al", "Randevu veya sipariş oluşturur",
                {"musteri_ad": {"type": "string"}, "telefon": {"type": "string"},
                 "tarih": {"type": "string"}, "saat": {"type": "string"}},
                ['randevu', 'manikür', 'pedikür', 'güzellik']),
            Fonksiyon("bilgi_ver", "Hizmet ve fiyat bilgisi verir",
                {"konu": {"type": "string"}},
                ["fiyat", "bilgi", "ne kadar", "nasıl"]),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot("ad", "Adınız nedir?"),
            Slot("tarih", "Hangi tarih için?"),
            Slot("saat", "Saat kaçta?"),
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return f"Merhaba, {firma_adi}! Size nasıl yardımcı olabilirim?"
