# VoiceAI Platform — Proje Bağlamı (CLAUDE.md) v2.0

> Bu dosyayı her yeni Claude konuşmasının başında yapıştır.
> PROGRESS.md dosyasını da yanına ekle.

---

## 🎯 Proje Nedir?

Türkiye'ye özel, VPS tabanlı, açık kaynaklı **çok kiracılı (multi-tenant)
yapay zeka sesli resepsiyonist SaaS platformu.**

- Netgsm / Verimor SIP trunk üzerinden gelen çağrıları karşılar
- Türkçe konuşur, anlar, rezervasyon / randevu / sipariş alır
- 40+ sektör şablonu — otel, klinik, halı yıkama, su bayii ve daha fazlası
- Tüm API anahtarları ve şifreler AES-256-GCM ile şifreli DB'de saklanır
- Panel üzerinden düzenlenebilir, "Test Et" butonu ile doğrulanabilir
- Faturalama, abonelik, SMS bildirimi tam otomatik
- Tüm veriler yerli VPS'de — KVKK uyumlu

---

## 🖥️ VPS

| Kaynak | Değer |
|--------|-------|
| CPU | 8 Çekirdek Xeon Platinum 8168 / Gold 6152 / E5 2699v4 |
| RAM | 16 GB DDR4 |
| Disk | 100 GB NVMe |
| Ağ | 10 Gbit |
| OS | Ubuntu 22.04 LTS |
| GPU | Yok — CPU INT8 optimizasyonu |

---

## 🧠 AI Stack

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| STT | Faster-Whisper Turbo INT8 | WER ~%7.7 Türkçe |
| LLM | Turkish-Llama-3-8B-function-calling Q4_K_M | Ollama |
| TTS | XTTS-v2 | Ses klonlama dahil |
| VAD | TEN VAD | 100ms barge-in |
| RAG | ChromaDB | Belge tabanlı eğitim |
| Pipeline | Pipecat + LangGraph | Slot filling |

## 🏗️ Altyapı Stack

| Katman | Teknoloji |
|--------|-----------|
| Telefoni | Asterisk 18+ PJSIP + ARI + AudioSocket |
| Backend | FastAPI Python 3.11+ async |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| DB | PostgreSQL 16 multi-tenant schema |
| Cache | Redis 7 |
| Kuyruk | Celery + Redis |
| Şifreleme | AES-256-GCM hassas veriler için |
| Fatura | Invoice Ninja OSS |
| Ödeme | iyzico |
| SMS | Netgsm / Verimor API |
| Konteyner | Docker Compose |
| Proxy | Nginx + Let's Encrypt |
| İzleme | Prometheus + Grafana |

---

## 🔐 Ayar ve API Yönetimi Mimarisi

### Temel Kural
`.env` sadece bootstrap içindir. Tüm operasyonel ayarlar
panel üzerinden düzenlenir ve şifreli DB'de saklanır.

### Şifreleme Akışı
```
Kullanıcı Panel'e yazar
        ↓
AES-256-GCM ile şifrele (crypto.py)
        ↓
PostgreSQL'e kaydet (shared.sistem_ayarlari veya firma_N.entegrasyon_ayarlari)
        ↓
Sistem kullanırken bellekte çöz (geçici, loglanmaz)
```

### Admin Panelden Yönetilen Sistem Ayarları
- SIP sağlayıcıları (Netgsm, Verimor, Twilio)
- SMS sağlayıcıları
- Ödeme sistemi (iyzico prod/sandbox)
- E-posta SMTP
- Yedekleme (rclone)
- Genel platform ayarları

### Firma Panelinden Yönetilen Entegrasyon Ayarları
- Telefon numarası ve SIP atama
- Dış sistem API (PMS, CRM, ERP)
- Google / Outlook Calendar (OAuth2)
- Webhook URL + secret
- Her ayarda "Test Et" butonu

---

## 🗂️ 40+ Şablon Kategorileri

### KONAKLAMA & TURİZM
`otel` `pansiyon_apart` `kamp_bungalov` `tekne_yat`

### SAĞLIK & KLİNİK
`klinik_poliklinik` `dis_klinigi` `goz_klinigi` `spa_masaj` `eczane` `veteriner`

### KİŞİSEL BAKIM & GÜZELLİK
`kuafor_berber` `guzellik_salonu` `epilasyon_lazer` `spor_salonu`

### YİYECEK & İÇECEK
`restoran` `kafe` `pastane`

### EV & YAŞAM HİZMETLERİ
`hali_yikama` `kuru_temizleme` `ev_tamircisi` `pvc_cam_usta` `mobilya_tamiri` `bahce_bakim`

### ARAÇ & TAŞIMACILIK
`arac_kiralama` `oto_servis` `arac_yikama` `lastikci` `ozel_sofor`

### ENERJİ & TEMEL HİZMETLER
`su_bayii` `tup_gaz_bayii` `elektrikci` `tesisatci` `isitma_klima`

### EĞİTİM & DANIŞMANLIK
`ozel_ders` `muzik_okulu` `avukatlik` `muhasebe` `emlak`

### ÖZEL HİZMETLER
`fotograf_studyo` `evcil_hayvan` `organizasyon` `matbaa` `ozel_sablon`

### Yeni Şablon Ekleme
1. `ai-engine/templates/{kategori}/{sablon_kodu}.py` oluştur
2. `ai-engine/templates/registry.py`'ye kaydet
3. `database/templates_schema.sql`'e DB şemasını ekle
4. Admin panelde yayınla

---

## 📁 Klasör Yapısı (Özet)

```
voiceai/
├── CLAUDE.md / PROGRESS.md / SKILLS.md / SESSION_TEMPLATES.md
├── docker-compose.yml / .env.example / .gitignore
├── asterisk/          — pjsip.conf, extensions.conf, ari.conf
├── ai-engine/         — STT, LLM, TTS, Pipecat pipeline, şablonlar
├── backend/           — FastAPI: auth, firmalar, ayarlar, fatura, sms
│   └── crypto.py      — AES-256-GCM şifreleme servisi
├── frontend/          — Next.js: admin panel + firma panel
│   └── components/settings/  — ApiKeyInput, TestButton
├── database/          — init.sql, settings_schema.sql, templates_schema.sql
├── nginx/ / monitoring/ / docs/
└── scripts/           — setup.sh, backup.sh, health_check.sh, rotate_key.sh
```

---

## 🏗️ Mimari Kararlar (Değiştirilemez)

1. PostgreSQL schema izolasyonu — firma başına ayrı schema
2. Asterisk ARI + AudioSocket — AGI kullanılmaz
3. Token streaming — ilk token gelince TTS başlar
4. Barge-in aktif — kullanıcı konuşursa TTS durur
5. Ses kaydı yok — sadece GZIP transkript + AI özeti
6. Hard-code yasak — tüm değerler DB veya .env'den
7. Docker zorunlu — direkt kurulum yapılmaz
8. AES-256-GCM zorunlu — tüm API anahtarları şifreli
9. Test butonu zorunlu — her entegrasyon ayarında olmalı
10. Şablon registry — yeni şablonlar registry.py'ye kayıt zorunlu

---

## 👥 Roller

| Yetki | Super Admin | Firma Admin | Kullanıcı |
|-------|:-----------:|:-----------:|:---------:|
| Sistem ayarları | ✅ | ❌ | ❌ |
| Şablon yönetimi | ✅ | ❌ | ❌ |
| Tüm firmaları gör | ✅ | ❌ | ❌ |
| Firma durdur/aktif | ✅ | ❌ | ❌ |
| Kendi entegrasyon | ✅ | ✅ | ❌ |
| Kendi API anahtarı | ✅ | ✅ | ❌ |
| Fatura görüntüle | Tümü | Kendi | ❌ |
| Raporlar | Tümü | Kendi | Kendi |

---

## ⚠️ Önemli Notlar

- `.env` bootstrap only — operasyonel ayarlar DB'de saklanır
- Her API ayarında "Test Et" butonu zorunlu
- Yeni şablon: registry.py + DB şeması + panel kaydı
- AES anahtarı rotasyonu: `scripts/rotate_encryption_key.sh`
- Değişiklik öncesi mevcut çalışan kodu korumak için sor

---

## 🔄 Bu Konuşmada Bana Söyle

1. Hangi fazdayız? (Faz 1-5)
2. Bugün ne yapacağız?
3. Aktif hata var mı?
4. PROGRESS.md'yi de yapıştır.
