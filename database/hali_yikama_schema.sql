-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Halı Yıkama DB Şeması
--  Firma ID: 3 (Test için)
-- ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS firma_3;

-- ── HİZMETLER ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_3.hizmetler (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    kategori VARCHAR(50),          -- hali, koltuk, yorgan, perde, diger
    birim VARCHAR(20) NOT NULL,    -- m2, adet, kg
    birim_fiyat DECIMAL(10,2) NOT NULL,
    min_miktar DECIMAL(10,2) DEFAULT 1,
    max_miktar DECIMAL(10,2),
    sure_gun INTEGER DEFAULT 2,    -- tahmini yıkama süresi (gün)
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── İŞ EMİRLERİ ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_3.is_emirleri (
    id SERIAL PRIMARY KEY,
    musteri_id INTEGER REFERENCES firma_3.musteri_profilleri(id),
    musteri_telefon VARCHAR(20) NOT NULL,
    musteri_ad VARCHAR(100),
    teslim_adresi TEXT NOT NULL,
    hizmet_id INTEGER REFERENCES firma_3.hizmetler(id),
    urun_turu VARCHAR(50) NOT NULL,
    miktar DECIMAL(10,2) NOT NULL,
    birim VARCHAR(20) NOT NULL,
    tahmini_fiyat DECIMAL(10,2),
    gercek_fiyat DECIMAL(10,2),
    teslim_alma_tarihi TIMESTAMP,
    tahmini_teslim_tarihi TIMESTAMP,
    gercek_teslim_tarihi TIMESTAMP,
    durum VARCHAR(30) DEFAULT 'bekliyor',
    -- bekliyor, teslim_alindi, yikaniyor, kurutuluyor, hazir, teslim_edildi, iptal
    notlar TEXT,
    sms_gonderildi BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── MÜŞTERİ PROFİLLERİ ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_3.musteri_profilleri (
    id SERIAL PRIMARY KEY,
    telefon VARCHAR(20) UNIQUE NOT NULL,
    ad VARCHAR(100),
    email VARCHAR(100),
    kayitli_adres TEXT,
    toplam_is_emri INTEGER DEFAULT 0,
    toplam_harcama DECIMAL(10,2) DEFAULT 0,
    son_siparis TIMESTAMP,
    tercih_notlari TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── FİYAT TAKVİMİ (Kampanyalar) ──────────────────────────────
CREATE TABLE IF NOT EXISTS firma_3.fiyat_takvimi (
    id SERIAL PRIMARY KEY,
    hizmet_id INTEGER REFERENCES firma_3.hizmetler(id),
    kampanya_adi VARCHAR(100),
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    kampanya_fiyati DECIMAL(10,2) NOT NULL,
    aktif BOOLEAN DEFAULT TRUE
);

-- ── AYARLAR ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_3.ayarlar (
    id SERIAL PRIMARY KEY,
    isletme_adi VARCHAR(200),
    adres TEXT,
    telefon VARCHAR(20),
    calisma_saatleri JSONB,
    min_siparis_tutari DECIMAL(10,2) DEFAULT 0,
    ucretsiz_teslim_limiti DECIMAL(10,2),
    aktif BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── İNDEKSLER ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_is_emirleri_telefon ON firma_3.is_emirleri(musteri_telefon);
CREATE INDEX IF NOT EXISTS idx_is_emirleri_durum ON firma_3.is_emirleri(durum);
CREATE INDEX IF NOT EXISTS idx_is_emirleri_tarih ON firma_3.is_emirleri(teslim_alma_tarihi);
CREATE INDEX IF NOT EXISTS idx_musteri_telefon ON firma_3.musteri_profilleri(telefon);

-- ── TEST VERİLERİ ─────────────────────────────────────────────
INSERT INTO firma_3.hizmetler (ad, kategori, birim, birim_fiyat, sure_gun) VALUES
('Halı Yıkama', 'hali', 'm2', 30.00, 2),
('Koltuk Takımı (3+2+1)', 'koltuk', 'adet', 750.00, 1),
('Koltuk (3lü)', 'koltuk', 'adet', 350.00, 1),
('Koltuk (2li)', 'koltuk', 'adet', 250.00, 1),
('Tekli Koltuk', 'koltuk', 'adet', 150.00, 1),
('Yorgan Yıkama', 'yorgan', 'adet', 200.00, 2),
('Perde Yıkama', 'perde', 'm2', 25.00, 3),
('Battaniye Yıkama', 'yorgan', 'adet', 150.00, 2),
('Yatak Örtüsü', 'diger', 'adet', 100.00, 1),
('Minder Yıkama', 'diger', 'adet', 80.00, 1)
ON CONFLICT DO NOTHING;

INSERT INTO firma_3.musteri_profilleri (telefon, ad, kayitli_adres) VALUES
('5551111111', 'Ayşe Kaya', 'Atatürk Mah. Gül Sok. No:5 Kadıköy/İstanbul'),
('5552222222', 'Mehmet Demir', 'Bağcılar Mah. Lale Cad. No:12 Bağcılar/İstanbul'),
('5553333333', 'Fatma Yılmaz', 'Çankaya Mah. Akasya Sok. No:8 Çankaya/Ankara')
ON CONFLICT (telefon) DO NOTHING;

INSERT INTO firma_3.ayarlar (isletme_adi, calisma_saatleri) VALUES
(
    'VoiceAI Halı Yıkama',
    '{"hafta_ici": {"acilis": "08:00", "kapanis": "18:00"}, "cumartesi": {"acilis": "09:00", "kapanis": "16:00"}, "pazar": null}'::jsonb
) ON CONFLICT DO NOTHING;

-- Örnek iş emirleri
INSERT INTO firma_3.is_emirleri (musteri_telefon, musteri_ad, teslim_adresi, urun_turu, miktar, birim, tahmini_fiyat, durum) VALUES
('5551111111', 'Ayşe Kaya', 'Atatürk Mah. Gül Sok. No:5', 'Halı', 12.00, 'm2', 360.00, 'yikaniyor'),
('5552222222', 'Mehmet Demir', 'Bağcılar Mah. Lale Cad. No:12', 'Koltuk (3lü)', 1.00, 'adet', 350.00, 'hazir'),
('5553333333', 'Fatma Yılmaz', 'Çankaya Mah. Akasya Sok. No:8', 'Yorgan', 2.00, 'adet', 400.00, 'bekliyor')
ON CONFLICT DO NOTHING;

-- ── GÖRÜNÜMLER ────────────────────────────────────────────────
CREATE OR REPLACE VIEW firma_3.aktif_is_emirleri AS
SELECT
    ie.id,
    ie.musteri_ad,
    ie.musteri_telefon,
    ie.urun_turu,
    ie.miktar,
    ie.birim,
    ie.tahmini_fiyat,
    ie.durum,
    ie.teslim_alma_tarihi,
    ie.tahmini_teslim_tarihi
FROM firma_3.is_emirleri ie
WHERE ie.durum NOT IN ('teslim_edildi', 'iptal')
ORDER BY ie.created_at DESC;

-- ── TRİGGER: İş emri oluşturulduğunda müşteri profili güncelle ──
CREATE OR REPLACE FUNCTION firma_3.is_emri_sonrasi_guncelle()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO firma_3.musteri_profilleri (telefon, ad)
    VALUES (NEW.musteri_telefon, NEW.musteri_ad)
    ON CONFLICT (telefon) DO UPDATE
    SET ad = COALESCE(EXCLUDED.ad, firma_3.musteri_profilleri.ad),
        toplam_is_emri = firma_3.musteri_profilleri.toplam_is_emri + 1,
        son_siparis = NOW(),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS is_emri_olusturuldu ON firma_3.is_emirleri;
CREATE TRIGGER is_emri_olusturuldu
AFTER INSERT ON firma_3.is_emirleri
FOR EACH ROW
EXECUTE FUNCTION firma_3.is_emri_sonrasi_guncelle();

-- ── YETKİLENDİRME ─────────────────────────────────────────────
GRANT ALL PRIVILEGES ON SCHEMA firma_3 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA firma_3 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA firma_3 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA firma_3 TO voiceai_user;

DO $$
BEGIN
    RAISE NOTICE '✅ Halı Yıkama şeması başarıyla oluşturuldu!';
    RAISE NOTICE '   - 10 hizmet';
    RAISE NOTICE '   - 3 müşteri profili';
    RAISE NOTICE '   - 3 örnek iş emri';
END $$;
