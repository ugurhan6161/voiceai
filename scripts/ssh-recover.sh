#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — SSH Erişim Kurtarma Scripti
#
#  Kullanım: VPS sağlayıcısının WEB KONSOLU (KVM/noVNC) üzerinden
#            root olarak çalıştırın:
#
#    curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/ssh-recover.sh \
#      | sudo bash
#
#  VEYA dosyayı indirip çalıştırın:
#    wget -O /tmp/ssh-recover.sh https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/ssh-recover.sh
#    bash /tmp/ssh-recover.sh
#
#  Bu script:
#    1. SSH root girişini yeniden etkinleştirir (PermitRootLogin yes)
#    2. SSH servisini yeniden başlatır
#    3. UFW'de 22/tcp portunu açık bırakır
#    4. fail2ban'dan sunucu IP'sini kaldırır (yanlış ban varsa)
#
#  ⚠️  Bu script yalnızca VPS sağlayıcısının web konsolu
#      (erişim kesildiğinde) üzerinden çalıştırılmalıdır.
# ─────────────────────────────────────────────────────────────

BOLD="\e[1m"
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
RESET="\e[0m"

echo -e "${BOLD}========================================"
echo -e "   VoiceAI SSH Erişim Kurtarma"
echo -e "========================================${RESET}"
echo ""

# ── 1. Root girişini etkinleştir ──────────────────────────
echo -e "${BOLD}[1/4] SSH root erişimi etkinleştiriliyor...${RESET}"
if [ ! -f /etc/ssh/sshd_config ]; then
    echo -e "  ${RED}✗ /etc/ssh/sshd_config bulunamadı — SSH kurulu mu?${RESET}"
else
    # PermitRootLogin no → yes
    if grep -qE '^\s*PermitRootLogin[\s=]+no' /etc/ssh/sshd_config; then
        sed -i 's/^\s*PermitRootLogin\s.*/PermitRootLogin yes/' /etc/ssh/sshd_config
        echo -e "  ${GREEN}✓ PermitRootLogin no → yes${RESET}"
    # PermitRootLogin satırı yok veya yorum satırı — ekle
    elif ! grep -qE '^\s*PermitRootLogin' /etc/ssh/sshd_config; then
        echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
        echo -e "  ${GREEN}✓ PermitRootLogin yes eklendi${RESET}"
    else
        echo -e "  ℹ️  PermitRootLogin zaten açık"
    fi

    # SSH servisini yeniden başlat
    if systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null; then
        echo -e "  ${GREEN}✓ SSH servisi yeniden başlatıldı${RESET}"
    else
        echo -e "  ${YELLOW}⚠️  SSH yeniden başlatılamadı — manuel deneyin: service ssh restart${RESET}"
    fi
fi

# ── 2. UFW SSH portunu garanti altına al ──────────────────
echo -e "${BOLD}[2/4] UFW: 22/tcp portu açılıyor...${RESET}"
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp 2>/dev/null || true
    # UFW etkin değilse etkinleştirme — mevcut durumu koru
    UFW_STATUS=$(ufw status 2>/dev/null | head -1)
    echo -e "  ${GREEN}✓ UFW 22/tcp kuralı eklendi — Durum: $UFW_STATUS${RESET}"
else
    echo -e "  ℹ️  UFW kurulu değil — atlanıyor"
fi

# ── 3. fail2ban SSH ban'ını kaldır (varsa) ────────────────
echo -e "${BOLD}[3/4] fail2ban SSH ban listesi temizleniyor...${RESET}"
if command -v fail2ban-client &>/dev/null; then
    if fail2ban-client status sshd &>/dev/null 2>&1; then
        fail2ban-client unban --all 2>/dev/null || true
        echo -e "  ${GREEN}✓ fail2ban SSH banları kaldırıldı${RESET}"
    else
        echo -e "  ℹ️  fail2ban sshd jail aktif değil — atlanıyor"
    fi
else
    echo -e "  ℹ️  fail2ban kurulu değil — atlanıyor"
fi

# ── 4. Bağlantı testi bilgisi ─────────────────────────────
echo -e "${BOLD}[4/4] Bağlantı bilgisi...${RESET}"
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo -e "  Sunucu IP  : ${BOLD}${SERVER_IP}${RESET}"
echo -e "  SSH Port   : 22"
echo -e "  Kullanıcı  : root"

echo ""
echo -e "${BOLD}========================================${RESET}"
echo -e "${GREEN}${BOLD}✅ SSH kurtarma tamamlandı!${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""
echo -e "Şimdi PuTTY veya VS Code ile bağlanmayı deneyin:"
echo -e "  ${BOLD}ssh root@${SERVER_IP}${RESET}"
echo ""
echo -e "${YELLOW}⚠️  Bağlantı hâlâ başarısız olursa:${RESET}"
echo -e "  1. VPS sağlayıcınızın güvenlik duvarı kurallarını kontrol edin"
echo -e "     (Hetzner: Firewall, DigitalOcean: Cloud Firewall, vb.)"
echo -e "  2. SSH servis durumunu kontrol edin:"
echo -e "     ${BOLD}systemctl status sshd${RESET}"
echo -e "  3. SSH loglarını inceleyin:"
echo -e "     ${BOLD}journalctl -u sshd -n 50${RESET}"
echo ""
