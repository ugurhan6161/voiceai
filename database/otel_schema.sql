-- Otel Şablonu için Veritabanı Şeması
-- Firma ID: 1 (Test için)

-- Firma şeması oluştur (eğer yoksa)
CREATE SCHEMA IF NOT EXISTS firma_1;

-- Odalar tablosu
CREATE TABLE IF NOT EXISTS firma_1.odalar (
    id SERIAL PRIMARY KEY,
    oda_no VARCHAR(10) NOT NULL UNIQUE,
    tip VARCHAR(50) NOT NULL,  -- 'tek', 'cift', 'suit', 'aile'
    kapasite INTEGER NOT NULL,
    fiyat DECIMAL(10, 2) NOT NULL,
    ozellikler JSONB,  -- Ek özellikler (balkon, deniz manzarası, vb.)
    aktif BOOLEAN DEFAULT true,
    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rezervasyonlar tablosu
CREATE TABLE IF NOT EXISTS firma_1.rezervasyonlar (
    id SERIAL PRIMARY KEY,
    musteri_ad VARCHAR(100) NOT NULL,
    telefon VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    tarih DATE NOT NULL,
    saat TIME,
    kisi_sayisi INTEGER NOT NULL,
    oda_id INTEGER REFERENCES firma_1.odalar(id),
    sure INTEGER,  -- Konaklama süresi (gün)
    durum VARCHAR(20) DEFAULT 'onaylandi',  -- 'onaylandi', 'iptal', 'tamamlandi'
    notlar TEXT,
    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iptal_zamani TIMESTAMP
);

-- Rezervasyonlar için indeksler
CREATE INDEX IF NOT EXISTS idx_rezervasyonlar_telefon ON firma_1.rezervasyonlar(telefon);
CREATE INDEX IF NOT EXISTS idx_rezervasyonlar_tarih ON firma_1.rezervasyonlar(tarih);
CREATE INDEX IF NOT EXISTS idx_rezervasyonlar_durum ON firma_1.rezervasyonlar(durum);

-- Ayarlar tablosu
CREATE TABLE IF NOT EXISTS firma_1.ayarlar (
    id SERIAL PRIMARY KEY,
    fiyat_listesi JSONB,  -- Hizmet türlerine göre fiyatlar
    calisma_saatleri JSONB,  -- Açılış/kapanış saatleri
    kapasite_limitleri JSONB,  -- Günlük/saatlik kapasite limitleri
    aktif BOOLEAN DEFAULT true,
    guncelleme_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test verileri ekle

-- Odalar
INSERT INTO firma_1.odalar (oda_no, tip, kapasite, fiyat, ozellikler) VALUES
('101', 'tek', 1, 500.00, '{"balkon": false, "manzara": "bahçe", "klima": true, "minibar": true}'),
('102', 'cift', 2, 800.00, '{"balkon": true, "manzara": "deniz", "klima": true, "minibar": true, "jakuzi": false}'),
('201', 'suit', 4, 1500.00, '{"balkon": true, "manzara": "deniz", "klima": true, "minibar": true, "jakuzi": true, "salon": true}'),
('202', 'aile', 4, 1200.00, '{"balkon": true, "manzara": "havuz", "klima": true, "minibar": true, "cocuk_yatagi": true}'),
('301', 'cift', 2, 900.00, '{"balkon": true, "manzara": "deniz", "klima": true, "minibar": true, "jakuzi": false}')
ON CONFLICT (oda_no) DO NOTHING;

-- Ayarlar
INSERT INTO firma_1.ayarlar (fiyat_listesi, calisma_saatleri, kapasite_limitleri) VALUES
(
    '{
        "tek_oda": 500,
        "cift_oda": 800,
        "suit": 1500,
        "aile_odasi": 1200,
        "kahvalti": 100,
        "spa": 200,
        "havuz": 0
    }'::jsonb,
    '{
        "resepsiyon": {"acilis": "00:00", "kapanis": "23:59"},
        "restoran": {"acilis": "07:00", "kapanis": "23:00"},
        "spa": {"acilis": "09:00", "kapanis": "20:00"}
    }'::jsonb,
    '{
        "gunluk_max_rezervasyon": 50,
        "saatlik_max_rezervasyon": 10
    }'::jsonb
)
ON CONFLICT DO NOTHING;

-- Örnek rezervasyonlar (test için)
INSERT INTO firma_1.rezervasyonlar (musteri_ad, telefon, tarih, saat, kisi_sayisi, oda_id, sure, durum, notlar) VALUES
('Ahmet Yılmaz', '5551234567', CURRENT_DATE + INTERVAL '2 days', '14:00', 2, 2, 3, 'onaylandi', 'Balayı paketi'),
('Ayşe Demir', '5559876543', CURRENT_DATE + INTERVAL '5 days', '15:00', 4, 4, 7, 'onaylandi', 'Aile tatili'),
('Mehmet Kaya', '5556543210', CURRENT_DATE + INTERVAL '1 day', '12:00', 1, 1, 2, 'onaylandi', NULL)
ON CONFLICT DO NOTHING;

-- İndeksler oluştur (performans için)
CREATE INDEX IF NOT EXISTS idx_rezervasyonlar_tarih_durum ON firma_1.rezervasyonlar(tarih, durum);
CREATE INDEX IF NOT EXISTS idx_rezervasyonlar_telefon_durum ON firma_1.rezervasyonlar(telefon, durum);
CREATE INDEX IF NOT EXISTS idx_odalar_tip_aktif ON firma_1.odalar(tip, aktif);

-- Görünümler (raporlama için)
CREATE OR REPLACE VIEW firma_1.gunluk_rezervasyonlar AS
SELECT 
    r.id,
    r.musteri_ad,
    r.telefon,
    r.tarih,
    r.saat,
    r.kisi_sayisi,
    o.oda_no,
    o.tip as oda_tipi,
    r.sure,
    r.durum,
    r.olusturma_zamani
FROM firma_1.rezervasyonlar r
LEFT JOIN firma_1.odalar o ON r.oda_id = o.id
WHERE r.tarih >= CURRENT_DATE
ORDER BY r.tarih, r.saat;

CREATE OR REPLACE VIEW firma_1.musait_odalar AS
SELECT 
    o.id,
    o.oda_no,
    o.tip,
    o.kapasite,
    o.fiyat,
    o.ozellikler
FROM firma_1.odalar o
WHERE o.aktif = true
AND o.id NOT IN (
    SELECT oda_id 
    FROM firma_1.rezervasyonlar 
    WHERE tarih = CURRENT_DATE 
    AND durum = 'onaylandi'
    AND oda_id IS NOT NULL
);

-- Trigger: Rezervasyon oluşturulduğunda otomatik bildirim
CREATE OR REPLACE FUNCTION firma_1.rezervasyon_bildirim()
RETURNS TRIGGER AS $$
BEGIN
    -- Burada SMS veya email bildirimi tetiklenebilir
    -- Şimdilik sadece log
    RAISE NOTICE 'Yeni rezervasyon oluşturuldu: ID=%, Müşteri=%, Tarih=%', 
        NEW.id, NEW.musteri_ad, NEW.tarih;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rezervasyon_olusturuldu
AFTER INSERT ON firma_1.rezervasyonlar
FOR EACH ROW
EXECUTE FUNCTION firma_1.rezervasyon_bildirim();

-- Yetkilendirme
GRANT ALL PRIVILEGES ON SCHEMA firma_1 TO voiceai;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA firma_1 TO voiceai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA firma_1 TO voiceai;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA firma_1 TO voiceai;

-- Başarı mesajı
DO $$
BEGIN
    RAISE NOTICE '✅ Otel şeması başarıyla oluşturuldu!';
    RAISE NOTICE '📊 Test verileri eklendi:';
    RAISE NOTICE '   - 5 oda';
    RAISE NOTICE '   - 3 örnek rezervasyon';
    RAISE NOTICE '   - Fiyat listesi ve ayarlar';
END $$;
