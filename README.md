# 🎙️ VoiceAI Platform

Türkiye'nin ilk yerli, açık kaynaklı, KVKK uyumlu yapay zeka sesli resepsiyonist SaaS platformu.

## 🚀 Hızlı Başlangıç (VPS)

```bash
# Tek komutla kur (Ubuntu 22.04 LTS):
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh | sudo bash
```

Veya adım adım:

```bash
# 1. Repo'yu klonla
git clone https://github.com/ugurhan6161/voiceai.git /opt/voiceai
cd /opt/voiceai

# 2. Ortam değişkenlerini ayarla
cp .env.example .env
nano .env  # Değerleri doldur

# 3. SSL sertifikası oluştur
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem -out nginx/ssl/fullchain.pem \
  -subj "/C=TR/O=VoiceAI/CN=31.57.77.166"

# 4. Tüm servisleri başlat
docker compose up -d --build

# 5. Ollama modelini indir
docker exec voiceai-ollama ollama pull llama3.1:8b

# 6. Durumu kontrol et
docker compose ps
bash scripts/health_check.sh
```

> 📖 **Tam kurulum rehberi için:** [INSTALL.md](./INSTALL.md)

## 📁 Proje Yapısı

```
voiceai/
├── INSTALL.md         → Adım adım VPS kurulum rehberi
├── docker-compose.yml → Ana servis orkestrasyon (14 servis)
├── .env.example       → Ortam değişkenleri şablonu
├── asterisk/          → Telefoni konfigürasyonları (SIP/ARI)
├── ai-engine/         → STT + LLM + TTS + LiveKit Agent
├── backend/           → FastAPI REST API
├── frontend/          → Next.js 14 Admin/Firma paneli
├── database/          → PostgreSQL şemaları
├── nginx/             → Reverse proxy + SSL
├── monitoring/        → Prometheus + Grafana
└── scripts/           → Kurulum, yedekleme, bakım
```

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
| Şifreleme | AES-256-GCM |
| Ödeme | iyzico |
| SMS | Netgsm |

## 🌐 Erişim

| Servis | URL |
|--------|-----|
| Admin Panel | http://31.57.77.166/admin/login |
| Firma Panel | http://31.57.77.166/firma/login |
| API Docs | http://31.57.77.166/api/docs |

**Admin:** `admin@voiceai.com` / `Admin2026!`

## 📄 Lisans

MIT License — Ticari kullanım serbesttir.
