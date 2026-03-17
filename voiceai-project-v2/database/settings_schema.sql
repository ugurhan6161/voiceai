-- ─────────────────────────────────────────────────────────────
--  VoiceAI Platform — Ayarlar ve Şablon DB Şeması
--  Bu dosya init.sql'den sonra çalıştırılır
-- ─────────────────────────────────────────────────────────────

-- ── SİSTEM AYARLARI (Admin Yönetir) ──────────────────────────
-- Tüm değerler AES-256-GCM ile şifreli saklanır
CREATE TABLE IF NOT EXISTS shared.sistem_ayarlari (
    id SERIAL PRIMARY KEY,
    kategori VARCHAR(50) NOT NULL,
    -- Kategoriler: sip_netgsm | sip_verimor | sip_twilio |
    --              sms_netgsm | sms_verimor |
    --              iyzico | paytr |
    --              smtp | yedekleme | genel
    anahtar VARCHAR(100) NOT NULL,
    deger TEXT,
    -- AES-256-GCM şifreli: base64(nonce + ciphertext)
    sifirli BOOLEAN DEFAULT FALSE,
    -- TRUE ise frontend'de "••••••••" göster
    aciklama VARCHAR(200),
    guncelleme TIMESTAMP DEFAULT NOW(),
    guncelleyen INTEGER REFERENCES shared.kullanicilar(id),
    UNIQUE(kategori, anahtar)
);

-- Başlangıç ayar anahtarları (değerler boş — panelden doldurulur)
INSERT INTO shared.sistem_ayarlari (kategori, anahtar, sifirli, aciklama) VALUES
-- Netgsm SIP
('sip_netgsm', 'host',       FALSE, 'SIP sunucu adresi'),
('sip_netgsm', 'kullanici',  FALSE, 'SIP kullanıcı adı'),
('sip_netgsm', 'sifre',      TRUE,  'SIP şifresi'),
('sip_netgsm', 'aktif',      FALSE, 'Aktif mi? true/false'),
-- Verimor SIP
('sip_verimor', 'host',      FALSE, 'SIP sunucu adresi'),
('sip_verimor', 'kullanici', FALSE, 'SIP kullanıcı adı'),
('sip_verimor', 'sifre',     TRUE,  'SIP şifresi'),
('sip_verimor', 'aktif',     FALSE, 'Aktif mi? true/false'),
-- Netgsm SMS
('sms_netgsm', 'kullanici',  FALSE, 'SMS API kullanıcı adı'),
('sms_netgsm', 'sifre',      TRUE,  'SMS API şifresi'),
('sms_netgsm', 'baslik',     FALSE, 'SMS gönderici başlığı'),
('sms_netgsm', 'aktif',      FALSE, 'Aktif mi?'),
-- iyzico
('iyzico', 'api_key',        TRUE,  'iyzico API Key'),
('iyzico', 'secret_key',     TRUE,  'iyzico Secret Key'),
('iyzico', 'mod',            FALSE, 'production veya sandbox'),
-- SMTP
('smtp', 'host',             FALSE, 'SMTP sunucu'),
('smtp', 'port',             FALSE, 'SMTP port'),
('smtp', 'kullanici',        FALSE, 'SMTP kullanıcı'),
('smtp', 'sifre',            TRUE,  'SMTP şifre'),
('smtp', 'gonderen_ad',      FALSE, 'Gönderen görünen ad'),
-- Genel
('genel', 'platform_adi',    FALSE, 'Platform adı'),
('genel', 'destek_email',    FALSE, 'Destek e-posta adresi'),
('genel', 'min_odeme_gunu',  FALSE, 'Fatura ödeme süresi (gün)')
ON CONFLICT DO NOTHING;


-- ── ŞABLON TANIMLARI ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shared.sablon_tanimlari (
    id SERIAL PRIMARY KEY,
    kod VARCHAR(50) UNIQUE NOT NULL,
    ad VARCHAR(100) NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    ikon VARCHAR(10) DEFAULT '🏢',
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    sira INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tüm şablonları kaydet
INSERT INTO shared.sablon_tanimlari (kod, ad, kategori, ikon, sira) VALUES
-- Konaklama
('otel',              'Otel / Resort',              'konaklama',          '🏨', 1),
('pansiyon_apart',    'Pansiyon / Apart',            'konaklama',          '🏠', 2),
('kamp_bungalov',     'Kamp / Bungalov',             'konaklama',          '🏕️', 3),
('tekne_yat',         'Tekne / Yat Kiralama',        'konaklama',          '🚢', 4),
-- Sağlık
('klinik_poliklinik', 'Klinik / Poliklinik',         'saglik',             '🏥', 10),
('dis_klinigi',       'Diş Kliniği',                 'saglik',             '🦷', 11),
('goz_klinigi',       'Göz Kliniği',                 'saglik',             '👁️', 12),
('spa_masaj',         'Spa / Masaj Salonu',           'saglik',             '🧘', 13),
('eczane',            'Eczane',                       'saglik',             '💊', 14),
('veteriner',         'Veteriner',                    'saglik',             '🐾', 15),
-- Kişisel Bakım
('kuafor_berber',     'Kuaför / Berber',              'kisisel_bakim',      '💈', 20),
('guzellik_salonu',   'Güzellik Salonu / Nail Art',   'kisisel_bakim',      '💅', 21),
('epilasyon_lazer',   'Epilasyon / Lazer Merkezi',    'kisisel_bakim',      '✨', 22),
('spor_salonu',       'Spor Salonu / Fitness',        'kisisel_bakim',      '🏋️', 23),
-- Yiyecek
('restoran',          'Restoran',                     'yiyecek_icecek',     '🍽️', 30),
('kafe',              'Kafe',                         'yiyecek_icecek',     '☕', 31),
('pastane',           'Pastane',                      'yiyecek_icecek',     '🎂', 32),
-- Ev Hizmetleri
('hali_yikama',       'Halı Yıkama',                  'ev_hizmetleri',      '🧺', 40),
('kuru_temizleme',    'Kuru Temizleme',                'ev_hizmetleri',      '👔', 41),
('ev_tamircisi',      'Ev Tamircisi / Usta',           'ev_hizmetleri',      '🔧', 42),
('pvc_cam_usta',      'PVC / Cam Ustası',              'ev_hizmetleri',      '🪟', 43),
('mobilya_tamiri',    'Mobilya Tamiri',                'ev_hizmetleri',      '🛋️', 44),
('bahce_bakim',       'Bahçe Bakım Hizmeti',           'ev_hizmetleri',      '🌿', 45),
-- Araç
('arac_kiralama',     'Araç Kiralama',                 'arac_tasima',        '🚗', 50),
('oto_servis',        'Oto Servis / Tamirci',          'arac_tasima',        '🔧', 51),
('arac_yikama',       'Araç Yıkama',                   'arac_tasima',        '🚿', 52),
('lastikci',          'Lastikçi',                      'arac_tasima',        '🛞', 53),
('ozel_sofor',        'Özel Şoför / Transfer',         'arac_tasima',        '🚐', 54),
-- Enerji
('su_bayii',          'Su Bayii',                      'enerji_temel',       '💧', 60),
('tup_gaz_bayii',     'Tüp Gaz Bayii',                 'enerji_temel',       '🔥', 61),
('elektrikci',        'Elektrikçi',                    'enerji_temel',       '⚡', 62),
('tesisatci',         'Tesisatçı',                     'enerji_temel',       '🔩', 63),
('isitma_klima',      'Isıtma / Klima Servis',         'enerji_temel',       '🌡️', 64),
-- Eğitim
('ozel_ders',         'Özel Ders / Etüt',              'egitim_danismanlik', '📚', 70),
('muzik_okulu',       'Müzik Okulu',                   'egitim_danismanlik', '🎵', 71),
('avukatlik',         'Avukatlık / Hukuk',             'egitim_danismanlik', '⚖️', 72),
('muhasebe',          'Muhasebe / Mali Müşavir',       'egitim_danismanlik', '💼', 73),
('emlak',             'Emlak Danışmanlığı',             'egitim_danismanlik', '🏠', 74),
-- Özel
('fotograf_studyo',   'Fotoğraf / Video Stüdyo',       'ozel_hizmetler',     '📸', 80),
('evcil_hayvan',      'Evcil Hayvan Bakımevi',         'ozel_hizmetler',     '🐕', 81),
('organizasyon',      'Organizasyon / Etkinlik',       'ozel_hizmetler',     '🎉', 82),
('matbaa',            'Baskı / Matbaa',                'ozel_hizmetler',     '🖨️', 83),
('ozel_sablon',       'Özel / Diğer',                  'ozel_hizmetler',     '⚙️', 99)
ON CONFLICT DO NOTHING;


-- ── FİRMA ENTEGRASYON AYARLARI ŞABLONU ───────────────────────
-- Her firma şemasında bu tablo oluşturulur (template_engine.py tarafından)
-- CREATE TABLE {schema}.entegrasyon_ayarlari (
--     id SERIAL PRIMARY KEY,
--     tur VARCHAR(50) NOT NULL,
--     anahtar VARCHAR(100) NOT NULL,
--     deger TEXT,           -- AES-256-GCM şifreli
--     sifirli BOOLEAN DEFAULT FALSE,
--     aciklama VARCHAR(200),
--     guncelleme TIMESTAMP DEFAULT NOW(),
--     UNIQUE(tur, anahtar)
-- );
--
-- Firma entegrasyon kategorileri:
-- sip_numarasi | pms_api | crm_api | calendar_google |
-- calendar_outlook | webhook | ozel_api
