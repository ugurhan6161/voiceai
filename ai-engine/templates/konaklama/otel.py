"""VoiceAI — Otel Şablonu"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class OtelSablonu(BaseTemplate):
    KOD = "otel"; AD = "Otel"; KATEGORI = "konaklama"; IKON = "🏨"

    def get_db_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS {schema}.odalar (
            id SERIAL PRIMARY KEY, oda_no VARCHAR(10) UNIQUE NOT NULL,
            tip VARCHAR(50) NOT NULL, kapasite INTEGER NOT NULL,
            fiyat DECIMAL(10,2) NOT NULL, ozellikler JSONB, aktif BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS {schema}.rezervasyonlar (
            id SERIAL PRIMARY KEY, musteri_ad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20) NOT NULL, email VARCHAR(100),
            tarih DATE NOT NULL, saat TIME, kisi_sayisi INTEGER NOT NULL,
            oda_id INTEGER REFERENCES {schema}.odalar(id), sure INTEGER,
            durum VARCHAR(20) DEFAULT 'onaylandi', notlar TEXT,
            sms_gonderildi BOOLEAN DEFAULT FALSE,
            olusturma_zamani TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS {schema}.ayarlar (
            id SERIAL PRIMARY KEY, fiyat_listesi JSONB,
            calisma_saatleri JSONB, aktif BOOLEAN DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_rez_telefon ON {schema}.rezervasyonlar(telefon);
        CREATE INDEX IF NOT EXISTS idx_rez_tarih ON {schema}.rezervasyonlar(tarih);
        INSERT INTO {schema}.odalar (oda_no, tip, kapasite, fiyat) VALUES
        ('101','tek',1,500.00),('102','cift',2,800.00),('201','suit',4,1500.00)
        ON CONFLICT DO NOTHING;
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka resepsiyonistisin. Adın {asistan_adi}.
Görevin: Oda rezervasyonu almak, müsaitlik kontrolü yapmak, fiyat bilgisi vermek.
Kişiliğin: Nazik, profesyonel, misafirperver. "Hoş geldiniz", "Tabii efendim" kullan.
Rezervasyon için: tarih, gece sayısı, kişi sayısı, oda tipi bilgilerini al.
Fiyatları TL olarak belirt. İşlem sonunda SMS onayı gönder."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon("rezervasyon_yap", "Oda rezervasyonu oluşturur",
                {"musteri_ad": {"type": "string"}, "telefon": {"type": "string"},
                 "tarih": {"type": "string"}, "sure": {"type": "integer"},
                 "kisi_sayisi": {"type": "integer"}, "oda_tipi": {"type": "string"}},
                ["rezervasyon", "oda", "konaklama", "yer ayırt"]),
            Fonksiyon("musaitlik_kontrol", "Belirtilen tarihte müsait odaları listeler",
                {"tarih": {"type": "string"}, "kisi_sayisi": {"type": "integer"}},
                ["müsait", "boş oda", "var mı"]),
            Fonksiyon("rezervasyon_iptal", "Rezervasyonu iptal eder",
                {"telefon": {"type": "string"}},
                ["iptal", "vazgeçtim"]),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot("tarih", "Hangi tarihte gelmek istiyorsunuz?"),
            Slot("sure", "Kaç gece konaklayacaksınız?"),
            Slot("kisi_sayisi", "Kaç kişisiniz?"),
            Slot("oda_tipi", "Tek kişilik mi, çift kişilik mi tercih edersiniz?"),
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return f"Merhaba, {firma_adi}'e hoş geldiniz. Rezervasyon veya bilgi için yardımcı olabilirim."
