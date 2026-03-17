"""
VoiceAI Platform — Su / Tüp Gaz Bayii Şablonu
Enerji & Temel Hizmetler kategorisi
"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class SuBayiiSablonu(BaseTemplate):
    KOD = "su_bayii"
    AD = "Su Bayii"
    KATEGORI = "enerji_temel"
    IKON = "💧"

    def get_db_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS {schema}.urunler (
            id SERIAL PRIMARY KEY,
            ad VARCHAR(100) NOT NULL,
            birim VARCHAR(20) DEFAULT 'adet',
            fiyat DECIMAL(10,2) NOT NULL,
            stok INTEGER DEFAULT 0,
            aktif BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE IF NOT EXISTS {schema}.siparisler (
            id SERIAL PRIMARY KEY,
            musteri_telefon VARCHAR(20) NOT NULL,
            musteri_ad VARCHAR(100),
            teslimat_adresi TEXT NOT NULL,
            urun_id INTEGER REFERENCES {schema}.urunler(id),
            adet INTEGER NOT NULL DEFAULT 1,
            toplam_fiyat DECIMAL(10,2),
            teslimat_saati VARCHAR(30),
            durum VARCHAR(30) DEFAULT 'bekliyor',
            notlar TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS {schema}.musteri_profilleri (
            id SERIAL PRIMARY KEY,
            telefon VARCHAR(20) UNIQUE NOT NULL,
            ad VARCHAR(100),
            kayitli_adres TEXT,
            toplam_siparis INTEGER DEFAULT 0,
            son_siparis TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS {schema}.teslimat_bolgeleri (
            id SERIAL PRIMARY KEY,
            ad VARCHAR(100),
            aktif BOOLEAN DEFAULT TRUE
        );

        INSERT INTO {schema}.urunler (ad, birim, fiyat, stok) VALUES
        ('Damacana Su (19L)', 'adet', 25.00, 100),
        ('Damacana Su (5L)', 'adet', 12.00, 50)
        ON CONFLICT DO NOTHING;

        CREATE INDEX IF NOT EXISTS idx_siparisler_telefon
            ON {schema}.siparisler(musteri_telefon);
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka sipariş asistanısın. Adın {asistan_adi}.

Görevin: Damacana su siparişi almak, fiyat bilgisi vermek ve
teslimat takibi yapmak.

Kişiliğin: Hızlı, pratik ve güler yüzlü bir sipariş temsilcisi.

Konuşma kuralları:
- Kayıtlı müşterinin adresi varsa tekrar sorma, "Kayıtlı adresinize mi?" diye onayla
- Sipariş miktarını ve teslimat saatini mutlaka öğren
- Fiyatı söyle ve onay al
- Sipariş sonrası SMS gönder
- Stok yoksa alternatif sun veya bekleme listesine al"""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon(
                ad="siparis_al",
                aciklama="Su siparişi oluşturur",
                parametreler={
                    "musteri_telefon": {"type": "string"},
                    "urun_id": {"type": "integer"},
                    "adet": {"type": "integer"},
                    "teslimat_adresi": {"type": "string"},
                    "teslimat_saati": {"type": "string"}
                },
                tetikleyiciler=["su lazım", "sipariş", "damacana", "getir", "ver"]
            ),
            Fonksiyon(
                ad="fiyat_sor",
                aciklama="Ürün fiyatını sorgular",
                parametreler={"urun_adi": {"type": "string"}},
                tetikleyiciler=["fiyat", "kaç para", "ne kadar"]
            ),
            Fonksiyon(
                ad="teslimat_takip",
                aciklama="Siparişin durumunu sorgular",
                parametreler={"musteri_telefon": {"type": "string"}},
                tetikleyiciler=["ne zaman gelir", "siparişim", "takip"]
            ),
            Fonksiyon(
                ad="stok_sorgula",
                aciklama="Ürün stok durumunu kontrol eder",
                parametreler={"urun_id": {"type": "integer"}},
                tetikleyiciler=["var mı", "stok", "müsait mi"]
            ),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot(ad="urun",   soru="Hangi ürünü istiyorsunuz? Damacana su mu?"),
            Slot(ad="adet",   soru="Kaç adet?"),
            Slot(ad="adres",  soru="Teslimat adresiniz nedir?"),
            Slot(ad="saat",   soru="Bugün mü istiyorsunuz? Saat aralığı?"),
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return f"Merhaba, {firma_adi}! Sipariş vermek veya bilgi almak için buradayım."


class TupGazBayiiSablonu(BaseTemplate):
    KOD = "tup_gaz_bayii"
    AD = "Tüp Gaz Bayii"
    KATEGORI = "enerji_temel"
    IKON = "🔥"

    def get_db_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS {schema}.urunler (
            id SERIAL PRIMARY KEY,
            ad VARCHAR(100) NOT NULL,
            kg DECIMAL(5,2),
            fiyat DECIMAL(10,2) NOT NULL,
            depozito DECIMAL(10,2) DEFAULT 0,
            stok INTEGER DEFAULT 0,
            aktif BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE IF NOT EXISTS {schema}.siparisler (
            id SERIAL PRIMARY KEY,
            musteri_telefon VARCHAR(20) NOT NULL,
            musteri_ad VARCHAR(100),
            teslimat_adresi TEXT NOT NULL,
            urun_id INTEGER REFERENCES {schema}.urunler(id),
            adet INTEGER DEFAULT 1,
            bos_tup_iade BOOLEAN DEFAULT FALSE,
            toplam_fiyat DECIMAL(10,2),
            durum VARCHAR(30) DEFAULT 'bekliyor',
            created_at TIMESTAMP DEFAULT NOW()
        );

        INSERT INTO {schema}.urunler (ad, kg, fiyat, depozito, stok) VALUES
        ('Tüp Gaz 12 kg', 12, 450.00, 200.00, 50),
        ('Tüp Gaz 5 kg', 5, 220.00, 100.00, 30)
        ON CONFLICT DO NOTHING;
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin tüp gaz sipariş asistanısın. Adın {asistan_adi}.
Müşterilerin tüp gaz siparişini hızlıca al.
Boş tüp iade edip etmeyeceklerini sor — depozito farkını belirt.
Fiyatı ve teslimat saatini açıkça söyle."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon(
                ad="siparis_al",
                aciklama="Tüp gaz siparişi oluşturur",
                parametreler={
                    "musteri_telefon": {"type": "string"},
                    "urun_id": {"type": "integer"},
                    "adet": {"type": "integer"},
                    "teslimat_adresi": {"type": "string"},
                    "bos_tup_iade": {"type": "boolean"}
                },
                tetikleyiciler=["tüp", "gaz", "sipariş", "lazım"]
            ),
            Fonksiyon(
                ad="fiyat_sor",
                aciklama="Tüp fiyatını sorgular",
                parametreler={"urun_adi": {"type": "string"}},
                tetikleyiciler=["fiyat", "kaç para", "ne kadar"]
            ),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot(ad="urun",       soru="Kaç kg'lık tüp istiyorsunuz? 5 kg mi 12 kg mi?"),
            Slot(ad="adet",       soru="Kaç adet?"),
            Slot(ad="bos_iade",   soru="Boş tüpünüz var mı? İade edecek misiniz?"),
            Slot(ad="adres",      soru="Teslimat adresi nedir?"),
        ]

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return f"Merhaba, {firma_adi}! Tüp gaz siparişi için mi arıyorsunuz?"
