-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Veritabanı İlk Şema
--  Otomatik çalışır: docker-compose up ilk çalıştırıldığında
-- ─────────────────────────────────────────────────────────────

-- Ortak schema
CREATE SCHEMA IF NOT EXISTS shared;

-- ── PAKETLER ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.paketler (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    fiyat DECIMAL(10,2) NOT NULL,
    cagri_limiti INTEGER NOT NULL DEFAULT 500,
    sms_limiti INTEGER NOT NULL DEFAULT 500,
    ajan_sayisi INTEGER NOT NULL DEFAULT 1,
    depolama_gb DECIMAL(5,2) NOT NULL DEFAULT 1.0,
    ses_klonlama BOOLEAN DEFAULT FALSE,
    whatsapp BOOLEAN DEFAULT FALSE,
    white_label BOOLEAN DEFAULT FALSE,
    fazla_cagri_fiyat DECIMAL(6,4) DEFAULT 0.60,
    fazla_sms_fiyat DECIMAL(6,4) DEFAULT 0.30,
    gizli BOOLEAN DEFAULT FALSE,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Başlangıç paketleri
INSERT INTO shared.paketler (ad, fiyat, cagri_limiti, sms_limiti, ajan_sayisi) VALUES
('Başlangıç', 990.00, 500, 500, 1),
('Pro', 2490.00, 2000, 1000, 3),
('Pro Plus', 3490.00, 3000, 2000, 5)
ON CONFLICT DO NOTHING;

-- ── FİRMALAR ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.firmalar (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(200) NOT NULL,
    sektor VARCHAR(50) NOT NULL,  -- otel, klinik, kuafor, restoran, diger
    schema_adi VARCHAR(50) UNIQUE NOT NULL,
    paket_id INTEGER REFERENCES shared.paketler(id),
    durum VARCHAR(20) DEFAULT 'aktif',  -- aktif, uyari, durduruldu
    email VARCHAR(200),
    telefon VARCHAR(20),
    adres TEXT,
    vergi_no VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ── KULLANICILAR ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.kullanicilar (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    email VARCHAR(200) UNIQUE NOT NULL,
    sifre_hash VARCHAR(200) NOT NULL,
    ad VARCHAR(100),
    rol VARCHAR(20) DEFAULT 'firma_admin',  -- super_admin, firma_admin, firma_kullanici
    aktif BOOLEAN DEFAULT TRUE,
    son_giris TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ── FATURALAR ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.faturalar (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    fatura_no VARCHAR(50) UNIQUE NOT NULL,
    paket_ucreti DECIMAL(10,2) NOT NULL,
    asim_ucreti DECIMAL(10,2) DEFAULT 0,
    toplam DECIMAL(10,2) NOT NULL,
    kdv DECIMAL(10,2) DEFAULT 0,
    genel_toplam DECIMAL(10,2) NOT NULL,
    durum VARCHAR(20) DEFAULT 'bekliyor',  -- bekliyor, odendi, gecikti, iptal
    vade_tarihi DATE NOT NULL,
    odeme_tarihi TIMESTAMP,
    pdf_url VARCHAR(500),
    ay INTEGER NOT NULL,
    yil INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── KULLANIM SAYAÇLARI ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.kullanim_sayaclari (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    ay INTEGER NOT NULL,
    yil INTEGER NOT NULL,
    cagri_sayisi INTEGER DEFAULT 0,
    sms_sayisi INTEGER DEFAULT 0,
    depolama_gb DECIMAL(10,4) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(firma_id, ay, yil)
);

-- ── ÇAĞRI LOGLARI ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.cagri_loglari (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    telefon VARCHAR(20),
    baslangic TIMESTAMP NOT NULL,
    bitis TIMESTAMP,
    sure_saniye INTEGER,
    transkript_gzip BYTEA,
    ai_ozet TEXT,
    sonuc VARCHAR(50),  -- rezervasyon, bilgi, aktarim, basarisiz
    duygu_skoru VARCHAR(20),  -- pozitif, notr, negatif
    aktarim BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── İNDEKSLER ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_firmalar_durum ON shared.firmalar(durum);
CREATE INDEX IF NOT EXISTS idx_faturalar_firma ON shared.faturalar(firma_id, durum);
CREATE INDEX IF NOT EXISTS idx_kullanim_firma_ay ON shared.kullanim_sayaclari(firma_id, yil, ay);
CREATE INDEX IF NOT EXISTS idx_cagri_firma_tarih ON shared.cagri_loglari(firma_id, baslangic);

-- ─────────────────────────────────────────────────────────────
--  NOT: Firma şemaları (firma_1, firma_2, vb.) backend tarafından
--  dinamik olarak oluşturulur (template_engine.py)
-- ─────────────────────────────────────────────────────────────
