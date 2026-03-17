-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Klinik / Poliklinik DB Şeması
--  Firma ID: 2 (Test için)
-- ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS firma_2;

-- ── DOKTORLAR ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_2.doktorlar (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    uzmanlik VARCHAR(100) NOT NULL,
    unvan VARCHAR(50) DEFAULT 'Dr.',
    telefon VARCHAR(20),
    email VARCHAR(100),
    biyografi TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── HASTA PROFİLLERİ ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_2.hasta_profilleri (
    id SERIAL PRIMARY KEY,
    telefon VARCHAR(20) UNIQUE NOT NULL,
    ad VARCHAR(100),
    soyad VARCHAR(100),
    dogum_tarihi DATE,
    tc_kimlik VARCHAR(11),
    email VARCHAR(100),
    sigorta_turu VARCHAR(50),  -- SGK, Özel, Yok
    sigorta_no VARCHAR(50),
    kan_grubu VARCHAR(5),
    alerjiler TEXT,
    kronik_hastaliklar TEXT,
    notlar TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── RANDEVULAR ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_2.randevular (
    id SERIAL PRIMARY KEY,
    hasta_id INTEGER REFERENCES firma_2.hasta_profilleri(id),
    doktor_id INTEGER REFERENCES firma_2.doktorlar(id),
    hasta_telefon VARCHAR(20) NOT NULL,
    hasta_ad VARCHAR(100),
    tarih DATE NOT NULL,
    saat TIME NOT NULL,
    sure_dakika INTEGER DEFAULT 30,
    sikayet TEXT,
    durum VARCHAR(20) DEFAULT 'onaylandi',  -- onaylandi, iptal, tamamlandi, gelmedi
    randevu_turu VARCHAR(30) DEFAULT 'muayene',  -- muayene, kontrol, tahlil, ameliyat
    notlar TEXT,
    sms_gonderildi BOOLEAN DEFAULT FALSE,
    hatirlatma_gonderildi BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── ÇALIŞMA TAKVİMİ ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_2.calisma_takvimi (
    id SERIAL PRIMARY KEY,
    doktor_id INTEGER REFERENCES firma_2.doktorlar(id),
    gun_haftanin INTEGER NOT NULL,  -- 1=Pazartesi, 7=Pazar
    baslangic_saat TIME NOT NULL,
    bitis_saat TIME NOT NULL,
    randevu_suresi INTEGER DEFAULT 30,  -- dakika
    aktif BOOLEAN DEFAULT TRUE
);

-- ── AYARLAR ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firma_2.ayarlar (
    id SERIAL PRIMARY KEY,
    klinik_adi VARCHAR(200),
    adres TEXT,
    telefon VARCHAR(20),
    calisma_saatleri JSONB,
    randevu_suresi INTEGER DEFAULT 30,
    max_gunluk_randevu INTEGER DEFAULT 50,
    sms_hatirlatma_saat INTEGER DEFAULT 24,  -- kaç saat önce
    aktif BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── İNDEKSLER ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_randevular_tarih ON firma_2.randevular(tarih);
CREATE INDEX IF NOT EXISTS idx_randevular_doktor ON firma_2.randevular(doktor_id, tarih);
CREATE INDEX IF NOT EXISTS idx_randevular_hasta ON firma_2.randevular(hasta_telefon);
CREATE INDEX IF NOT EXISTS idx_randevular_durum ON firma_2.randevular(durum);
CREATE INDEX IF NOT EXISTS idx_hasta_telefon ON firma_2.hasta_profilleri(telefon);

-- ── TEST VERİLERİ ─────────────────────────────────────────────
INSERT INTO firma_2.doktorlar (ad, uzmanlik, unvan, telefon) VALUES
('Ahmet Yılmaz', 'Dahiliye', 'Uzm. Dr.', '5551234567'),
('Fatma Kaya', 'Kardiyoloji', 'Doç. Dr.', '5559876543'),
('Mehmet Demir', 'Ortopedi', 'Op. Dr.', '5556543210'),
('Ayşe Çelik', 'Nöroloji', 'Prof. Dr.', '5554321098'),
('Ali Şahin', 'Genel Cerrahi', 'Op. Dr.', '5558765432')
ON CONFLICT DO NOTHING;

INSERT INTO firma_2.hasta_profilleri (telefon, ad, soyad, sigorta_turu) VALUES
('5551111111', 'Zeynep', 'Arslan', 'SGK'),
('5552222222', 'Hasan', 'Öztürk', 'Özel'),
('5553333333', 'Elif', 'Yıldız', 'SGK')
ON CONFLICT (telefon) DO NOTHING;

INSERT INTO firma_2.calisma_takvimi (doktor_id, gun_haftanin, baslangic_saat, bitis_saat) VALUES
(1, 1, '09:00', '17:00'),
(1, 2, '09:00', '17:00'),
(1, 3, '09:00', '17:00'),
(1, 4, '09:00', '17:00'),
(1, 5, '09:00', '17:00'),
(2, 1, '10:00', '18:00'),
(2, 3, '10:00', '18:00'),
(2, 5, '10:00', '18:00'),
(3, 2, '08:00', '16:00'),
(3, 4, '08:00', '16:00')
ON CONFLICT DO NOTHING;

INSERT INTO firma_2.ayarlar (klinik_adi, calisma_saatleri, randevu_suresi) VALUES
(
    'VoiceAI Klinik',
    '{"hafta_ici": {"acilis": "08:00", "kapanis": "18:00"}, "cumartesi": {"acilis": "09:00", "kapanis": "14:00"}, "pazar": null}'::jsonb,
    30
) ON CONFLICT DO NOTHING;

-- Örnek randevular
INSERT INTO firma_2.randevular (hasta_id, doktor_id, hasta_telefon, hasta_ad, tarih, saat, sikayet, durum) VALUES
(1, 1, '5551111111', 'Zeynep Arslan', CURRENT_DATE + INTERVAL '1 day', '10:00', 'Baş ağrısı', 'onaylandi'),
(2, 2, '5552222222', 'Hasan Öztürk', CURRENT_DATE + INTERVAL '2 days', '11:30', 'Göğüs ağrısı', 'onaylandi'),
(3, 3, '5553333333', 'Elif Yıldız', CURRENT_DATE + INTERVAL '3 days', '14:00', 'Diz ağrısı', 'onaylandi')
ON CONFLICT DO NOTHING;

-- ── GÖRÜNÜMLER ────────────────────────────────────────────────
CREATE OR REPLACE VIEW firma_2.gunluk_randevular AS
SELECT
    r.id,
    r.tarih,
    r.saat,
    r.hasta_ad,
    r.hasta_telefon,
    d.ad AS doktor_ad,
    d.uzmanlik,
    r.sikayet,
    r.durum,
    r.randevu_turu
FROM firma_2.randevular r
LEFT JOIN firma_2.doktorlar d ON r.doktor_id = d.id
WHERE r.tarih >= CURRENT_DATE
ORDER BY r.tarih, r.saat;

CREATE OR REPLACE VIEW firma_2.musait_slotlar AS
SELECT
    d.id AS doktor_id,
    d.ad AS doktor_ad,
    d.uzmanlik,
    ct.gun_haftanin,
    ct.baslangic_saat,
    ct.bitis_saat,
    ct.randevu_suresi
FROM firma_2.doktorlar d
JOIN firma_2.calisma_takvimi ct ON d.id = ct.doktor_id
WHERE d.aktif = TRUE AND ct.aktif = TRUE;

-- ── TRİGGER: Randevu oluşturulduğunda hasta profili güncelle ──
CREATE OR REPLACE FUNCTION firma_2.randevu_sonrasi_guncelle()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO firma_2.hasta_profilleri (telefon, ad)
    VALUES (NEW.hasta_telefon, NEW.hasta_ad)
    ON CONFLICT (telefon) DO UPDATE
    SET ad = COALESCE(EXCLUDED.ad, firma_2.hasta_profilleri.ad),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS randevu_olusturuldu ON firma_2.randevular;
CREATE TRIGGER randevu_olusturuldu
AFTER INSERT ON firma_2.randevular
FOR EACH ROW
EXECUTE FUNCTION firma_2.randevu_sonrasi_guncelle();

-- ── YETKİLENDİRME ─────────────────────────────────────────────
GRANT ALL PRIVILEGES ON SCHEMA firma_2 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA firma_2 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA firma_2 TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA firma_2 TO voiceai_user;

DO $$
BEGIN
    RAISE NOTICE '✅ Klinik şeması başarıyla oluşturuldu!';
    RAISE NOTICE '   - 5 doktor';
    RAISE NOTICE '   - 3 hasta profili';
    RAISE NOTICE '   - 3 örnek randevu';
END $$;
