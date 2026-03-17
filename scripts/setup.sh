#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — VPS İlk Kurulum Scripti
#  Kullanım: sudo bash scripts/setup.sh
#  Ubuntu 22.04 LTS üzerinde çalışır
# ─────────────────────────────────────────────────────────────

set -e  # Hata olursa dur

echo "🚀 VoiceAI Platform VPS Kurulumu Başlıyor..."
echo "================================================"

# ── 1. Sistem Güncellemesi ─────────────────────────────────
echo "📦 [1/8] Sistem güncelleniyor..."
apt update && apt upgrade -y
apt install -y curl wget git unzip htop net-tools ufw fail2ban

# ── 2. Docker Kurulumu ─────────────────────────────────────
echo "🐳 [2/8] Docker kuruluyor..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo "✅ Docker $(docker --version)"
echo "✅ Docker Compose $(docker-compose --version)"

# ── 3. Güvenlik Duvarı ─────────────────────────────────────
echo "🔒 [3/8] Güvenlik duvarı yapılandırılıyor..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 5060/udp    # SIP
ufw allow 5061/tcp    # SIP-TLS
ufw allow 10000:10100/udp  # RTP ses kanalları
ufw --force enable
echo "✅ UFW güvenlik duvarı aktif"

# ── 4. Fail2ban ─────────────────────────────────────────────
echo "🛡️ [4/8] Fail2ban yapılandırılıyor..."
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
echo "🔑 [5/8] SSH güvenliği sıkılaştırılıyor..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
echo "✅ SSH: Root login kapalı, sadece key-based auth"

# ── 6. Otomatik Güncellemeler ───────────────────────────────
echo "🔄 [6/8] Otomatik güvenlik güncellemeleri aktif ediliyor..."
apt install -y unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
echo "✅ Otomatik güncellemeler aktif"

# ── 7. Proje Kurulumu ───────────────────────────────────────
echo "📁 [7/8] Proje dizini hazırlanıyor..."
mkdir -p /opt/voiceai
cd /opt/voiceai

echo ""
echo "⚠️  ŞİMDİ YAPMANIZ GEREKENLER:"
echo "1. .env dosyasını oluştur: cp .env.example .env"
echo "2. .env dosyasını düzenle: nano .env"
echo "3. Repo'yu klonla veya dosyaları yükle"
echo ""

# ── 8. Ollama Model İndirme (Arka Planda) ──────────────────
echo "🤖 [8/8] Ollama hazırlanıyor..."
echo "Not: Docker başlatıldıktan sonra modeli indirmek için:"
echo "docker exec voiceai-ollama ollama pull atasoglu/Turkish-Llama-3-8B-function-calling"
echo ""

echo "================================================"
echo "✅ VPS Temel Kurulum Tamamlandı!"
echo ""
echo "Sonraki Adımlar:"
echo "1. GitHub'dan projeyi klonla:"
echo "   git clone https://github.com/[KULLANICI]/voiceai.git /opt/voiceai"
echo ""
echo "2. Ortam değişkenlerini ayarla:"
echo "   cd /opt/voiceai && cp .env.example .env && nano .env"
echo ""
echo "3. Servisleri başlat:"
echo "   docker-compose up -d"
echo ""
echo "4. Durumu kontrol et:"
echo "   docker-compose ps"
echo "   docker-compose logs -f"
echo "================================================"
