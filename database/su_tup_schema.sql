-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Su / Tüp Gaz Bayii DB Şeması
--  Firma ID: 4 (Test için)
-- ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS firma_4;

-- ── ÜRÜNLER ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_4.urunler (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    kategori VARCHAR(30) DEFAULT 'su',  -- su, tup, aksesuar
    birim VARCHAR(20) DEFAULT 'adet',
    fiyat DECIMAL(10,2) NOT NULL,
    depozito DECIMAL(10,2) DEFAULT 0,
    kg DECIMAL(5,2),                    -- tüp için kg bilgisi
    hacim_litre DECIMAL(5,2),           -- su için litre bilgisi
    stok INTEGER DEFAULT 0,
    min_stok_uyari INTEGER DEFAULT 10,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── SİPARİŞLER ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_4.siparisler (
    id SERIAL PRIMARY KEY,
    musteri_id INTEGER REFERENCES firma_4.musteri_profilleri(id),
    musteri_telefon VARCHAR(20) NOT NULL,
    musteri_ad VARCHAR(100),
    teslimat_adresi TEXT NOT NULL,
    urun_id INTEGER REFERENCES firma_4.urunler(id),
    adet INTEGER NOT NULL DEFAULT 1,
    birim_fiyat DECIMAL(10,2),
    toplam_fiyat DECIMAL(10,2),
    depozito_toplam DECIMAL(10,2) DEFAULT 0,
    bos_iade BOOLEAN DEFAULT FALSE,     -- boş tüp/damacana iade
    bos_iade_adet INTEGER DEFAULT 0,
    teslimat_saati VARCHAR(30),         -- "14:00-16:00" gibi
    teslimat_notu TEXT,
    durum VARCHAR(30) DEFAULT 'bekliyor',
    -- bekliyor, hazirlaniyor, yolda, teslim_edildi, iptal
    sms_gonderildi BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── MÜŞTERİ PROFİLLERİ ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_4.musteri_profilleri (
    id SERIAL PRIMARY KEY,
    telefon VARCHAR(20) UNIQUE NOT NULL,
    ad VARCHAR(100),
    email VARCHAR(100),
    kayitli_adres TEXT,
    bos_damacana_sayisi INTEGER DEFAULT 0,  -- müşterideki boş damacana
    bos_tup_sayisi INTEGER DEFAULT 0,       -- müşterideki boş tüp
    toplam_siparis INTEGER DEFAULT 0,
    toplam_harcama DECIMAL(10,2) DEFAULT 0,
    son_siparis TIMESTAMP,
    tercih_urun_id INTEGER REFERENCES firma_4.urunler(id),
    notlar TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── TESLİMAT BÖLGELERİ ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_4.teslimat_bolgeleri (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    ilce VARCHAR(50),
    mahalleler TEXT[],
    min_siparis_adet INTEGER DEFAULT 1,
    teslimat_ucreti DECIMAL(10,2) DEFAULT 0,
    aktif BOOLEAN DEFAULT TRUE
);

-- ── AYARLAR ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_4.ayarlar (
    id SERIAL PRIMARY KEY,
    isletme_adi VARCHAR(200),
    adres TEXT,
    telefon VARCHAR(20),
    calisma_saatleri JSONB,
    min_siparis_adet INTEGER DEFAULT 1,
    ucretsiz_teslimat_limiti INTEGER DEFAULT 3,
    aktif BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── İNDEKSLER ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_siparisler_telefon ON firma_4.siparisler(musteri_telefon);
CREATE INDEX IF NOT EXISTS idx_siparisler_durum ON firma_4.siparisler(durum);
CREATE INDEX IF NOT EXISTS idx_siparisler_tarih ON firma_4.siparisler(created_at);
CREATE INDEX IF NOT EXISTS idx_musteri_telefon ON firma_4.musteri_profilleri(telefon);

-- ── TEST VERİLERİ ─────────────────────────────────────────────
INSERT INTO firma_4.urunler (ad, kategori, birim, fiyat, depozito, hacim_litre, stok) VALUES
('Damacana Su 19L', 'su', 'adet', 25.00, 50.00, 19, 200),
('Damacana Su 5L', 'su', 'adet', 12.00, 20.00, 5, 100),
('Damacana Su 10L', 'su', 'adet', 18.00, 30.00, 10, 80)
ON CONFLICT DO NOTHING;

INSERT INTO firma_4.urunler (ad, kategori, birim, fiyat, depozito, kg, stok) VALUES
('Tüp Gaz 12 kg', 'tup', 'adet', 450.00, 200.00, 12, 50),
('Tüp Gaz 5 kg', 'tup', 'adet', 220.00, 100.00, 5, 30),
('Tüp Gaz 2 kg (Bütan)', 'tup', 'adet', 120.00, 50.00, 2, 20)
ON CONFLICT DO NOTHING;

INSERT INTO firma_4.musteri_profilleri (telefon, ad, kayitli_adres, bos_damacana_sayisi) VALUES
('5551111111', 'Ali Veli', 'Merkez Mah. Cumhuriyet Cad. No:10', 2),
('5552222222', 'Hasan Hüseyin', 'Yeni Mah. İstiklal Sok. No:5', 1),
('5553333333', 'Zeynep Nur', 'Bahçelievler Mah. Çiçek Cad. No:3', 0)
ON CONFLICT (telefon) DO NOTHING;

INSERT INTO firma_4.teslimat_bolgeleri (ad, ilce, teslimat_ucreti) VALUES
('Merkez', 'Merkez', 0),
('Kuzey Bölge', 'Kuzey', 5.00),
('Güney Bölge', 'Güney', 5.00)
ON CONFLICT DO NOTHING;

INSERT INTO firma_4.ayarlar (isletme_adi, calisma_saatleri) VALUES
(
    'VoiceAI Su & Tüp Bayii',
    '{"hafta_ici": {"acilis": "07:00", "kapanis": "21:00"}, "cumartesi": {"acilis": "08:00", "kapanis": "20:00"}, "pazar": {"acilis": "09:00", "kapanis": "18:00"}}'::jsonb
) ON CONFLICT DO NOTHING;

-- Örnek siparişler
INSERT INTO firma_4.siparisler (musteri_telefon, musteri_ad, teslimat_adresi, urun_id, adet, birim_fiyat, toplam_fiyat, durum) VALUES
('5551111111', 'Ali Veli', 'Merkez Mah. Cumhuriyet Cad. No:10', 1, 2, 25.00, 50.00, 'teslim_edildi'),
('5552222222', 'Hasan Hüseyin', 'Yeni Mah. İstiklal Sok. No:5', 4, 1, 450.00, 450.00, 'yolda'),
('5553333333', 'Zeynep Nur', 'Bahçelievler Mah. Çiçek Cad. No:3', 1, 3, 25.00, 75.00, 'bekliyor')
ON CONFLICT DO NOTHING;

-- ── GÖRÜNÜMLER ────────────────────────────────────────────────
CREATE OR REPLACE VIEW firma_4.bekleyen_siparisler AS
SELECT
    s.id,
    s.musteri_ad,
    s.musteri_telefon,
    u.ad AS urun_adi,
    s.adet,
    s.toplam_fiyat,
    s.teslimat_adresi,
    s.teslimat_saati,
    s.durum,
    s.created_at
FROM firma_4.siparisler s
LEFT JOIN firma_4.urunler u ON s.urun_id = u.id
WHERE s.durum IN ('bekliyor', 'hazirlaniyor', 'yolda')
ORDER BY s.created_at ASC;

CREATE OR REPLACE VIEW firma_4.stok_durumu AS
SELECT
    id,
    ad,
    kategori,
    fiyat,
    stok,
    min_stok_uyari,
    CASE WHEN stok <= min_stok_uyari THEN TRUE ELSE FALSE END AS dusuk_stok
FROM firma_4.urunler
WHERE aktif = TRUE
ORDER BY kategori, ad;

-- ── TRİGGER: Sipariş oluşturulduğunda müşteri profili güncelle ──
CREATE OR REPLACE FUNCTION firma_4.siparis_sonrasi_guncelle()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO firma_4.musteri_profilleri (telefon, ad)
    VALUES (NEW.musteri_telefon, NEW.musteri_ad)
    ON CONFLICT (telefon) DO UPDATE
    SET ad = COALESCE(EXCLUDED.ad, firma_4.musteri_profilleri.ad),
        toplam_siparis = firma_4.musteri_profilleri.toplam_siparis + 1,
        son_siparis = NOW(),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS siparis_olusturuldu ON firma_4.siparisler;
CREATE TRIGGER siparis_olusturuldu
AFTER INSERT ON firma_4.siparisler
FOR EACH ROW
EXECUTE FUNCTION firma_4.siparis_sonrasi_guncelle();

-- ── TRİGGER: Stok düşürme ────────────────────────────────────
CREATE OR REPLACE FUNCTION firma_4.stok_guncelle()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.durum = 'teslim_edildi' AND OLD.durum != 'teslim_edildi' THEN
        UPDATE firma_4.urunler
        SET stok = stok - NEW.adet
        WHERE id = NEW.urun_id AND stok >= NEW.adet;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS siparis_teslim_stok ON firma_4.siparisler;
CREATE TRIGGER siparis_teslim_stok
AFTER UPDATE ON firma_4.siparisler
FOR EACH ROW
EXECUTE FUNCTION firma_4.stok_guncelle();

-- ── YETKİLENDİRME ─────────────────────────────────────────────
GRANT ALL PRIVILEGES ON SCHEMA firma_4 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA firma_4 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA firma_4 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA firma_4 TO voiceai_user;

DO $$
BEGIN
    RAISE NOTICE '✅ Su/Tüp Bayii şeması başarıyla oluşturuldu!';
    RAISE NOTICE '   - 6 ürün (3 su + 3 tüp)';
    RAISE NOTICE '   - 3 müşteri profili';
    RAISE NOTICE '   - 3 örnek sipariş';
END $$;
