#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — VPS Temizlik Scripti
#  Kullanım: sudo bash scripts/cleanup.sh [seçenekler]
#  Ubuntu 22.04 LTS üzerinde çalışır.
#
#  Seçenekler:
#    -y, --yes       Onay sormadan çalıştır (otomatik mod)
#    --full          Docker ve Asterisk paketlerini de kaldır
#                    (VPS format alternatifi — derin temizlik)
#
#  ⚠️  Bu script mevcut VoiceAI kurulumunu, Docker container/
#      image/volume'larını ve geçici dosyaları kaldırır.
#      Devam etmeden önce önemli verilerinizi yedekleyin!
# ─────────────────────────────────────────────────────────────

# set -e kullanılmıyor; her adım bağımsız çalışır, bir hata
# diğer adımları durdurmaz.

# ── Etkileşimli dialog'ları devre dışı bırak ──────────────
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# INSTALL_DIR: env değişkeni varsa kullan, yoksa script'in üst dizini.
# /opt/voiceai dışından çalıştırılıyorsa INSTALL_DIR ortam değişkeni ile belirtin.
INSTALL_DIR="${INSTALL_DIR:-$(dirname "$SCRIPT_DIR")}"
# Geçerli bir VoiceAI kurulumu mu kontrol et; değilse /opt/voiceai'ye dön
if [ ! -f "$INSTALL_DIR/docker-compose.yml" ] && [ -f "/opt/voiceai/docker-compose.yml" ]; then
    INSTALL_DIR="/opt/voiceai"
fi

BOLD="\e[1m"
RED="\e[31m"
YELLOW="\e[33m"
GREEN="\e[32m"
RESET="\e[0m"

AUTO_YES=false
FULL_CLEAN=false

# ── Argümanları ayrıştır ───────────────────────────────────────
for ARG in "$@"; do
    case "$ARG" in
        -y|--yes)   AUTO_YES=true ;;
        --full)     FULL_CLEAN=true ;;
    esac
done

echo -e "${BOLD}========================================${RESET}"
echo -e "${BOLD}   VoiceAI VPS Temizlik Scripti${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""
echo -e "${YELLOW}⚠️  UYARI: Bu işlem geri alınamaz!${RESET}"
echo -e "   • Mevcut VoiceAI kurulumu silinecek ($INSTALL_DIR)"
echo -e "   • Tüm Docker container/image/volume'lar kaldırılacak"
echo -e "   • Asterisk yapılandırması sıfırlanacak"
echo -e "   • Geçici ve önbellek dosyaları temizlenecek"
if [ "$FULL_CLEAN" = true ]; then
    echo -e "   ${RED}• [--full] Docker ve Asterisk paketleri de kaldırılacak${RESET}"
fi
echo ""

if [ "$AUTO_YES" = false ]; then
    echo -n "Devam etmek istiyor musunuz? (evet/hayır): "
    read -r CONFIRM
    CONFIRM=$(echo "$CONFIRM" | xargs)
    if [ "$CONFIRM" != "evet" ]; then
        echo "İşlem iptal edildi."
        exit 0
    fi
fi

echo ""

# Hata sayacı — sonunda kaç adım başarısız oldu bildir
ERRORS=0

# ── 1. VoiceAI Docker Servislerini Durdur ─────────────────────
echo -e "${BOLD}[1/7] Docker servisleri durduruluyor...${RESET}"
if [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
    if ! (cd "$INSTALL_DIR" && docker compose down --volumes --remove-orphans 2>/dev/null); then
        echo -e "  ${YELLOW}⚠️  Docker compose down başarısız — devam ediliyor${RESET}"
        ERRORS=$((ERRORS+1))
    else
        echo -e "  ${GREEN}✓ Docker servisleri durduruldu${RESET}"
    fi
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

    # VoiceAI image'larını sil
    mapfile -t VOICEAI_IMAGES < <(docker images --filter "reference=voiceai*" -q 2>/dev/null)
    if [ "${#VOICEAI_IMAGES[@]}" -gt 0 ]; then
        docker rmi -f "${VOICEAI_IMAGES[@]}" 2>/dev/null || true
        echo -e "  ${GREEN}✓ VoiceAI image'ları silindi${RESET}"
    fi

    # Tüm kullanılmayan kaynakları temizle
    docker system prune -af --volumes 2>/dev/null || true
    echo -e "  ${GREEN}✓ Docker system prune tamamlandı${RESET}"

    # --full: Docker paketini kaldır
    if [ "$FULL_CLEAN" = true ]; then
        echo -e "  ${YELLOW}[--full] Docker kaldırılıyor...${RESET}"
        systemctl stop docker 2>/dev/null || true
        apt-get purge -y docker-ce docker-ce-cli containerd.io docker-compose-plugin \
            docker-buildx-plugin 2>/dev/null || true
        rm -rf /var/lib/docker /var/lib/containerd \
               /usr/local/lib/docker /usr/local/bin/docker-compose \
               /etc/docker 2>/dev/null || true
        echo -e "  ${GREEN}✓ Docker kaldırıldı${RESET}"
    fi
else
    echo -e "  ℹ️  Docker kurulu değil — atlanıyor"
fi

# ── 3. VoiceAI Kurulum Dizinini Sil ───────────────────────────
echo -e "${BOLD}[3/7] VoiceAI kurulum dizini siliniyor...${RESET}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR" || { echo -e "  ${RED}✗ $INSTALL_DIR silinemedi${RESET}"; ERRORS=$((ERRORS+1)); }
    [ ! -d "$INSTALL_DIR" ] && echo -e "  ${GREEN}✓ $INSTALL_DIR silindi${RESET}"
else
    echo -e "  ℹ️  $INSTALL_DIR zaten yok"
fi

# ── 4. Asterisk Yapılandırmasını Sıfırla ──────────────────────
echo -e "${BOLD}[4/7] Asterisk yapılandırması sıfırlanıyor...${RESET}"
if command -v asterisk &>/dev/null || [ -d /etc/asterisk ]; then
    systemctl stop asterisk 2>/dev/null || true

    if [ "$FULL_CLEAN" = true ]; then
        echo -e "  ${YELLOW}[--full] Asterisk paketi kaldırılıyor...${RESET}"
        apt-get purge -y asterisk asterisk-pjsip asterisk-res-ari 2>/dev/null || true
        rm -rf /etc/asterisk /var/lib/asterisk /var/log/asterisk 2>/dev/null || true
        echo -e "  ${GREEN}✓ Asterisk kaldırıldı${RESET}"
    else
        # Sadece VoiceAI'nın kopyaladığı dosyaları sıfırla
        for CONF in pjsip.conf extensions.conf ari.conf http.conf rtp.conf modules.conf; do
            CONF_PATH="/etc/asterisk/$CONF"
            SAMPLE_PATH="/etc/asterisk/${CONF}.dpkg-new"
            if [ -f "$CONF_PATH" ]; then
                if [ -f "$SAMPLE_PATH" ]; then
                    cp "$SAMPLE_PATH" "$CONF_PATH"
                else
                    echo -e "  ${YELLOW}⚠️  $CONF için örnek dosya yok — sıfırlanıyor${RESET}"
                    echo "; VoiceAI cleanup — dosya sıfırlandı" > "$CONF_PATH"
                fi
            fi
        done
        rm -rf /var/lib/asterisk/sounds/voiceai 2>/dev/null || true
        echo -e "  ${GREEN}✓ Asterisk yapılandırması sıfırlandı${RESET}"
    fi
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
    ufw allow 22/tcp 2>/dev/null || true
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
journalctl --vacuum-time=1d 2>/dev/null || true
echo -e "  ${GREEN}✓ Önbellek temizlendi${RESET}"

echo ""
echo -e "${BOLD}========================================${RESET}"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ VPS Temizliği Tamamlandı!${RESET}"
else
    echo -e "${YELLOW}${BOLD}⚠️  Temizlik tamamlandı — $ERRORS adım başarısız oldu${RESET}"
    echo -e "${YELLOW}   Yukarıdaki ✗ satırlarını kontrol edin.${RESET}"
fi
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
