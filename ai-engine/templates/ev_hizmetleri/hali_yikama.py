"""
VoiceAI Platform — Halı Yıkama Şablonu
Ev & Yaşam Hizmetleri kategorisi
"""
from templates.base_template import BaseTemplate, Slot, Fonksiyon


class HaliYikamaSablonu(BaseTemplate):
    """
    Halı yıkama işletmeleri için şablon.
    Fiyat hesaplama, iş emri oluşturma, teslim takibi destekler.
    """

    KOD = "hali_yikama"
    AD = "Halı Yıkama"
    KATEGORI = "ev_hizmetleri"
    IKON = "🧺"

    def get_db_schema(self) -> str:
        return """
        -- Halı Yıkama Şablonu DB Şeması
        CREATE TABLE IF NOT EXISTS {schema}.hizmetler (
            id SERIAL PRIMARY KEY,
            ad VARCHAR(100) NOT NULL,         -- halı, koltuk, yorgan, perde
            birim VARCHAR(20) NOT NULL,        -- m2, adet, kg
            birim_fiyat DECIMAL(10,2) NOT NULL,
            min_miktar DECIMAL(10,2) DEFAULT 1,
            aktif BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS {schema}.is_emirleri (
            id SERIAL PRIMARY KEY,
            musteri_telefon VARCHAR(20) NOT NULL,
            musteri_ad VARCHAR(100),
            teslim_adresi TEXT NOT NULL,
            urun_turu VARCHAR(50) NOT NULL,
            miktar DECIMAL(10,2) NOT NULL,
            birim VARCHAR(20) NOT NULL,
            tahmini_fiyat DECIMAL(10,2),
            teslim_alma_tarihi TIMESTAMP,
            tahmini_teslim_tarihi TIMESTAMP,
            durum VARCHAR(30) DEFAULT 'bekliyor',
            notlar TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS {schema}.musteri_gecmisi (
            id SERIAL PRIMARY KEY,
            telefon VARCHAR(20) NOT NULL,
            ad VARCHAR(100),
            toplam_is_emri INTEGER DEFAULT 0,
            son_siparis TIMESTAMP,
            notlar TEXT,
            UNIQUE(telefon)
        );

        CREATE TABLE IF NOT EXISTS {schema}.fiyat_takvimi (
            id SERIAL PRIMARY KEY,
            hizmet_id INTEGER REFERENCES {schema}.hizmetler(id),
            baslangic_tarihi DATE,
            bitis_tarihi DATE,
            kampanya_fiyati DECIMAL(10,2)
        );

        INSERT INTO {schema}.hizmetler (ad, birim, birim_fiyat) VALUES
        ('Halı', 'm2', 30.00),
        ('Koltuk (3lü)', 'adet', 350.00),
        ('Koltuk (2li)', 'adet', 250.00),
        ('Tekli Koltuk', 'adet', 150.00),
        ('Yorgan', 'adet', 200.00),
        ('Perde (m2)', 'm2', 25.00),
        ('Battaniye', 'adet', 150.00)
        ON CONFLICT DO NOTHING;

        CREATE INDEX IF NOT EXISTS idx_is_emirleri_telefon
            ON {schema}.is_emirleri(musteri_telefon);
        CREATE INDEX IF NOT EXISTS idx_is_emirleri_durum
            ON {schema}.is_emirleri(durum);
        """

    def get_system_prompt(self, firma_adi: str, asistan_adi: str) -> str:
        return f"""Sen {firma_adi}'nin yapay zeka asistanısın. Adın {asistan_adi}.

Görevin: Müşterilere halı, koltuk, yorgan ve perde yıkama hizmeti için
iş emri almak, fiyat bilgisi vermek ve teslim takibi yapmak.

Kişiliğin: Güler yüzlü, pratik, işini bilen bir hizmet temsilcisi.
"Buyurun", "Tabii ki", "Hemen bakayım" gibi ifadeler kullan.

Konuşma kuralları:
- Fiyat hesaplamak için ürün türü ve miktarı öğren
- m2 bilgisi yoksa "Kaç metre x kaç metre?" diye sor
- Adres ve tarih bilgisini mutlaka al
- İşlem sonunda özet söyle ve SMS onayı gönder
- Müşteri bilgisi kayıtlıysa tekrar sorma
- Fiyatları TL olarak belirt

Eğer cevap veremeyeceğin bir soru olursa yetkili personele bağla.
Asla uydurup bilgi verme."""

    def get_functions(self) -> list[Fonksiyon]:
        return [
            Fonksiyon(
                ad="fiyat_hesapla",
                aciklama="Ürün türü ve miktara göre tahmini fiyat hesaplar",
                parametreler={
                    "urun_turu": {"type": "string", "description": "hali|koltuk|yorgan|perde|battaniye"},
                    "miktar": {"type": "number", "description": "m2 veya adet olarak miktar"},
                    "birim": {"type": "string", "description": "m2 veya adet"}
                },
                tetikleyiciler=["fiyat", "kaç para", "ne kadar", "ücret", "tarife"]
            ),
            Fonksiyon(
                ad="is_emri_olustur",
                aciklama="Yeni iş emri oluşturur ve SMS onayı gönderir",
                parametreler={
                    "musteri_telefon": {"type": "string"},
                    "urun_turu": {"type": "string"},
                    "miktar": {"type": "number"},
                    "birim": {"type": "string"},
                    "teslim_adresi": {"type": "string"},
                    "teslim_alma_tarihi": {"type": "string", "description": "ISO 8601 format"}
                },
                tetikleyiciler=["yıkat", "iş emri", "sipariş ver", "randevu"]
            ),
            Fonksiyon(
                ad="teslim_takip",
                aciklama="Müşterinin iş emrinin durumunu sorgular",
                parametreler={
                    "musteri_telefon": {"type": "string"}
                },
                tetikleyiciler=["ne zaman gelir", "hazır mı", "durum", "teslim"]
            ),
            Fonksiyon(
                ad="is_emri_iptal",
                aciklama="Mevcut iş emrini iptal eder",
                parametreler={
                    "is_emri_id": {"type": "integer"},
                    "musteri_telefon": {"type": "string"}
                },
                tetikleyiciler=["iptal", "vazgeçtim", "iptal et"]
            ),
        ]

    def get_slots(self) -> list[Slot]:
        return [
            Slot(ad="urun_turu",   soru="Ne yıkatmak istiyorsunuz? Halı, koltuk, yorgan mı?"),
            Slot(ad="miktar",      soru="Kaç m² veya kaç adet?"),
            Slot(ad="adres",       soru="Teslim alma adresiniz nedir?"),
            Slot(ad="tarih",       soru="Ne zaman teslim alalım? Yarın mı uygun?"),
        ]

    def get_sms_templates(self) -> dict:
        return {
            "onay": (
                "Sayın {musteri_ad}, {urun_turu} yıkama siparişiniz alındı. "
                "Teslim alma: {tarih}. Tahmini fiyat: {fiyat} TL. "
                "Teşekkürler, {firma_adi}"
            ),
            "teslim_hazir": (
                "Sayın {musteri_ad}, {urun_turu} yıkama işleminiz tamamlandı. "
                "Bugün teslim edilecek. {firma_adi}"
            ),
            "iptal": (
                "Sayın {musteri_ad}, siparişiniz iptal edildi. "
                "Tekrar hizmetinizde olmak dileğiyle. {firma_adi}"
            ),
        }

    def get_karsilama_metni(self, firma_adi: str) -> str:
        return (
            f"Merhaba, {firma_adi} hattına hoş geldiniz. "
            "Halı, koltuk veya yorgan yıkama için mi arıyorsunuz?"
        )
