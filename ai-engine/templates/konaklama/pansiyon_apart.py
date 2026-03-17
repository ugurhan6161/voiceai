"""VoiceAI — Pansiyon / Apart Şablonu"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class PansiyonApartSablonu(BaseTemplate):
    KOD = "pansiyon_apart"; AD = "Pansiyon / Apart"; KATEGORI = "konaklama"; IKON = "🏠"

    def get_db_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS {schema}.odalar (
            id SERIAL PRIMARY KEY, oda_no VARCHAR(10) UNIQUE NOT NULL,
            tip VARCHAR(50) NOT NULL, kapasite INTEGER NOT NULL,
            fiyat DECIMAL(10,2) NOT NULL, aktif BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS {schema}.rezervasyonlar (
            id SERIAL PRIMARY KEY, musteri_ad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20) NOT NULL, tarih DATE NOT NULL,
            sure INTEGER NOT NULL, kisi_sayisi INTEGER NOT NULL,
            oda_id INTEGER REFERENCES {schema}.odalar(id),
            durum VARCHAR(20) DEFAULT 'onaylandi', notlar TEXT,
            sms_gonderildi BOOLEAN DEFAULT FALSE,
            olusturma_zamani TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS {schema}.ayarlar (
            id SERIAL PRIMARY KEY, fiyat_listesi JSONB, calisma_saatleri JSONB, aktif BOOLEAN DEFAULT TRUE
        );
        INSERT INTO {schema}.odalar (oda_no, tip, kapasite, fiyat) VALUES
        ('1','standart',2,400.00),('2','aile',4,700.00),('3','apart',4,900.00)
        ON CONFLICT DO NOTHING;
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka asistanısın. Adın {asistan_adi}.
Pansiyon ve apart daire rezervasyonu alıyorsun. Tarih, süre, kişi sayısı bilgilerini al.
Günlük ve haftalık fiyatları belirt. Kahvaltı dahil mi sorusunu yanıtla."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon("rezervasyon_yap", "Rezervasyon oluşturur",
                {"musteri_ad": {"type": "string"}, "telefon": {"type": "string"},
                 "tarih": {"type": "string"}, "sure": {"type": "integer"}, "kisi_sayisi": {"type": "integer"}},
                ["rezervasyon", "yer", "konaklama"]),
            Fonksiyon("musaitlik_kontrol", "Müsait odaları listeler",
                {"tarih": {"type": "string"}}, ["müsait", "boş", "var mı"]),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot("tarih", "Hangi tarihte gelmek istiyorsunuz?"),
            Slot("sure", "Kaç gece kalacaksınız?"),
            Slot("kisi_sayisi", "Kaç kişisiniz?"),
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return f"Merhaba, {firma_adi}! Rezervasyon için yardımcı olabilirim."
