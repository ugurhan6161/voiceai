#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Dograh AI — Türkçe Sesli Asistan Platformu
#  Tek Komutla VPS Kurulum Scripti
#
#  Kullanım:
#    curl -fsSL https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/setup.sh | sudo bash
#
#  Veya:
#    sudo bash setup.sh
#
#  Gereksinimler: Ubuntu 22.04+ · 4+ GB RAM · Docker
#
#  Ne yapar:
#    1. Docker & Docker Compose kurulumu (yoksa)
#    2. Güvenlik duvarı (UFW) yapılandırması
#    3. Proje dosyalarını indirir/klonlar
#    4. Güvenli .env oluşturur
#    5. SSL sertifikası hazırlar (self-signed)
#    6. Tüm servisleri başlatır (remote profil)
#    7. Sağlık kontrolü yapar
#
#  Dograh varsayılan olarak kendi ücretsiz API anahtarlarını
#  otomatik üretir — harici API key gerekmez!
# ─────────────────────────────────────────────────────────────

set -e

# ── Yapılandırma ──────────────────────────────────────────────
REPO_URL="${REPO_URL:-https://github.com/ugurhan6161/dograh-turkish.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/dograh}"
TOTAL_STEPS=7

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🎙️  Dograh AI — Türkçe Sesli Asistan Platformu          ║"
echo "║  Açık kaynaklı Vapi alternatifi · Tek komut kurulum      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  📍 Kurulum dizini : $INSTALL_DIR"
echo "  🐳 Docker profili : remote (VPS)"
echo "  🔒 Telemetri      : Kapalı"
echo ""
echo "════════════════════════════════════════════════════════════"

# ── Yardımcı Fonksiyonlar ─────────────────────────────────────
log_step() {
    local step=$1
    local msg=$2
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  [$step/$TOTAL_STEPS] $msg"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

detect_ip() {
    local ip
    ip=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || true)
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 5 icanhazip.com 2>/dev/null || true)
    fi
    if [ -z "$ip" ]; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    echo "$ip"
}

wait_for_healthy() {
    local container=$1
    local max_wait=${2:-180}
    local elapsed=0
    echo "  ⏳ $container sağlık kontrolü bekleniyor..."
    while [ $elapsed -lt $max_wait ]; do
        local status
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        if [ "$status" = "healthy" ]; then
            echo "  ✅ $container sağlıklı"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
    echo "  ⚠️  $container henüz sağlıklı değil (bekleme süresi: ${max_wait}s)"
    return 1
}

# ── 1. Docker Kurulumu ─────────────────────────────────────────
log_step 1 "🐳 Docker ve Docker Compose kuruluyor..."
export DEBIAN_FRONTEND=noninteractive

# Temel paketler
apt-get update -qq
apt-get install -y -qq curl wget git openssl ca-certificates ufw

if command -v docker &>/dev/null; then
    echo "  ℹ️  Docker zaten kurulu: $(docker --version)"
else
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo "  ✅ Docker kuruldu: $(docker --version)"
fi

if ! docker compose version &>/dev/null; then
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    echo "  ✅ Docker Compose kuruldu: $(docker compose version)"
else
    echo "  ℹ️  Docker Compose zaten kurulu: $(docker compose version)"
fi

# ── 2. Güvenlik Duvarı ────────────────────────────────────────
log_step 2 "🔒 Güvenlik duvarı (UFW) yapılandırılıyor..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp       # SSH
ufw allow 80/tcp       # HTTP
ufw allow 443/tcp      # HTTPS
ufw allow 3010/tcp     # Dograh Dashboard (direkt erişim)
ufw allow 8000/tcp     # Dograh API (direkt erişim)
ufw allow 3478/tcp     # TURN TCP
ufw allow 3478/udp     # TURN UDP
ufw allow 5349/tcp     # TURNS TCP
ufw allow 5349/udp     # TURNS UDP
ufw allow 49152:49200/udp  # TURN relay portları
ufw --force enable
echo "  ✅ UFW aktif"

# ── 3. Proje Dosyaları ────────────────────────────────────────
log_step 3 "📁 Proje dosyaları hazırlanıyor: $INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  ℹ️  Proje zaten var — güncelleniyor..."
    cd "$INSTALL_DIR" && git pull
else
    # Önce repo'yu klonlamayı dene, başarısız olursa dosyaları indir
    if git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null; then
        echo "  ✅ Repo klonlandı"
    else
        echo "  ℹ️  Repo klon başarısız — dosyalar doğrudan indiriliyor..."
        mkdir -p "$INSTALL_DIR"
        cd "$INSTALL_DIR"

        # docker-compose.yaml indir
        curl -fsSL "https://raw.githubusercontent.com/ugurhan6161/dograh-turkish/main/docker-compose.yaml" \
          -o docker-compose.yaml 2>/dev/null || \
        curl -fsSL "https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml" \
          -o docker-compose.yaml

        echo "  ✅ docker-compose.yaml indirildi"
    fi
fi
cd "$INSTALL_DIR"
echo "  ✅ Proje dizini: $INSTALL_DIR"

# ── 4. Ortam Değişkenleri ─────────────────────────────────────
log_step 4 "⚙️ Ortam değişkenleri (.env) hazırlanıyor..."

VPS_IP=$(detect_ip)
if [ -z "$VPS_IP" ]; then
    echo "  ⚠️  VPS IP algılanamadı — .env dosyasını manuel düzenleyin"
    VPS_IP="localhost"
fi

if [ ! -f "$INSTALL_DIR/.env" ] || [ "${FORCE_ENV:-false}" = "true" ]; then
    # Güvenli değerler üret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    PG_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || openssl rand -hex 16)
    REDIS_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(12))" 2>/dev/null || openssl rand -hex 12)
    MINIO_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || openssl rand -hex 16)
    TURN_SECRET_VAL=$(python3 -c "import secrets; print(secrets.token_hex(24))" 2>/dev/null || openssl rand -hex 24)

    cat > "$INSTALL_DIR/.env" << ENVEOF
# ─────────────────────────────────────────────────────────────
#  Dograh AI — Ortam Değişkenleri (Otomatik Üretildi)
#  Tarih: $(date +%Y-%m-%d\ %H:%M:%S)
#  VPS IP: $VPS_IP
# ─────────────────────────────────────────────────────────────

# Genel
ENVIRONMENT=production
REGISTRY=ghcr.io/dograh-hq

# Veritabanı
POSTGRES_PASSWORD=$PG_PASS

# Redis
REDIS_PASSWORD=$REDIS_PASS

# MinIO
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=$MINIO_PASS

# JWT
OSS_JWT_SECRET=$JWT_SECRET

# Backend URL
BACKEND_API_ENDPOINT=http://$VPS_IP:8000
BACKEND_URL=http://api:8000

# Telemetri (kapalı)
ENABLE_TELEMETRY=false

# FastAPI
FASTAPI_WORKERS=2

# TURN Server (WebRTC)
TURN_HOST=$VPS_IP
TURN_SECRET=$TURN_SECRET_VAL
ENVEOF

    # turnserver.conf güncelle (varsa)
    if [ -f "$INSTALL_DIR/turnserver.conf" ]; then
        sed -i "s|^# external-ip=.*|external-ip=$VPS_IP|" "$INSTALL_DIR/turnserver.conf"
        sed -i "s|^static-auth-secret=.*|static-auth-secret=$TURN_SECRET_VAL|" "$INSTALL_DIR/turnserver.conf"
    fi

    echo "  ✅ .env oluşturuldu (tüm şifreler otomatik üretildi)"
    echo "  ℹ️  VPS IP: $VPS_IP"
else
    echo "  ℹ️  .env zaten var — atlanıyor"
fi

# ── 5. SSL Sertifikası ────────────────────────────────────────
log_step 5 "🔐 SSL sertifikası hazırlanıyor..."
mkdir -p "$INSTALL_DIR/certs"

if [ ! -f "$INSTALL_DIR/certs/fullchain.pem" ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$INSTALL_DIR/certs/privkey.pem" \
      -out    "$INSTALL_DIR/certs/fullchain.pem" \
      -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Dograh/CN=$VPS_IP" 2>/dev/null
    echo "  ✅ Self-signed SSL sertifikası oluşturuldu"
    echo "  ℹ️  Domain'iniz varsa: certbot certonly --standalone -d alan-adi.com"
else
    echo "  ℹ️  SSL sertifikası zaten var — atlanıyor"
fi

# ── 6. Servisleri Başlat ──────────────────────────────────────
log_step 6 "🚀 Dograh servisleri başlatılıyor..."
cd "$INSTALL_DIR"

# Nginx config yoksa oluştur (remote profil için gerekli)
if [ ! -f "$INSTALL_DIR/nginx.conf" ]; then
    cat > "$INSTALL_DIR/nginx.conf" << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://ui:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /ws/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    client_max_body_size 50M;
}
NGINXEOF
fi

# turnserver.conf yoksa oluştur
if [ ! -f "$INSTALL_DIR/turnserver.conf" ]; then
    cat > "$INSTALL_DIR/turnserver.conf" << TURNEOF
listening-port=3478
tls-listening-port=5349
external-ip=$VPS_IP
min-port=49152
max-port=49200
use-auth-secret
static-auth-secret=$(grep '^TURN_SECRET=' "$INSTALL_DIR/.env" | cut -d= -f2)
realm=dograh.local
no-multicast-peers
no-cli
no-tlsv1
no-tlsv1_1
TURNEOF
fi

# Remote profil ile başlat (nginx + coturn dahil)
docker compose --profile remote up -d --pull always

echo "  ⏳ Servisler başlatılıyor, lütfen bekleyin..."
sleep 15

# ── 7. Sağlık Kontrolü ───────────────────────────────────────
log_step 7 "🔍 Sağlık kontrolleri yapılıyor..."

echo ""
echo "  Servis Durumları:"
echo "  ─────────────────"

SERVICES="dograh-postgres dograh-redis dograh-minio dograh-api dograh-ui dograh-cloudflared dograh-nginx dograh-coturn"
RUNNING=0
TOTAL=0

for svc in $SERVICES; do
    TOTAL=$((TOTAL + 1))
    if docker inspect --format='{{.State.Running}}' "$svc" 2>/dev/null | grep -q "true"; then
        echo "  ✅ $svc"
        RUNNING=$((RUNNING + 1))
    else
        echo "  ⏳ $svc (henüz başlamadı — birkaç dakika bekleyin)"
    fi
done

echo ""
echo "  Sonuç: $RUNNING / $TOTAL servis çalışıyor"

# API sağlık kontrolü
echo ""
echo "  API Sağlık Kontrolü:"
wait_for_healthy "dograh-api" 120 || true

# ── Tamamlandı ─────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ Dograh AI Kurulumu Tamamlandı!                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  🌐 Erişim Adresleri:"
echo "  ────────────────────"
echo "  Dashboard      : http://$VPS_IP:3010"
echo "  API            : http://$VPS_IP:8000"
echo "  API Docs       : http://$VPS_IP:8000/api/v1/docs"
echo "  HTTPS          : https://$VPS_IP (self-signed)"
echo ""
echo "  🎙️ İlk Sesli Asistanınızı Oluşturun:"
echo "  ─────────────────────────────────────"
echo "  1. http://$VPS_IP:3010 adresini tarayıcıda açın"
echo "  2. Inbound veya Outbound çağrı türü seçin"
echo "  3. Botunuza bir isim verin (örn: 'Müşteri Hizmetleri')"
echo "  4. Kullanım amacını yazın (örn: 'Randevu alma ve bilgi verme')"
echo "  5. Web Call ile test edin!"
echo ""
echo "  ℹ️  API anahtarı gerekmez — Dograh otomatik üretir!"
echo "  ℹ️  Kendi LLM/TTS/STT API anahtarlarınızı da ekleyebilirsiniz."
echo ""
echo "  📋 Faydalı Komutlar:"
echo "  ─────────────────────"
echo "  cd $INSTALL_DIR"
echo "  docker compose --profile remote ps"
echo "  docker compose --profile remote logs -f"
echo "  docker compose --profile remote restart"
echo "  docker compose --profile remote down"
echo ""
echo "  📖 Dokümantasyon: https://docs.dograh.com"
echo ""
echo "════════════════════════════════════════════════════════════"
