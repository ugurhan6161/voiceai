#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — VPS Temizlik Scripti
#  Kullanım: sudo bash scripts/cleanup.sh
#  Ubuntu 22.04 LTS üzerinde çalışır.
#
#  ⚠️  Bu script mevcut VoiceAI kurulumunu, Docker container/
#      image/volume'larını ve geçici dosyaları kaldırır.
#      Devam etmeden önce önemli verilerinizi yedekleyin!
# ─────────────────────────────────────────────────────────────

set -e

INSTALL_DIR="/opt/voiceai"
BOLD="\e[1m"
RED="\e[31m"
YELLOW="\e[33m"
GREEN="\e[32m"
RESET="\e[0m"

echo -e "${BOLD}========================================${RESET}"
echo -e "${BOLD}   VoiceAI VPS Temizlik Scripti${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""
echo -e "${YELLOW}⚠️  UYARI: Bu işlem geri alınamaz!${RESET}"
echo -e "   • Mevcut VoiceAI kurulumu silinecek"
echo -e "   • Tüm Docker container/image/volume'lar kaldırılacak"
echo -e "   • Asterisk yapılandırması sıfırlanacak"
echo -e "   • Geçici ve önbellek dosyaları temizlenecek"
echo ""
echo -n "Devam etmek istiyor musunuz? (evet/hayır): "
read -r CONFIRM
CONFIRM=$(echo "$CONFIRM" | xargs)   # baştaki/sondaki boşlukları kaldır

if [ "$CONFIRM" != "evet" ]; then
    echo "İşlem iptal edildi."
    exit 0
fi

echo ""

# ── 1. VoiceAI Docker Servislerini Durdur ─────────────────────
echo -e "${BOLD}[1/7] Docker servisleri durduruluyor...${RESET}"
if [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
    cd "$INSTALL_DIR"
    docker compose down --volumes --remove-orphans 2>/dev/null || true
    echo -e "  ${GREEN}✓ Docker servisleri durduruldu${RESET}"
else
    echo -e "  ℹ️  $INSTALL_DIR/docker-compose.yml bulunamadı — atlanıyor"
fi

# ── 2. Tüm Docker Temizliği ────────────────────────────────────
echo -e "${BOLD}[2/7] Docker container, image ve volume'ları temizleniyor...${RESET}"
if command -v docker &>/dev/null; then
    # Çalışan container'ları durdur
    mapfile -t RUNNING < <(docker ps -aq 2>/dev/null)
    if [ "${#RUNNING[@]}" -gt 0 ]; then
        docker stop "${RUNNING[@]}" 2>/dev/null || true
        docker rm -f "${RUNNING[@]}" 2>/dev/null || true
        echo -e "  ${GREEN}✓ Tüm container'lar silindi${RESET}"
    else
        echo -e "  ℹ️  Silinecek container yok"
    fi

    # Tüm image'ları sil (VoiceAI'ya ait olanlar)
    VOICEAI_IMAGES=$(docker images --filter "reference=voiceai*" -q 2>/dev/null)
    if [ -n "$VOICEAI_IMAGES" ]; then
        docker rmi -f $VOICEAI_IMAGES 2>/dev/null || true
        echo -e "  ${GREEN}✓ VoiceAI image'ları silindi${RESET}"
    fi

    # Kullanılmayan tüm kaynakları temizle
    docker system prune -af --volumes 2>/dev/null || true
    echo -e "  ${GREEN}✓ Docker system prune tamamlandı${RESET}"
else
    echo -e "  ℹ️  Docker kurulu değil — atlanıyor"
fi

# ── 3. VoiceAI Kurulum Dizinini Sil ───────────────────────────
echo -e "${BOLD}[3/7] VoiceAI kurulum dizini siliniyor...${RESET}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "  ${GREEN}✓ $INSTALL_DIR silindi${RESET}"
else
    echo -e "  ℹ️  $INSTALL_DIR zaten yok"
fi

# ── 4. Asterisk Yapılandırmasını Sıfırla ──────────────────────
echo -e "${BOLD}[4/7] Asterisk yapılandırması sıfırlanıyor...${RESET}"
if command -v asterisk &>/dev/null; then
    systemctl stop asterisk 2>/dev/null || true
    # Sadece VoiceAI'nın kopyaladığı dosyaları sil (orijinal örneklerle değiştir)
    for CONF in pjsip.conf extensions.conf ari.conf http.conf rtp.conf modules.conf; do
        CONF_PATH="/etc/asterisk/$CONF"
        SAMPLE_PATH="/etc/asterisk/${CONF}.dpkg-new"
        if [ -f "$CONF_PATH" ]; then
            if [ -f "$SAMPLE_PATH" ]; then
                cp "$SAMPLE_PATH" "$CONF_PATH"
            else
                echo -e "  ${YELLOW}⚠️  $CONF için örnek dosya bulunamadı — içerik sıfırlanıyor${RESET}"
                echo "; VoiceAI cleanup — dosya sıfırlandı" > "$CONF_PATH"
            fi
        fi
    done
    # VoiceAI ses dosyaları
    rm -rf /var/lib/asterisk/sounds/voiceai 2>/dev/null || true
    echo -e "  ${GREEN}✓ Asterisk yapılandırması sıfırlandı${RESET}"
else
    echo -e "  ℹ️  Asterisk kurulu değil — atlanıyor"
fi

# ── 5. Fail2ban VoiceAI Kurallarını Temizle ───────────────────
echo -e "${BOLD}[5/7] Fail2ban yapılandırması temizleniyor...${RESET}"
if [ -f /etc/fail2ban/jail.local ]; then
    rm -f /etc/fail2ban/jail.local
    systemctl restart fail2ban 2>/dev/null || true
    echo -e "  ${GREEN}✓ /etc/fail2ban/jail.local silindi${RESET}"
else
    echo -e "  ℹ️  jail.local zaten yok"
fi

# ── 6. UFW Portlarını Sıfırla ─────────────────────────────────
echo -e "${BOLD}[6/7] UFW güvenlik duvarı kuralları sıfırlanıyor...${RESET}"
if command -v ufw &>/dev/null; then
    ufw --force reset 2>/dev/null || true
    # Temel SSH kuralı — bağlantıyı kesmemek için
    ufw allow 22/tcp
    ufw --force enable 2>/dev/null || true
    echo -e "  ${GREEN}✓ UFW sıfırlandı (sadece SSH:22 açık bırakıldı)${RESET}"
else
    echo -e "  ℹ️  UFW kurulu değil — atlanıyor"
fi

# ── 7. Sistem Önbelleği ve Geçici Dosyaları Temizle ───────────
echo -e "${BOLD}[7/7] Sistem önbelleği ve geçici dosyalar temizleniyor...${RESET}"
apt-get autoremove -y 2>/dev/null || true
apt-get autoclean -y 2>/dev/null || true
rm -rf /tmp/voiceai* /tmp/get-docker.sh 2>/dev/null || true
# Kullanılmayan log dökümleri
journalctl --vacuum-time=1d 2>/dev/null || true
echo -e "  ${GREEN}✓ Önbellek temizlendi${RESET}"

echo ""
echo -e "${BOLD}========================================${RESET}"
echo -e "${GREEN}${BOLD}✅ VPS Temizliği Tamamlandı!${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""
echo -e "Sunucu şimdi temiz bir kurulum için hazır."
echo -e "Kuruluma başlamak için:"
echo ""
echo -e "  ${BOLD}bash scripts/setup.sh${RESET}"
echo ""
echo -e "veya otomatik kurulum için:"
echo ""
echo -e "  ${BOLD}curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/setup.sh | sudo bash${RESET}"
echo ""
