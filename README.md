# 🎙️ VoiceAI Platform

Türkiye'nin ilk yerli, açık kaynaklı, KVKK uyumlu yapay zeka sesli resepsiyonist SaaS platformu.

## 🚀 Hızlı Başlangıç

```bash
# 1. Repo'yu klonla
git clone https://github.com/ugurhan6161/voiceai.git
cd voiceai

# 2. Ortam değişkenlerini ayarla
cp .env.example .env
nano .env  # Değerleri doldur

# 3. Tüm servisleri başlat
docker-compose up -d

# 4. Durumu kontrol et
docker-compose ps
```

## 📁 Proje Yapısı

```
voiceai/
├── CLAUDE.md          → Claude AI bağlam dosyası
├── PROGRESS.md        → İlerleme günlüğü
├── SKILLS.md          → Claude skill tanımları
├── docker-compose.yml → Ana servis orkestrasyon
├── asterisk/          → Telefoni konfigürasyonları
├── ai-engine/         → STT + LLM + TTS motoru
├── backend/           → FastAPI REST API
├── frontend/          → Next.js Admin/Firma paneli
├── database/          → DB şemaları ve migrasyonlar
├── nginx/             → Reverse proxy konfigürasyonu
└── scripts/           → Kurulum ve bakım scriptleri
```

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| STT | Faster-Whisper Turbo INT8 |
| LLM | Turkish-Llama-3-8B-function-calling |
| TTS | XTTS-v2 |
| Telefoni | Asterisk 18+ / PJSIP |
| Backend | FastAPI (Python) |
| Frontend | Next.js 14 |
| Veritabanı | PostgreSQL 16 |

## 📖 Dokümantasyon

- [MVP Yol Haritası](./docs/MVP_YOL_HARITASI.md)
- [Kurulum Rehberi](./docs/KURULUM.md)
- [API Dokümantasyonu](./docs/API.md)
- [KVKK Uyumluluk](./docs/KVKK.md)

## 🤝 Claude ile Çalışma

Her yeni Claude konuşmasını şu şekilde başlat:

```
CLAUDE.md ve PROGRESS.md dosyalarımı paylaşıyorum:

[CLAUDE.md içeriğini yapıştır]
[PROGRESS.md içeriğini yapıştır]

Bugün yapmak istediğim: [GÖREV]
```

## 📄 Lisans

MIT License — Ticari kullanım serbesttir.
