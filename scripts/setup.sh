#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — Tek Komutla VPS Kurulumu
#  Kullanım: curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh | sudo bash
#  Ubuntu 22.04 LTS · 8 Çekirdek · 16 GB RAM · 100 GB NVMe
#
#  Tüm AI servisleri ücretsiz ve yereldir (API anahtarı gerekmez):
#    STT  → Faster-Whisper (Türkçe, ücretsiz, yerel)
#    LLM  → Ollama + llama3.1:8b (Türkçe destekli, ücretsiz, yerel)
#    TTS  → gTTS (Google Text-to-Speech, ücretsiz)
# ─────────────────────────────────────────────────────────────

set -e  # Hata olursa dur

REPO_URL="${REPO_URL:-https://github.com/ugurhan6161/voiceai.git}"
INSTALL_DIR="/opt/voiceai"
TOTAL_STEPS=14

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🎙️  VoiceAI Platform — Tek Komutla VPS Kurulumu         ║"
echo "║  Türkçe AI Sesli Resepsiyonist · Ücretsiz API'ler       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  STT : Faster-Whisper Turbo (Türkçe, ücretsiz, yerel)"
echo "  LLM : Ollama llama3.1:8b (Türkçe destekli, ücretsiz)"
echo "  TTS : gTTS (Türkçe, ücretsiz)"
echo "  Dil : Varsayılan Türkçe (TR/EN/AR/RU destekli)"
echo ""
echo "════════════════════════════════════════════════════════════"

# ── Yardımcı fonksiyonlar ─────────────────────────────────────
log_step() {
    local step=$1
    local msg=$2
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  [$step/$TOTAL_STEPS] $msg"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

detect_vps_ip() {
    local ip
    ip=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || true)
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 5 icanhazip.com 2>/dev/null || true)
    fi
    if [ -z "$ip" ]; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    if [ -z "$ip" ]; then
        echo ""
        return 1
    fi
    echo "$ip"
}

wait_for_container() {
    local container=$1
    local max_wait=${2:-120}
    local elapsed=0
    echo "  ⏳ $container container'ı bekleniyor..."
    while [ $elapsed -lt $max_wait ]; do
        if docker inspect --format='{{.State.Running}}' "$container" 2>/dev/null | grep -q "true"; then
            echo "  ✅ $container çalışıyor"
            return 0
        fi
        sleep 3
        elapsed=$((elapsed + 3))
    done
    echo "  ⚠️  $container başlatılamadı ($max_wait sn zaman aşımı)"
    return 1
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
    echo "  ⚠️  $container sağlık durumu: $status ($max_wait sn zaman aşımı)"
    return 1
}

# ── 1. Sistem Güncellemesi ─────────────────────────────────────
log_step 1 "📦 Sistem güncelleniyor ve temel paketler kuruluyor..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl wget git unzip htop net-tools ufw fail2ban \
    python3 openssl ca-certificates gnupg lsb-release
echo "  ✅ Sistem güncel, temel paketler kuruldu"

# ── 2. Docker Kurulumu ─────────────────────────────────────────
log_step 2 "🐳 Docker ve Docker Compose kuruluyor..."
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

# Docker Compose v2 (plugin)
if ! docker compose version &>/dev/null; then
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
    echo "  ✅ Docker Compose kuruldu: $(docker compose version)"
else
    echo "  ℹ️  Docker Compose zaten kurulu: $(docker compose version)"
fi

# ── 3. Güvenlik Duvarı (UFW) ──────────────────────────────────
log_step 3 "🔒 Güvenlik duvarı yapılandırılıyor..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp          # SSH
ufw allow 80/tcp          # HTTP
ufw allow 443/tcp         # HTTPS
ufw allow 5060/udp        # SIP
ufw allow 5061/tcp        # SIP-TLS
ufw allow 7880/tcp        # LiveKit HTTP/WS
ufw allow 7881/tcp        # LiveKit RTC TCP
ufw allow 7882/udp        # LiveKit RTC UDP
ufw allow 10000:20000/udp # RTP ses kanalları
ufw allow 50000:60000/udp # LiveKit RTP aralığı
# Docker → Asterisk ARI
ufw allow from 172.17.0.0/16 to any port 8088
ufw allow from 172.18.0.0/16 to any port 8088
ufw --force enable
echo "  ✅ UFW güvenlik duvarı aktif"

# ── 4. Fail2ban ────────────────────────────────────────────────
log_step 4 "🛡️ Fail2ban yapılandırılıyor..."
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
echo "  ✅ Fail2ban aktif (SSH + Asterisk koruması)"

# ── 5. SSH Güvenliği ───────────────────────────────────────────
log_step 5 "🔑 SSH güvenliği sıkılaştırılıyor..."
if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null || \
   grep -q "^#PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null; then
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl restart sshd 2>/dev/null || true
    echo "  ✅ SSH: Root login kapatıldı"
else
    echo "  ℹ️  SSH: Root login zaten kapalı veya yapılandırma farklı"
    echo "  ⚠️  Lütfen /etc/ssh/sshd_config dosyasını kontrol edin"
fi

# ── 6. Otomatik Güncellemeler ──────────────────────────────────
log_step 6 "🔄 Otomatik güvenlik güncellemeleri aktif ediliyor..."
apt-get install -y -qq unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' > /etc/apt/apt.conf.d/51voiceai-unattended
dpkg-reconfigure --priority=critical unattended-upgrades 2>/dev/null || true
echo "  ✅ Otomatik güvenlik güncellemeleri aktif"

# ── 7. Proje Klonlama ─────────────────────────────────────────
log_step 7 "📁 Proje klonlanıyor: $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  ℹ️  Proje zaten var — güncelleniyor..."
    cd "$INSTALL_DIR" && git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
echo "  ✅ Proje hazır: $INSTALL_DIR"

# ── 8. Ortam Değişkenleri (.env) ───────────────────────────────
log_step 8 "⚙️ Ortam değişkenleri (.env) hazırlanıyor..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"

    # Güvenli rastgele değerler üret
    APP_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ENC_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    JWT_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    PG_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
    REDIS_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    LK_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    LK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    GRAFANA_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

    # VPS IP'sini algıla
    VPS_IP=$(detect_vps_ip)
    if [ -z "$VPS_IP" ]; then
        echo "  ⚠️  VPS IP adresi algılanamadı — .env dosyasında APP_DOMAIN'i manuel düzenleyin"
        VPS_IP="VPS_IP_ADRESINIZ"
    fi

    sed -i "s|APP_SECRET_KEY=.*|APP_SECRET_KEY=$APP_SECRET|" .env
    sed -i "s|APP_DOMAIN=.*|APP_DOMAIN=$VPS_IP|" .env
    sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENC_KEY|" .env
    sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_KEY|" .env
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$PG_PASS|" .env
    sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASS|" .env
    sed -i "s|LIVEKIT_API_KEY=.*|LIVEKIT_API_KEY=$LK_KEY|" .env
    sed -i "s|LIVEKIT_API_SECRET=.*|LIVEKIT_API_SECRET=$LK_SECRET|" .env
    sed -i "s|GRAFANA_PASSWORD=.*|GRAFANA_PASSWORD=$GRAFANA_PASS|" .env

    echo "  ✅ .env oluşturuldu (tüm şifreler otomatik üretildi)"
else
    echo "  ℹ️  .env zaten var — atlanıyor"
fi

# ── 9. SSL Sertifikası (Self-Signed) ──────────────────────────
log_step 9 "🔐 SSL sertifikası hazırlanıyor..."
mkdir -p "$INSTALL_DIR/nginx/ssl"
if [ ! -f "$INSTALL_DIR/nginx/ssl/fullchain.pem" ]; then
    VPS_IP=$(detect_vps_ip)
    if [ -z "$VPS_IP" ]; then
        echo "  ⚠️  VPS IP algılanamadı — SSL sertifikası hostname ile oluşturulacak"
        VPS_IP=$(hostname -f 2>/dev/null || echo "voiceai-server")
    fi
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$INSTALL_DIR/nginx/ssl/privkey.pem" \
      -out    "$INSTALL_DIR/nginx/ssl/fullchain.pem" \
      -subj "/C=TR/ST=Istanbul/L=Istanbul/O=VoiceAI/CN=$VPS_IP" 2>/dev/null
    echo "  ✅ Self-signed SSL sertifikası oluşturuldu"
    echo "  ℹ️  Domain'iniz varsa: certbot certonly --standalone -d alan-adi.com"
else
    echo "  ℹ️  SSL sertifikası zaten var — atlanıyor"
fi

# ── 10. Asterisk Kurulumu (Native) ─────────────────────────────
log_step 10 "📞 Asterisk PBX kuruluyor (native)..."
if command -v asterisk &>/dev/null; then
    echo "  ℹ️  Asterisk zaten kurulu: $(asterisk -V)"
else
    apt-get install -y -qq asterisk
    echo "  ✅ Asterisk kuruldu"
fi

# Yapılandırma dosyalarını kopyala
echo "  📋 Asterisk yapılandırma dosyaları kopyalanıyor..."
cp "$INSTALL_DIR/asterisk/pjsip.conf"      /etc/asterisk/pjsip.conf
cp "$INSTALL_DIR/asterisk/extensions.conf"  /etc/asterisk/extensions.conf
cp "$INSTALL_DIR/asterisk/ari.conf"         /etc/asterisk/ari.conf
cp "$INSTALL_DIR/asterisk/http.conf"        /etc/asterisk/http.conf
cp "$INSTALL_DIR/asterisk/rtp.conf"         /etc/asterisk/rtp.conf
cp "$INSTALL_DIR/asterisk/modules.conf"     /etc/asterisk/modules.conf
cp "$INSTALL_DIR/asterisk/asterisk.conf"    /etc/asterisk/asterisk.conf

# Ses dosyaları dizini
mkdir -p /var/lib/asterisk/sounds/voiceai

# Asterisk başlat
systemctl enable asterisk
systemctl restart asterisk
echo "  ✅ Asterisk çalışıyor: $(asterisk -V 2>/dev/null || echo 'kurulu')"

# ── 11. Docker Servisleri Başlat ───────────────────────────────
log_step 11 "🚀 Docker servisleri başlatılıyor (14 servis)..."
cd "$INSTALL_DIR"
docker compose up -d --build

echo "  ⏳ Servisler başlatılıyor, lütfen bekleyin..."
sleep 10

# ── 12. PostgreSQL Sağlık Kontrolü + Şema Yükleme ─────────────
log_step 12 "🗄️ Veritabanı şemaları yükleniyor..."

# PostgreSQL'in sağlıklı olmasını bekle
wait_for_healthy "voiceai-postgres" 120

# Şemaları yükle
echo "  📋 Ek veritabanı şemaları yükleniyor..."
PG_USER=$(grep '^POSTGRES_USER=' "$INSTALL_DIR/.env" | cut -d= -f2)
PG_DB=$(grep '^POSTGRES_DB=' "$INSTALL_DIR/.env" | cut -d= -f2)
PG_USER="${PG_USER:-voiceai_user}"
PG_DB="${PG_DB:-voiceai}"

for schema_file in settings_schema.sql sip_dahili_schema.sql super_admin.sql; do
    if [ -f "$INSTALL_DIR/database/$schema_file" ]; then
        if docker exec -i voiceai-postgres psql -U "$PG_USER" -d "$PG_DB" \
          < "$INSTALL_DIR/database/$schema_file" >/dev/null 2>&1; then
            echo "  ✅ $schema_file yüklendi"
        else
            echo "  ℹ️  $schema_file atlandı (zaten yüklü olabilir)"
        fi
    fi
done

# Sektör şemalarını da yükle
for schema_file in otel_schema.sql klinik_schema.sql hali_yikama_schema.sql su_tup_schema.sql; do
    if [ -f "$INSTALL_DIR/database/$schema_file" ]; then
        if docker exec -i voiceai-postgres psql -U "$PG_USER" -d "$PG_DB" \
          < "$INSTALL_DIR/database/$schema_file" >/dev/null 2>&1; then
            echo "  ✅ $schema_file yüklendi"
        else
            echo "  ℹ️  $schema_file atlandı (zaten yüklü olabilir)"
        fi
    fi
done

echo "  ✅ Veritabanı hazır"

# ── 13. Ollama LLM Model İndirme ──────────────────────────────
log_step 13 "🧠 Türkçe destekli LLM modeli indiriliyor (llama3.1:8b)..."
echo "  ℹ️  Bu adım ilk kurulumda 5-15 dakika sürebilir..."

# Ollama container'ın çalışmasını bekle
wait_for_container "voiceai-ollama" 60

# Modeli indir
OLLAMA_MODEL=$(grep '^OLLAMA_MODEL=' "$INSTALL_DIR/.env" | cut -d= -f2)
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1:8b}"

echo "  📥 Model indiriliyor: $OLLAMA_MODEL"
docker exec voiceai-ollama ollama pull "$OLLAMA_MODEL" && \
    echo "  ✅ $OLLAMA_MODEL modeli indirildi (Türkçe destekli)" || \
    echo "  ⚠️  Model indirilemedi — sonra tekrar deneyin: docker exec voiceai-ollama ollama pull $OLLAMA_MODEL"

# ── 14. Sağlık Kontrolleri ─────────────────────────────────────
log_step 14 "🔍 Son sağlık kontrolleri yapılıyor..."

echo ""
echo "  Servis Durumları:"
echo "  ─────────────────"

# Container durumlarını kontrol et
SERVICES="voiceai-nginx voiceai-postgres voiceai-redis voiceai-ollama voiceai-whisper voiceai-xtts voiceai-ai-engine voiceai-livekit-agent voiceai-backend voiceai-celery voiceai-celery-beat voiceai-frontend voiceai-chromadb voiceai-livekit voiceai-prometheus voiceai-grafana"
RUNNING=0
TOTAL=0

for svc in $SERVICES; do
    TOTAL=$((TOTAL + 1))
    if docker inspect --format='{{.State.Running}}' "$svc" 2>/dev/null | grep -q "true"; then
        echo "  ✅ $svc"
        RUNNING=$((RUNNING + 1))
    else
        echo "  ❌ $svc (çalışmıyor)"
    fi
done

echo ""
echo "  Sonuç: $RUNNING / $TOTAL servis çalışıyor"

# Asterisk durumu
if systemctl is-active --quiet asterisk; then
    echo "  ✅ Asterisk PBX (native)"
else
    echo "  ❌ Asterisk PBX (çalışmıyor)"
fi

# ── Tamamlandı ─────────────────────────────────────────────────
VPS_IP=$(detect_vps_ip)
if [ -z "$VPS_IP" ]; then
    VPS_IP="<VPS_IP_ADRESINIZ>"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ VoiceAI Platform Kurulumu Tamamlandı!                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  🌐 Erişim Adresleri:"
echo "  ────────────────────"
echo "  Admin Panel  : http://$VPS_IP/admin/login"
echo "  Firma Panel  : http://$VPS_IP/firma/login"
echo "  API Docs     : http://$VPS_IP/api/docs"
echo "  Grafana      : http://$VPS_IP:3000"
echo ""
echo "  🔑 Varsayılan Admin Girişi:"
echo "  ────────────────────────────"
echo "  Email : admin@voiceai.com"
echo "  Şifre : Admin2026!"
echo "  ⚠️  İlk girişten sonra şifreyi değiştirin!"
echo ""
echo "  🎙️ AI Servisleri (Tümü Ücretsiz):"
echo "  ───────────────────────────────────"
echo "  STT : Faster-Whisper Turbo INT8 (Türkçe)"
echo "  LLM : Ollama $OLLAMA_MODEL (Türkçe destekli)"
echo "  TTS : gTTS (Türkçe)"
echo "  Dil : Varsayılan Türkçe"
echo ""
echo "  📋 Faydalı Komutlar:"
echo "  ─────────────────────"
echo "  docker compose -f $INSTALL_DIR/docker-compose.yml ps"
echo "  docker compose -f $INSTALL_DIR/docker-compose.yml logs -f"
echo "  bash $INSTALL_DIR/scripts/health_check.sh"
echo ""
echo "  📖 Dokümantasyon: $INSTALL_DIR/INSTALL.md"
echo "  📖 Kullanım     : $INSTALL_DIR/USER_GUIDE.md"
echo ""
echo "════════════════════════════════════════════════════════════"
