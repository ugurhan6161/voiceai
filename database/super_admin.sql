-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Super Admin Kullanıcısı
--  Çalıştır: docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai < /opt/voiceai/database/super_admin.sql
-- ─────────────────────────────────────────────────────────────

-- pgcrypto extension gerekli
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Geri arama kuyruğu tablosu (init.sql'de yoksa ekle)
CREATE TABLE IF NOT EXISTS shared.geri_arama_kuyrugu (
    id SERIAL PRIMARY KEY,
    kuyruk_id VARCHAR(20) UNIQUE NOT NULL,
    telefon VARCHAR(20) NOT NULL,
    firma_id INTEGER REFERENCES shared.firmalar(id),
    musteri_ad VARCHAR(100),
    notlar TEXT,
    deneme_sayisi INTEGER DEFAULT 0,
    durum VARCHAR(20) DEFAULT 'bekliyor',
    olusturma_zamani TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Şablon tanımları tablosu
CREATE TABLE IF NOT EXISTS shared.sablon_tanimlari (
    id SERIAL PRIMARY KEY,
    kod VARCHAR(50) UNIQUE NOT NULL,
    ad VARCHAR(100) NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    ikon VARCHAR(10) DEFAULT '🏢',
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    sira INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tüm şablonları ekle
INSERT INTO shared.sablon_tanimlari (kod, ad, kategori, ikon, aciklama, sira) VALUES
-- Konaklama
('otel', 'Otel', 'konaklama', '🏨', 'Otel rezervasyon ve bilgi sistemi', 1),
('pansiyon_apart', 'Pansiyon / Apart', 'konaklama', '🏠', 'Pansiyon ve apart daire rezervasyonu', 2),
('kamp_bungalov', 'Kamp / Bungalov', 'konaklama', '⛺', 'Kamp alanı ve bungalov rezervasyonu', 3),
('tekne_yat', 'Tekne / Yat', 'konaklama', '⛵', 'Tekne ve yat kiralama', 4),
-- Sağlık
('klinik_poliklinik', 'Klinik / Poliklinik', 'saglik', '🏥', 'Randevu ve hasta yönetimi', 10),
('dis_klinigi', 'Diş Kliniği', 'saglik', '🦷', 'Diş kliniği randevu sistemi', 11),
('goz_klinigi', 'Göz Kliniği', 'saglik', '👁️', 'Göz kliniği randevu sistemi', 12),
('spa_masaj', 'Spa / Masaj', 'saglik', '💆', 'Spa ve masaj randevu sistemi', 13),
('eczane', 'Eczane', 'saglik', '💊', 'Eczane bilgi ve sipariş sistemi', 14),
('veteriner', 'Veteriner', 'saglik', '🐾', 'Veteriner randevu sistemi', 15),
-- Kişisel Bakım
('kuafor_berber', 'Kuaför / Berber', 'kisisel_bakim', '💈', 'Kuaför ve berber randevu sistemi', 20),
('guzellik_salonu', 'Güzellik Salonu', 'kisisel_bakim', '💅', 'Güzellik salonu randevu sistemi', 21),
('epilasyon_lazer', 'Epilasyon / Lazer', 'kisisel_bakim', '✨', 'Epilasyon ve lazer randevu sistemi', 22),
('spor_salonu', 'Spor Salonu', 'kisisel_bakim', '🏋️', 'Spor salonu üyelik ve randevu', 23),
-- Yiyecek & İçecek
('restoran', 'Restoran', 'yiyecek_icecek', '🍽️', 'Restoran rezervasyon ve sipariş', 30),
('kafe', 'Kafe', 'yiyecek_icecek', '☕', 'Kafe rezervasyon ve sipariş', 31),
('pastane', 'Pastane', 'yiyecek_icecek', '🎂', 'Pastane sipariş ve rezervasyon', 32),
-- Ev Hizmetleri
('hali_yikama', 'Halı Yıkama', 'ev_hizmetleri', '🧺', 'Halı ve koltuk yıkama iş emri', 40),
('kuru_temizleme', 'Kuru Temizleme', 'ev_hizmetleri', '👔', 'Kuru temizleme sipariş sistemi', 41),
('ev_tamircisi', 'Ev Tamircisi', 'ev_hizmetleri', '🔧', 'Ev tamir ve bakım randevu', 42),
('pvc_cam_usta', 'PVC / Cam Usta', 'ev_hizmetleri', '🪟', 'PVC ve cam usta randevu', 43),
('mobilya_tamiri', 'Mobilya Tamiri', 'ev_hizmetleri', '🪑', 'Mobilya tamir randevu', 44),
('bahce_bakim', 'Bahçe Bakım', 'ev_hizmetleri', '🌿', 'Bahçe bakım randevu', 45),
-- Araç
('arac_kiralama', 'Araç Kiralama', 'arac_tasima', '🚗', 'Araç kiralama rezervasyon', 50),
('oto_servis', 'Oto Servis', 'arac_tasima', '🔩', 'Oto servis randevu sistemi', 51),
('arac_yikama', 'Araç Yıkama', 'arac_tasima', '🚿', 'Araç yıkama randevu', 52),
('lastikci', 'Lastikçi', 'arac_tasima', '🔄', 'Lastik değişim randevu', 53),
('ozel_sofor', 'Özel Şoför', 'arac_tasima', '🚖', 'Özel şoför rezervasyon', 54),
-- Enerji & Temel
('su_bayii', 'Su Bayii', 'enerji_temel', '💧', 'Damacana su sipariş sistemi', 60),
('tup_gaz_bayii', 'Tüp Gaz Bayii', 'enerji_temel', '🔥', 'Tüp gaz sipariş sistemi', 61),
('elektrikci', 'Elektrikçi', 'enerji_temel', '⚡', 'Elektrikçi randevu sistemi', 62),
('tesisatci', 'Tesisatçı', 'enerji_temel', '🔧', 'Tesisatçı randevu sistemi', 63),
('isitma_klima', 'Isıtma / Klima', 'enerji_temel', '❄️', 'Isıtma ve klima servis randevu', 64),
-- Eğitim & Danışmanlık
('ozel_ders', 'Özel Ders', 'egitim_danismanlik', '📚', 'Özel ders randevu sistemi', 70),
('muzik_okulu', 'Müzik Okulu', 'egitim_danismanlik', '🎵', 'Müzik okulu randevu sistemi', 71),
('avukatlik', 'Avukatlık', 'egitim_danismanlik', '⚖️', 'Avukatlık randevu sistemi', 72),
('muhasebe', 'Muhasebe', 'egitim_danismanlik', '📊', 'Muhasebe danışmanlık randevu', 73),
('emlak', 'Emlak', 'egitim_danismanlik', '🏡', 'Emlak danışmanlık sistemi', 74),
-- Özel Hizmetler
('fotograf_studyo', 'Fotoğraf Stüdyo', 'ozel_hizmetler', '📷', 'Fotoğraf stüdyo randevu', 80),
('evcil_hayvan', 'Evcil Hayvan', 'ozel_hizmetler', '🐕', 'Evcil hayvan bakım randevu', 81),
('organizasyon', 'Organizasyon', 'ozel_hizmetler', '🎉', 'Organizasyon planlama sistemi', 82),
('matbaa', 'Matbaa', 'ozel_hizmetler', '🖨️', 'Matbaa sipariş sistemi', 83),
('ozel_sablon', 'Özel Şablon', 'ozel_hizmetler', '⭐', 'Özelleştirilebilir şablon', 99)
ON CONFLICT (kod) DO NOTHING;

-- Super Admin kullanıcısı oluştur
INSERT INTO shared.kullanicilar
    (email, sifre_hash, ad, rol, aktif)
VALUES
    (
        'admin@voiceai.com',
        crypt('Admin2026!', gen_salt('bf')),
        'Super Admin',
        'super_admin',
        true
    )
ON CONFLICT (email) DO UPDATE
SET sifre_hash = crypt('Admin2026!', gen_salt('bf')),
    rol = 'super_admin',
    aktif = true;

-- Doğrulama
DO $$
DECLARE
    admin_id INTEGER;
BEGIN
    SELECT id INTO admin_id FROM shared.kullanicilar WHERE email = 'admin@voiceai.com';
    IF admin_id IS NOT NULL THEN
        RAISE NOTICE '✅ Super Admin oluşturuldu: admin@voiceai.com (ID: %)', admin_id;
    ELSE
        RAISE EXCEPTION '❌ Super Admin oluşturulamadı!';
    END IF;

    RAISE NOTICE '✅ Şablon tanımları eklendi: % adet', (SELECT COUNT(*) FROM shared.sablon_tanimlari);
    RAISE NOTICE '✅ Geri arama kuyruğu tablosu hazır';
END $$;
