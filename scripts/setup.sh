#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — VPS İlk Kurulum Scripti
#  Kullanım: sudo bash scripts/setup.sh
#  Ubuntu 22.04 LTS üzerinde çalışır
# ─────────────────────────────────────────────────────────────

set -e  # Hata olursa dur

# ── Etkileşimli dialog'ları devre dışı bırak ──────────────
# apt/dpkg kurulumlarında "Pending kernel upgrade" gibi
# ncurses dialog'larının çıkmasını engeller.
export DEBIAN_FRONTEND=noninteractive
# needrestart: çekirdek/servis yeniden başlatma dialog'unu bastırır
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

REPO_URL="${REPO_URL:-https://github.com/ugurhan6161/voiceai.git}"
INSTALL_DIR="/opt/voiceai"

echo "🚀 VoiceAI Platform VPS Kurulumu Başlıyor..."
echo "================================================"

# ── 1. Sistem Güncellemesi ─────────────────────────────────
echo "📦 [1/10] Sistem güncelleniyor..."
apt-get update -q && apt-get upgrade -y -q
apt-get install -y -q curl wget git unzip htop net-tools ufw fail2ban python3

# ── 2. Docker Kurulumu ─────────────────────────────────────
echo "🐳 [2/10] Docker kuruluyor..."
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sh /tmp/get-docker.sh
rm /tmp/get-docker.sh
systemctl enable docker
systemctl start docker

# Docker Compose v2 (plugin)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

echo "✅ Docker $(docker --version)"
echo "✅ Docker Compose $(docker compose version)"

# ── 3. Güvenlik Duvarı ─────────────────────────────────────
echo "🔒 [3/10] Güvenlik duvarı yapılandırılıyor..."
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
echo "✅ UFW güvenlik duvarı aktif"

# ── 4. Fail2ban ─────────────────────────────────────────────
echo "🛡️ [4/10] Fail2ban yapılandırılıyor..."
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
echo "✅ Fail2ban aktif"

# ── 5. SSH Güvenliği ────────────────────────────────────────
echo "🔑 [5/10] SSH güvenliği sıkılaştırılıyor..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
echo "✅ SSH: Root login kapalı"

# ── 6. Otomatik Güncellemeler ───────────────────────────────
echo "🔄 [6/10] Otomatik güvenlik güncellemeleri aktif ediliyor..."
apt-get install -y -q unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades
echo "✅ Otomatik güncellemeler aktif"

# ── 7. Proje Klonlama ───────────────────────────────────────
echo "📁 [7/10] Proje klonlanıyor: $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "ℹ️  Proje zaten var — güncelleniyor..."
    cd "$INSTALL_DIR" && git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── 8. Ortam Değişkenleri ───────────────────────────────────
echo "⚙️ [8/10] .env dosyası hazırlanıyor..."
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

    sed -i "s|APP_SECRET_KEY=.*|APP_SECRET_KEY=$APP_SECRET|" .env
    sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENC_KEY|" .env
    sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_KEY|" .env
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$PG_PASS|" .env
    sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASS|" .env
    sed -i "s|LIVEKIT_API_KEY=.*|LIVEKIT_API_KEY=$LK_KEY|" .env
    sed -i "s|LIVEKIT_API_SECRET=.*|LIVEKIT_API_SECRET=$LK_SECRET|" .env

    echo "✅ .env oluşturuldu — lütfen düzenleyin: nano $INSTALL_DIR/.env"
else
    echo "ℹ️  .env zaten var — atlanıyor"
fi

# ── 9. SSL Sertifikası (Self-Signed) ───────────────────────
echo "🔐 [9/10] SSL sertifikası hazırlanıyor..."
mkdir -p "$INSTALL_DIR/nginx/ssl"
if [ ! -f "$INSTALL_DIR/nginx/ssl/fullchain.pem" ]; then
    VPS_IP=$(curl -s ifconfig.me || echo "31.57.77.166")
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$INSTALL_DIR/nginx/ssl/privkey.pem" \
      -out    "$INSTALL_DIR/nginx/ssl/fullchain.pem" \
      -subj "/C=TR/ST=Istanbul/L=Istanbul/O=VoiceAI/CN=$VPS_IP"
    echo "✅ Self-signed SSL sertifikası oluşturuldu"
    echo "ℹ️  Domain'iniz varsa: certbot certonly --standalone -d yourdomain.com"
else
    echo "ℹ️  SSL sertifikası zaten var — atlanıyor"
fi

# ── 10. Docker Servisleri Başlat ────────────────────────────
echo "🚀 [10/10] Docker servisleri başlatılıyor..."
cd "$INSTALL_DIR"
docker compose up -d --build

echo ""
echo "================================================"
echo "✅ VoiceAI Platform Kurulumu Tamamlandı!"
echo "================================================"
echo ""
echo "📋 Sonraki Adımlar:"
echo ""
echo "1. Asterisk kur (native):"
echo "   apt install -y asterisk asterisk-pjsip asterisk-res-ari"
echo "   cp $INSTALL_DIR/asterisk/pjsip.conf /etc/asterisk/"
echo "   cp $INSTALL_DIR/asterisk/extensions.conf /etc/asterisk/"
echo "   cp $INSTALL_DIR/asterisk/ari.conf /etc/asterisk/"
echo "   cp $INSTALL_DIR/asterisk/http.conf /etc/asterisk/"
echo "   cp $INSTALL_DIR/asterisk/rtp.conf /etc/asterisk/"
echo "   cp $INSTALL_DIR/asterisk/modules.conf /etc/asterisk/"
echo "   systemctl enable asterisk && systemctl restart asterisk"
echo ""
echo "2. Ollama modelini indir (container hazır olduktan sonra):"
echo "   docker exec voiceai-ollama ollama pull llama3.1:8b"
echo ""
echo "3. Veritabanı şemalarını yükle:"
echo "   docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai < $INSTALL_DIR/database/settings_schema.sql"
echo "   docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai < $INSTALL_DIR/database/sip_dahili_schema.sql"
echo "   docker exec -i voiceai-postgres psql -U voiceai_user -d voiceai < $INSTALL_DIR/database/super_admin.sql"
echo ""
echo "4. Durumu kontrol et:"
echo "   docker compose -f $INSTALL_DIR/docker-compose.yml ps"
echo "   bash $INSTALL_DIR/scripts/health_check.sh"
echo ""
echo "🌐 Admin Panel: http://$(curl -s ifconfig.me 2>/dev/null || echo '31.57.77.166')/admin/login"
echo "   Email : admin@voiceai.com"
echo "   Şifre : Admin2026!"
echo ""
echo "📖 Tam kurulum rehberi: $INSTALL_DIR/INSTALL.md"
echo "================================================"
