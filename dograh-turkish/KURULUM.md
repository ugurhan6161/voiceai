# Dograh AI — Detaylı Türkçe Kurulum Rehberi

> Ubuntu 22.04+ · 4 GB RAM (minimum) · Docker

---

## 🚀 Yöntem 1: Tek Komutla Otomatik Kurulum (Önerilen)

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/setup.sh | sudo bash
```

Bu komut her şeyi otomatik yapar. Aşağıdaki adımları tek tek yapmanıza gerek yoktur.

---

## 📋 Yöntem 2: Adım Adım Manuel Kurulum

### 1. Docker Kurulumu

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker && sudo systemctl start docker

# Docker Compose v2
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Doğrula
docker --version
docker compose version
```

### 2. Proje Dosyalarını İndir

```bash
# Seçenek A: Git ile klonla
git clone https://github.com/ugurhan6161/dograh-turkish.git /opt/dograh
cd /opt/dograh

# Seçenek B: Sadece docker-compose.yaml indir
mkdir -p /opt/dograh && cd /opt/dograh
curl -o docker-compose.yaml https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/docker-compose.yaml
```

### 3. Ortam Değişkenlerini Ayarla

```bash
cd /opt/dograh
cp .env.example .env  # veya .env dosyasını oluştur
nano .env
```

**Mutlaka değiştirilmesi gerekenler (üretim ortamı):**

```bash
# Güvenli şifreler üret:
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)"
echo "REDIS_PASSWORD=$(openssl rand -hex 12)"
echo "MINIO_SECRET_KEY=$(openssl rand -hex 16)"
echo "OSS_JWT_SECRET=$(openssl rand -hex 32)"
echo "TURN_SECRET=$(openssl rand -hex 24)"
```

### 4. SSL Sertifikası

**Let's Encrypt (domain varsa — ÖNERİLEN):**

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d alan-adi.com

mkdir -p /opt/dograh/certs
cp /etc/letsencrypt/live/alan-adi.com/fullchain.pem /opt/dograh/certs/
cp /etc/letsencrypt/live/alan-adi.com/privkey.pem /opt/dograh/certs/
```

**Self-Signed (domain yoksa):**

```bash
VPS_IP=$(curl -s ifconfig.me)
mkdir -p /opt/dograh/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/dograh/certs/privkey.pem \
  -out /opt/dograh/certs/fullchain.pem \
  -subj "/C=TR/O=Dograh/CN=$VPS_IP"
```

### 5. Servisleri Başlat

```bash
cd /opt/dograh

# Yerel geliştirme:
docker compose up -d --pull always

# VPS uzak sunucu (nginx + TURN dahil):
docker compose --profile remote up -d --pull always
```

### 6. Kontrol Et

```bash
# Servis durumları
docker compose --profile remote ps

# API sağlık kontrolü
curl http://localhost:8000/api/v1/health

# Logları izle
docker compose --profile remote logs -f
```

---

## 🌐 Erişim Adresleri

| Servis | URL |
|--------|-----|
| Dashboard | `http://<VPS_IP>:3010` |
| API | `http://<VPS_IP>:8000` |
| API Docs | `http://<VPS_IP>:8000/api/v1/docs` |
| HTTPS | `https://<VPS_IP>` |
| MinIO Console | `http://localhost:9001` |

---

## 🔧 Güncelleme

```bash
cd /opt/dograh
docker compose --profile remote up -d --pull always
```

---

## 🗑️ Kaldırma

```bash
cd /opt/dograh

# Servisleri durdur (veriler korunur)
docker compose --profile remote down

# Servisleri durdur + verileri sil
docker compose --profile remote down --volumes

# Proje dizinini sil
rm -rf /opt/dograh
```

---

## 📋 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Dashboard açılmıyor | `docker compose --profile remote logs ui` kontrol edin |
| API 502/503 hatası | `docker compose --profile remote logs api` kontrol edin |
| WebRTC ses yok | TURN server aktif mi: `docker compose --profile remote logs coturn` |
| Yavaş başlangıç | İlk çalıştırma image indirme nedeniyle 2-5 dk sürebilir |
| Port çakışması | 3010, 8000, 5432 portlarının boş olduğunu doğrulayın |

---

## 📊 Minimum Sistem Gereksinimleri

| Kaynak | Minimum | Önerilen |
|--------|---------|----------|
| CPU | 2 çekirdek | 4+ çekirdek |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB |
| OS | Ubuntu 22.04 | Ubuntu 22.04/24.04 |
| Docker | 24+ | En son sürüm |
