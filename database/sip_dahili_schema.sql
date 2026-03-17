-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — SIP Dahili Hat Şeması
--  Firma çalışanları Zoiper/MicroSIP ile bağlanır
-- ─────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── SIP DAHİLİLERİ ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.sip_dahilileri (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    dahili_no VARCHAR(10) UNIQUE NOT NULL,      -- 101, 102, ...
    kullanici_adi VARCHAR(50) UNIQUE NOT NULL,   -- firma_1_dahili
    sifre_hash TEXT NOT NULL,                    -- AES-256 şifreli
    yonlendirme_turu VARCHAR(20) DEFAULT 'uygulama',
    -- 'uygulama': Zoiper/SIP uygulamasına
    -- 'telefon': Gerçek telefon numarasına
    telefon_no VARCHAR(20),                      -- Gerçek tel (yonlendirme_turu='telefon' ise)
    aktif BOOLEAN DEFAULT TRUE,
    son_kayit TIMESTAMP,                         -- Son SIP kayıt zamanı
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── YÖNLENDIRME AYARLARI ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.yonlendirme_ayarlari (
    id SERIAL PRIMARY KEY,
    firma_id INTEGER REFERENCES shared.firmalar(id) UNIQUE,
    aktif_tur VARCHAR(20) DEFAULT 'uygulama',   -- 'uygulama' veya 'telefon'
    dahili_id INTEGER REFERENCES shared.sip_dahilileri(id),
    telefon_no VARCHAR(20),
    mesai_baslangic TIME DEFAULT '09:00',
    mesai_bitis TIME DEFAULT '18:00',
    mesai_disi_yonlendirme VARCHAR(20) DEFAULT 'sesli_mesaj',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── İNDEKSLER ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sip_firma ON shared.sip_dahilileri(firma_id);
CREATE INDEX IF NOT EXISTS idx_sip_dahili_no ON shared.sip_dahilileri(dahili_no);
CREATE INDEX IF NOT EXISTS idx_yonlendirme_firma ON shared.yonlendirme_ayarlari(firma_id);

-- ── ÖRNEK VERİ: Firma 1 için dahili ─────────────────────────
INSERT INTO shared.sip_dahilileri
    (firma_id, dahili_no, kullanici_adi, sifre_hash, yonlendirme_turu)
VALUES
    (1, '101', 'firma_1_dahili', 'DahiliSifre2026!', 'uygulama')
ON CONFLICT (dahili_no) DO NOTHING;

INSERT INTO shared.yonlendirme_ayarlari
    (firma_id, aktif_tur, telefon_no)
VALUES
    (1, 'uygulama', NULL)
ON CONFLICT (firma_id) DO NOTHING;

-- ── YETKİLENDİRME ─────────────────────────────────────────────
GRANT ALL PRIVILEGES ON shared.sip_dahilileri TO voiceai_user;
GRANT ALL PRIVILEGES ON shared.yonlendirme_ayarlari TO voiceai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shared TO voiceai_user;

DO $$
BEGIN
    RAISE NOTICE '✅ SIP dahili şeması oluşturuldu';
    RAISE NOTICE '   - Firma 1 dahili: 101 / firma_1_dahili / DahiliSifre2026!';
END $$;
