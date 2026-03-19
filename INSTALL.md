# VoiceAI Platform — VPS Kurulum Rehberi

> Ubuntu 22.04 LTS · 8 Çekirdek · 16 GB RAM · 100 GB NVMe
>
> **Tüm AI servisleri ücretsiz** — API anahtarı gerekmez!

---

## 🚀 Hızlı Kurulum (Önerilen — Tek Komut)

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh | sudo bash
```

Bu komut aşağıdakilerin **tamamını otomatik** yapar:

| # | İşlem | Durum |
|---|-------|:-----:|
| 1 | Sistem güncelleme + temel paketler | ✅ Otomatik |
| 2 | Docker + Docker Compose v2 | ✅ Otomatik |
| 3 | UFW güvenlik duvarı | ✅ Otomatik |
| 4 | Fail2ban (SSH + SIP koruması) | ✅ Otomatik |
| 5 | SSH güvenlik sıkılaştırma | ✅ Otomatik |
| 6 | Otomatik güvenlik güncellemeleri | ✅ Otomatik |
| 7 | Proje klonlama | ✅ Otomatik |
| 8 | `.env` yapılandırma + güvenli şifre üretimi | ✅ Otomatik |
| 9 | SSL sertifikası (self-signed) | ✅ Otomatik |
| 10 | Asterisk PBX kurulumu (native) | ✅ Otomatik |
| 11 | 14 Docker servis başlatma | ✅ Otomatik |
| 12 | Veritabanı şema yükleme | ✅ Otomatik |
| 13 | LLM model indirme (llama3.1:8b) | ✅ Otomatik |
| 14 | Sağlık kontrolleri | ✅ Otomatik |

> ⏱️ İlk kurulum ~15-20 dakika sürer. Tamamlandığında tüm servisler çalışır durumda olacaktır.

### Ücretsiz AI Servisleri

| Servis | Teknoloji | Türkçe | Maliyet |
|--------|-----------|:------:|---------|
| STT (Konuşma→Metin) | Faster-Whisper Turbo INT8 | ✅ | Ücretsiz (yerel) |
| LLM (Yapay Zeka) | Ollama + llama3.1:8b | ✅ | Ücretsiz (yerel) |
| TTS (Metin→Ses) | gTTS | ✅ | Ücretsiz |
| RAG (Belge Arama) | ChromaDB | ✅ | Ücretsiz (yerel) |

---

## 📋 Adım Adım Kurulum (Manuel)

Tek komut yerine adım adım yapmak isterseniz aşağıdaki talimatları izleyin.

### 0. (İsteğe Bağlı) VPS'i Sıfırla — Temiz Kurulum İçin

Mevcut bir Ubuntu sunucusunu kurulumdan önce sıfırlamak istiyorsanız
aşağıdaki komutları çalıştırın. Bu adım **yeni / hiç kurulmamış** bir
sunucu için gerekli değildir.

```bash
# Scripti doğrudan çalıştır (proje klonlandıysa)
sudo bash /opt/voiceai/scripts/cleanup.sh

# Onay vermeden otomatik çalıştır (-y / --yes):
sudo bash /opt/voiceai/scripts/cleanup.sh --yes

# Derin temizlik — Docker ve Asterisk paketleri de kaldırılır (--full):
sudo bash /opt/voiceai/scripts/cleanup.sh --yes --full

# veya repoya gerek kalmadan (güvenlik için önce indirip inceleyin):
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/cleanup.sh \
  -o /tmp/cleanup.sh
less /tmp/cleanup.sh          # içeriği inceleyin
sudo bash /tmp/cleanup.sh
```

Script şunları yapar:

| Adım | İşlem |
|------|-------|
| 1 | Mevcut VoiceAI Docker servislerini durdurur ve kaldırır |
| 2 | Tüm Docker container / image / volume'larını temizler |
| 3 | Proje kurulum dizinini siler |
| 4 | Asterisk yapılandırmasını sıfırlar |
| 5 | Fail2ban `jail.local` kurallarını kaldırır |
| 6 | UFW kurallarını sıfırlar (SSH:22 açık kalır) |
| 7 | `apt` önbelleği ve geçici dosyaları temizler |

`--full` ile ek olarak Docker ve Asterisk paketleri de APT'tan kaldırılır.

> ⚠️ **Script varsayılan olarak onay sorar.** Otomatik mod için `--yes` kullanın.

---

### 1. VPS Hazırlığı ve Temel Paketler

```bash
# Root olarak giriş yap
apt update && apt upgrade -y
apt install -y curl wget git unzip htop net-tools ufw fail2ban
```

### 2. Docker Kurulumu

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
systemctl enable docker && systemctl start docker

# Docker Compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Eski alias (geriye dönük uyumluluk)
ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

docker --version
docker compose version
```

### 3. Güvenlik Duvarı (UFW)

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp        # SSH
ufw allow 80/tcp        # HTTP
ufw allow 443/tcp       # HTTPS
ufw allow 5060/udp      # SIP
ufw allow 5061/tcp      # SIP-TLS
ufw allow 7880/tcp      # LiveKit HTTP/WS
ufw allow 7881/tcp      # LiveKit RTC TCP
ufw allow 7882/udp      # LiveKit RTC UDP
ufw allow 10000:20000/udp  # RTP ses kanalları
ufw allow 50000:60000/udp  # LiveKit RTP aralığı

# Docker → Asterisk (ARI) — host ağına erişim
ufw allow from 172.17.0.0/16 to any port 8088
ufw allow from 172.18.0.0/16 to any port 8088

ufw --force enable
ufw status
```

### 4. Fail2ban

```bash
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
maxretry = 3

[asterisk]
enabled = true
port = 5060,5061
protocol = udp,tcp
maxretry = 5
EOF
systemctl restart fail2ban
```

### 5. Projeyi Klon'la

```bash
mkdir -p /opt/voiceai
cd /opt/voiceai
git clone https://github.com/ugurhan6161/voiceai.git .
```

### 6. Ortam Değişkenlerini Ayarla

```bash
cd /opt/voiceai
cp .env.example .env
nano .env   # veya: vi .env
```

**Mutlaka doldurulması gereken alanlar:**

```bash
# Güvenli rastgele değerler üret:
APP_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
LIVEKIT_API_KEY=$(openssl rand -hex 16)
LIVEKIT_API_SECRET=$(openssl rand -hex 32)

# Değerleri göster ve .env'e yapıştır:
echo "APP_SECRET_KEY=$APP_SECRET_KEY"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo "LIVEKIT_API_KEY=$LIVEKIT_API_KEY"
echo "LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET"
```

### 7. SSL Sertifikası

**Seçenek A — Let's Encrypt (Alan adı varsa, ÖNERİLEN)**

```bash
apt install -y certbot
certbot certonly --standalone -d yourdomain.com

mkdir -p /opt/voiceai/nginx/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/voiceai/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   /opt/voiceai/nginx/ssl/
```

**Seçenek B — Self-Signed (Domain yoksa / geliştirme)**

```bash
mkdir -p /opt/voiceai/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/voiceai/nginx/ssl/privkey.pem \
  -out    /opt/voiceai/nginx/ssl/fullchain.pem \
  -subj "/C=TR/ST=Istanbul/L=Istanbul/O=VoiceAI/CN=31.57.77.166"
```

### 8. Asterisk Kurulumu (VPS'e Native)

```bash
# Asterisk 20 LTS
apt install -y asterisk asterisk-pjsip asterisk-res-ari

# Yapılandırma dosyalarını kopyala
cp /opt/voiceai/asterisk/pjsip.conf      /etc/asterisk/pjsip.conf
cp /opt/voiceai/asterisk/extensions.conf /etc/asterisk/extensions.conf
cp /opt/voiceai/asterisk/ari.conf        /etc/asterisk/ari.conf
cp /opt/voiceai/asterisk/http.conf       /etc/asterisk/http.conf
cp /opt/voiceai/asterisk/rtp.conf        /etc/asterisk/rtp.conf
cp /opt/voiceai/asterisk/modules.conf    /etc/asterisk/modules.conf

# Ses dosyaları dizini
mkdir -p /var/lib/asterisk/sounds/voiceai

# Asterisk başlat
systemctl enable asterisk && systemctl restart asterisk
asterisk -rx "core show version"
```

### 9. Docker Servislerini Başlat

```bash
cd /opt/voiceai

# İlk çalıştırma (image build ~10-15 dk sürebilir)
docker compose up -d --build

# Durumu kontrol et
docker compose ps
docker compose logs -f --tail=50
```

### 10. Ollama LLM Modelini İndir

```bash
# Ollama container başladıktan sonra (1-2 dk bekle)
docker exec voiceai-ollama ollama pull llama3.1:8b

# Türkçe için önerilen alternatif:
# docker exec voiceai-ollama ollama pull atasoglu/Turkish-Llama-3-8B-function-calling

# Model listesi kontrol
docker exec voiceai-ollama ollama list
```

### 11. Veritabanını Başlat

```bash
# PostgreSQL otomatik init.sql çalıştırır.
# Ek şemalar için:
docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai \
  < /opt/voiceai/database/settings_schema.sql

docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai \
  < /opt/voiceai/database/sip_dahili_schema.sql

docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai \
  < /opt/voiceai/database/super_admin.sql
```

---

## 🔍 Sağlık Kontrolleri

```bash
# Tüm container'lar çalışıyor mu?
docker compose ps

# Backend API
curl http://localhost:8000/health

# AI Engine
curl http://localhost:8001/health

# Whisper STT
curl http://voiceai-whisper:9000/health   # container içinden
# veya: docker exec voiceai-whisper curl http://localhost:9000/health

# Ollama
curl http://localhost:11434/api/tags

# Otomasyon sağlık scripti
bash /opt/voiceai/scripts/health_check.sh
```

---

## 🌐 Erişim Adresleri

| Servis | URL |
|--------|-----|
| Admin Panel | `http://<VPS_IP>/admin/login` |
| Firma Panel | `http://<VPS_IP>/firma/login` |
| API Docs | `http://<VPS_IP>/api/docs` |
| Grafana | `http://<VPS_IP>:3000` |
| LiveKit | `ws://<VPS_IP>:7880` |

**Varsayılan Admin Girişi**
- Email: `admin@voiceai.com`
- Şifre: `Admin2026!` *(İlk girişten sonra değiştirin!)*

---

## 🔄 Güncelleme

```bash
cd /opt/voiceai
git pull
docker compose up -d --build
```

---

## 🔧 Yararlı Komutlar

```bash
# Logları izle
docker compose logs -f backend
docker compose logs -f ai-engine

# Container'ı yeniden başlat
docker compose restart backend

# Veritabanı yedeği al
bash /opt/voiceai/scripts/backup.sh

# XTTS IP'sini kontrol et (restart sonrası değişebilir)
docker inspect voiceai-xtts | grep IPAddress

# Şifreleme anahtarını döndür
python3 /opt/voiceai/scripts/rotate_encryption_key.py
```

---

## 📋 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Nginx SSL hatası | `nginx/ssl/` dizinini ve sertifika dosyalarını kontrol et |
| Ollama model yok | `docker exec voiceai-ollama ollama pull llama3.1:8b` çalıştır |
| DB bağlantı hatası | `.env` içindeki `POSTGRES_PASSWORD`'u kontrol et |
| Asterisk ARI 403 | `asterisk/ari.conf` içindeki kullanıcı/şifreyi `.env` ile eşleştir |
| XTTS IP değişti | `docker inspect voiceai-xtts \| grep IPAddress` ile yeni IP'yi bul |
| LiveKit bağlanamıyor | UFW'de port 7880-7882 açık mı kontrol et |

---

## 🚨 Cleanup Başarısız Olursa — Elle Temizlik ve VPS Format

### Seçenek A — Derin Temizlik (`--full`)

Standart `cleanup.sh` işe yaramadıysa önce `--full` modunu deneyin.
Bu seçenek Docker ve Asterisk paketlerini APT üzerinden tamamen kaldırır:

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/cleanup.sh \
  -o /tmp/cleanup.sh
sudo bash /tmp/cleanup.sh --yes --full
```

### Seçenek B — Elle Manuel Temizlik

Aşağıdaki komutları tek tek çalıştırın; her biri bağımsız çalışır:

```bash
# 1. Docker servislerini durdur ve sil
docker compose -f /opt/voiceai/docker-compose.yml down --volumes 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker system prune -af --volumes

# 2. Docker paketini kaldır
systemctl stop docker 2>/dev/null || true
apt-get purge -y docker-ce docker-ce-cli containerd.io \
    docker-compose-plugin docker-buildx-plugin 2>/dev/null || true
rm -rf /var/lib/docker /etc/docker /usr/local/lib/docker \
       /usr/local/bin/docker-compose 2>/dev/null || true

# 3. Asterisk'i kaldır
systemctl stop asterisk 2>/dev/null || true
apt-get purge -y asterisk asterisk-pjsip asterisk-res-ari 2>/dev/null || true
rm -rf /etc/asterisk /var/lib/asterisk /var/log/asterisk 2>/dev/null || true

# 4. VoiceAI dizinini sil
rm -rf /opt/voiceai

# 5. UFW sıfırla (SSH açık kalsın)
ufw --force reset && ufw allow 22/tcp && ufw --force enable

# 6. Fail2ban temizle
rm -f /etc/fail2ban/jail.local && systemctl restart fail2ban 2>/dev/null || true

# 7. Gereksiz paketleri temizle
apt-get autoremove -y && apt-get autoclean -y
```

### Seçenek C — VPS Format (Son Çare)

**Ne zaman gerekli?**
Format yalnızca aşağıdaki durumlarda düşünülmelidir:

- Sistemde bilinmeyen/kötü amaçlı yazılım bulunduğundan şüpheleniyorsanız
- Yukarıdaki tüm adımlar başarısız oldu ve sistem hâlâ kararsızsa
- İşletim sistemi dosyaları bozulmuş (kernel panic, boot başarısız vb.)

**Normal bir VoiceAI yeniden kurulumu için VPS format gerekmez.**
`--full` veya Seçenek B yeterlidir.

**Format sonrası kurulum:**

VPS sağlayıcı panelinizden **OS Reinstall → Ubuntu 22.04 LTS** seçin.
Yeni root şifresi alın, SSH ile bağlanın, ardından:

```bash
# Temiz sunucuda tek komutla kurulum:
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh \
  | sudo bash
```
