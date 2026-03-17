"""VoiceAI — Kuru Temizleme Şablonu"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class KuruTemizlemeSablonu(BaseTemplate):
    KOD = "kurutemizleme"; AD = "Kuru Temizleme"; KATEGORI = "ev_hizmetleri"; IKON = "👔"

    def get_db_schema(self) -> str:
        return """

        CREATE TABLE IF NOT EXISTS {{schema}}.urunler (
            id SERIAL PRIMARY KEY, ad VARCHAR(100) NOT NULL,
            fiyat DECIMAL(10,2) NOT NULL, stok INTEGER DEFAULT 0, aktif BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS {{schema}}.siparisler (
            id SERIAL PRIMARY KEY, musteri_ad VARCHAR(100),
            telefon VARCHAR(20) NOT NULL, teslimat_adresi TEXT,
            urun_id INTEGER REFERENCES {{schema}}.urunler(id),
            adet INTEGER DEFAULT 1, toplam_fiyat DECIMAL(10,2),
            durum VARCHAR(30) DEFAULT 'bekliyor', sms_gonderildi BOOLEAN DEFAULT FALSE,
            olusturma_zamani TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS {{schema}}.musteri_profilleri (
            id SERIAL PRIMARY KEY, telefon VARCHAR(20) UNIQUE NOT NULL,
            ad VARCHAR(100), kayitli_adres TEXT
        );
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka asistanısın. Adın {asistan_adi}.
Kuru temizleme siparişi alır.
Müşteriye yardımcı ol, gerekli bilgileri al ve işlemi tamamla.
İşlem sonunda SMS onayı gönder."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon("randevu_al", "Randevu veya sipariş oluşturur",
                {"musteri_ad": {"type": "string"}, "telefon": {"type": "string"},
                 "tarih": {"type": "string"}, "saat": {"type": "string"}},
                ['sipariş', 'temizleme', 'kıyafet', 'teslim']),
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
