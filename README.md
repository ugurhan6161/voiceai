# 🎙️ VoiceAI Platform

Türkiye'nin ilk yerli, açık kaynaklı, KVKK uyumlu **yapay zeka sesli resepsiyonist** SaaS platformu.

> **Vapi'nin açık kaynaklı alternatifi** — Tüm AI servisleri ücretsiz ve yerel (API anahtarı gerekmez!)

[![Docker Ready](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Lisans: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Türkçe](https://img.shields.io/badge/dil-T%C3%BCrk%C3%A7e-red.svg)]()

---

## 🚀 Tek Komutla Kurulum (VPS)

```bash
# Ubuntu 22.04 LTS — Tek komutla her şeyi kur:
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh | sudo bash
```

> ⏱️ İlk kurulum ~15-20 dakika sürer (Docker image build + model indirme).
> Kurulum tamamlandığında **tüm servisler çalışır durumda** olacaktır.

### Kurulum Ne Yapar?

| Adım | İşlem | Otomatik |
|------|-------|:--------:|
| 1 | Sistem güncelleme + temel paketler | ✅ |
| 2 | Docker + Docker Compose v2 | ✅ |
| 3 | UFW güvenlik duvarı | ✅ |
| 4 | Fail2ban (SSH + SIP koruması) | ✅ |
| 5 | SSH güvenlik sıkılaştırma | ✅ |
| 6 | Otomatik güvenlik güncellemeleri | ✅ |
| 7 | Proje klonlama | ✅ |
| 8 | .env otomatik yapılandırma + güvenli şifre üretimi | ✅ |
| 9 | SSL sertifikası (self-signed) | ✅ |
| 10 | Asterisk PBX kurulumu (native) | ✅ |
| 11 | 14 Docker servis başlatma | ✅ |
| 12 | Veritabanı şema yükleme | ✅ |
| 13 | LLM model indirme (llama3.1:8b) | ✅ |
| 14 | Sağlık kontrolleri | ✅ |

---

## 🎯 Özellikler

- 🇹🇷 **Türkçe öncelikli** — Varsayılan dil Türkçe, çok dilli destek (TR/EN/AR/RU)
- 🆓 **Tamamen ücretsiz AI** — Tüm modeller yerel, harici API gerekmez
- 📞 **40+ sektör şablonu** — Otel, klinik, halı yıkama, restoran ve daha fazlası
- 🏢 **Çok kiracılı** — Her firma kendi schema'sında izole
- 🔐 **AES-256-GCM şifreleme** — Tüm hassas veriler şifreli
- 📱 **Zoiper/SIP desteği** — Çağrı yönlendirme: telefon veya SIP uygulama
- 📊 **Tam izleme** — Prometheus + Grafana dashboard
- ⚖️ **KVKK uyumlu** — Ses kaydı yok, sadece şifreli transkript

---

## 🧠 AI Servisleri (Tümü Ücretsiz)

| Servis | Teknoloji | Dil Desteği | Maliyet |
|--------|-----------|-------------|---------|
| **STT** (Konuşma→Metin) | Faster-Whisper Turbo INT8 | 🇹🇷 Türkçe + 99 dil | Ücretsiz (yerel) |
| **LLM** (Yapay Zeka) | Ollama + llama3.1:8b | 🇹🇷 Türkçe + çok dilli | Ücretsiz (yerel) |
| **TTS** (Metin→Ses) | gTTS (Google TTS) | 🇹🇷 Türkçe + çok dilli | Ücretsiz |
| **RAG** (Belge Arama) | ChromaDB | Tüm diller | Ücretsiz (yerel) |

> 💡 Harici API anahtarı gerekmez! Tüm AI modelleri VPS'inizde yerel çalışır.

---

## 📁 Proje Yapısı

```
voiceai/
├── docker-compose.yml → Ana servis orkestrasyonu (14 servis)
├── .env.example       → Ortam değişkenleri şablonu
├── scripts/
│   ├── setup.sh       → Tek komutla VPS kurulumu
│   ├── cleanup.sh     → Güvenli temizlik
│   ├── backup.sh      → Otomatik yedekleme
│   └── health_check.sh → Sağlık kontrolü
├── ai-engine/         → STT + LLM + TTS + LiveKit Agent
│   └── templates/     → 41 sektör şablonu (9 kategori)
├── backend/           → FastAPI REST API
├── frontend/          → Next.js 14 Admin/Firma paneli
├── asterisk/          → Telefoni (SIP/ARI/PJSIP)
├── database/          → PostgreSQL şemaları
├── nginx/             → Reverse proxy + SSL
└── monitoring/        → Prometheus + Grafana
```

---

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| STT | Faster-Whisper Turbo INT8 |
| LLM | Ollama llama3.1:8b |
| TTS | gTTS / XTTS-v2 |
| Gerçek Zamanlı Ses | LiveKit Agents v1 |
| Telefoni | Asterisk 20 / PJSIP / ARI |
| Backend | FastAPI Python 3.11 |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Veritabanı | PostgreSQL 16 (multi-tenant) |
| Cache/Kuyruk | Redis 7 + Celery |
| Vektör DB | ChromaDB (RAG) |
| Şifreleme | AES-256-GCM |
| İzleme | Prometheus + Grafana |
| Proxy | Nginx + SSL |

---

## 🌐 Erişim

Kurulum tamamlandığında:

| Servis | URL |
|--------|-----|
| Admin Panel | `http://<VPS_IP>/admin/login` |
| Firma Panel | `http://<VPS_IP>/firma/login` |
| API Docs | `http://<VPS_IP>/api/docs` |
| Grafana | `http://<VPS_IP>:3000` |

**Varsayılan Admin Girişi:**
- Email: `admin@voiceai.com`
- Şifre: `Admin2026!`
- ⚠️ İlk girişten sonra şifreyi değiştirin!

---

## 📞 Sektör Şablonları (41 Adet)

| Kategori | Şablonlar |
|----------|-----------|
| 🏥 Sağlık (7) | Klinik, Diş, Veteriner, Fizik Tedavi, Psikolog, Spa, Eczane |
| 🏨 Konaklama (4) | Otel, Pansiyon, Tekne/Yat, Kamp |
| 🏠 Ev Hizmetleri (6) | Halı Yıkama, Kuru Temizleme, Bahçe, Tamirci, Mobilya, PVC |
| ⚡ Enerji (4) | Su/Tüp Bayii, Elektrikçi, Tesisatçı, Klima |
| 🚗 Araç (5) | Kiralama, Yıkama, Servis, Lastikçi, Özel Şoför |
| 📚 Eğitim (5) | Avukat, Emlak, Muhasebe, Müzik Okulu, Özel Ders |
| 💇 Kişisel Bakım (4) | Güzellik, Epilasyon, Kuaför, Spor Salonu |
| 🎉 Özel Hizmetler (10) | Düğün, Fotoğraf, Nakliyat, Sigorta, Evcil Hayvan, Matbaa... |
| 🍽️ Yiyecek/İçecek (4) | Restoran, Kafe, Pastane, Catering |

---

## 🔧 Faydalı Komutlar

```bash
# Servislerin durumunu gör
docker compose -f /opt/voiceai/docker-compose.yml ps

# Logları izle
docker compose -f /opt/voiceai/docker-compose.yml logs -f

# Belirli bir servisin logunu gör
docker compose -f /opt/voiceai/docker-compose.yml logs -f backend

# Sağlık kontrolü
bash /opt/voiceai/scripts/health_check.sh

# Yedek al
bash /opt/voiceai/scripts/backup.sh

# Güncelleme
cd /opt/voiceai && git pull && docker compose up -d --build

# Temizlik (kaldırma)
sudo bash /opt/voiceai/scripts/cleanup.sh
```

---

## 📖 Dokümantasyon

- [INSTALL.md](./INSTALL.md) — Detaylı kurulum rehberi
- [USER_GUIDE.md](./USER_GUIDE.md) — Kullanıcı kılavuzu
- [PROGRESS.md](./PROGRESS.md) — Geliştirme ilerlemesi

---

## 📄 Lisans

MIT License — Ticari kullanım serbesttir.
