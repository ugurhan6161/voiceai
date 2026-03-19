# 🎙️ Dograh AI — Türkçe Sesli Asistan Platformu

**Vapi'nin açık kaynaklı alternatifi** — Sürükle-bırak iş akışı oluşturucu ile kendi sesli AI asistanlarınızı oluşturun.

[![Docker Ready](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Lisans: BSD 2-Clause](https://img.shields.io/badge/license-BSD%202--Clause-blue.svg)](https://github.com/dograh-hq/dograh/blob/main/LICENSE)
[![Türkçe](https://img.shields.io/badge/dil-T%C3%BCrk%C3%A7e-red.svg)]()

> Bu repo, [Dograh AI](https://github.com/dograh-hq/dograh) platformunun **Türkçe dil desteği ve
> VPS tek komut kurulumu** için özelleştirilmiş sürümüdür.

---

## 🚀 Tek Komutla VPS Kurulumu

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/setup.sh | sudo bash
```

> ⏱️ İlk kurulum ~5 dakika sürer (Docker image indirme).
> Tamamlandığında dashboard **http://VPS_IP:3010** adresinde erişime açılır.

### Yerel Bilgisayarda (Geliştirme)

```bash
# Docker Compose ile tek komut:
curl -o docker-compose.yaml https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/docker-compose.yaml && \
  REGISTRY=ghcr.io/dograh-hq ENABLE_TELEMETRY=false docker compose up --pull always
```

Dashboard: [http://localhost:3010](http://localhost:3010)

---

## 🎯 Özellikler

- 🆓 **API anahtarı gerekmez** — Dograh kendi API anahtarlarını otomatik üretir
- 🎙️ **Sürükle-bırak** iş akışı oluşturucu ile sesli bot tasarımı
- 📞 **Telefon entegrasyonu** — Twilio, Vonage, Vobiz, Cloudonix
- 🤖 **AI Test Personas** — LoopTalk ile gerçek müşteri simülasyonu
- 🔄 **Esnek entegrasyon** — Kendi LLM, TTS veya STT modelinizi kullanın
- 🔓 **100% açık kaynak** — Vendor lock-in yok
- 🇹🇷 **Türkçe kurulum** — Tüm dokümantasyon ve kurulum Türkçe

---

## 📋 Kurulum Ne Yapar?

| Adım | İşlem | Otomatik |
|------|-------|:--------:|
| 1 | Docker + Docker Compose kurulumu | ✅ |
| 2 | UFW güvenlik duvarı | ✅ |
| 3 | Proje dosyalarını indir | ✅ |
| 4 | .env güvenli şifre üretimi | ✅ |
| 5 | SSL sertifikası (self-signed) | ✅ |
| 6 | Tüm servisleri başlat | ✅ |
| 7 | Sağlık kontrolü | ✅ |

---

## 🏗️ Servisler

| Servis | Teknoloji | Port | Açıklama |
|--------|-----------|------|----------|
| **Dashboard** | Next.js | 3010 | Web arayüzü |
| **API** | FastAPI (Python) | 8000 | Backend REST API |
| **PostgreSQL** | pgvector/pg17 | 5432 | Veritabanı + vektör arama |
| **Redis** | Redis 7 | 6379 | Cache + kuyruk |
| **MinIO** | MinIO | 9000/9001 | Ses dosyaları depolama |
| **Cloudflared** | Cloudflare Tunnel | 2000 | Dış erişim tüneli |
| **Nginx** | Nginx Alpine | 80/443 | Reverse proxy (VPS) |
| **CoTURN** | CoTURN 4.8 | 3478 | WebRTC NAT geçişi (VPS) |

---

## 🎙️ İlk Sesli Asistanınız (2 Dakikada)

1. **Dashboard'u açın**: `http://VPS_IP:3010`
2. **Çağrı türü seçin**: Inbound veya Outbound
3. **Bot adı verin**: Kısa iki kelime (örn: *Müşteri Hizmetleri*)
4. **Kullanım amacı yazın**: 5-10 kelime (örn: *Randevu alma ve bilgi verme*)
5. **Başlatın**: Bot hazır! **Web Call** ile test edin.
6. **API anahtarı gerekmez**: Dograh otomatik üretir, istediğiniz zaman kendi anahtarlarınızı ekleyebilirsiniz.

---

## 🔧 Faydalı Komutlar

```bash
# Kurulum dizinine git
cd /opt/dograh

# Servislerin durumunu gör
docker compose --profile remote ps

# Logları izle
docker compose --profile remote logs -f

# Belirli bir servisin logunu gör
docker compose --profile remote logs -f api

# Servisleri yeniden başlat
docker compose --profile remote restart

# Servisleri durdur
docker compose --profile remote down

# Servisleri güncelle
docker compose --profile remote up -d --pull always

# Temiz kaldırma (veriler dahil)
docker compose --profile remote down --volumes
```

---

## 🌐 Kendi API Anahtarlarınızı Kullanma

Dograh varsayılan olarak kendi ücretsiz API'lerini kullanır. İsterseniz kendi API anahtarlarınızı da ekleyebilirsiniz:

| Servis | Desteklenen Sağlayıcılar |
|--------|-------------------------|
| **LLM** | OpenAI, Anthropic, Google, Groq, OpenRouter |
| **TTS** | ElevenLabs, PlayHT, Azure, Deepgram |
| **STT** | Deepgram, AssemblyAI, Google, Azure |
| **Telefon** | Twilio, Vonage, Vobiz, Cloudonix |

API anahtarlarını dashboard üzerinden ekleyebilirsiniz.

---

## 🔐 Güvenlik

- Tüm şifreler kurulumda otomatik üretilir
- SSL sertifikası otomatik oluşturulur
- UFW güvenlik duvarı aktif
- Telemetri varsayılan olarak kapalı
- Tüm veriler kendi sunucunuzda

### Let's Encrypt SSL (Domain Varsa)

```bash
apt install -y certbot
certbot certonly --standalone -d alan-adi.com

# Sertifikaları kopyala
cp /etc/letsencrypt/live/alan-adi.com/fullchain.pem /opt/dograh/certs/
cp /etc/letsencrypt/live/alan-adi.com/privkey.pem /opt/dograh/certs/

# Nginx'i yeniden başlat
docker compose --profile remote restart nginx
```

---

## 📁 Dosya Yapısı

```
dograh-turkish/
├── docker-compose.yaml  → Servis orkestrasyonu
├── setup.sh             → Tek komut VPS kurulumu
├── .env                 → Ortam değişkenleri
├── nginx.conf           → Reverse proxy
├── turnserver.conf      → TURN server (WebRTC)
├── README.md            → Bu dosya (Türkçe)
└── KURULUM.md           → Detaylı kurulum rehberi
```

---

## 🔗 Bağlantılar

- [Dograh Resmi Repo](https://github.com/dograh-hq/dograh)
- [Dograh Dokümantasyon](https://docs.dograh.com)
- [Dograh Cloud](https://app.dograh.com)
- [Dograh Slack](https://join.slack.com/t/dograh-community/shared_invite/zt-3czr47sw5-MSg1J0kJ7IMPOCHF~03auQ)

---

## 📄 Lisans

Bu repo [BSD 2-Clause License](https://github.com/dograh-hq/dograh/blob/main/LICENSE) ile lisanslanmıştır.
Dograh AI'ın orijinal lisansı korunmuştur.
