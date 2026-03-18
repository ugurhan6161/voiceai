# 🆘 VPS Acil Kurtarma Rehberi

> **Bu sayfayı ne zaman kullanmalısınız?**
> VPS sunucusuna SSH (PuTTY / VS Code) ile bağlanamıyorsanız bu rehberi takip edin.

---

## 1. VPS Sağlayıcısının Web Konsolunu Açın

VPS paneline (kontrol paneli) giriş yapın ve sunucunuzun **web konsolu**nu açın.
Her sağlayıcıda farklı bir isim taşır:

| Sağlayıcı | Konsol Nerede? |
|-----------|----------------|
| **Hetzner** | Cloud Console → Sunucu seçin → **Console** sekmesi |
| **DigitalOcean** | Droplet → Access → **Launch Droplet Console** |
| **Contabo** | Customer Panel → Your Services → **VNC** |
| **Vultr** | Products → Server → **View Console** |
| **Linode / Akamai** | Linodes → **Launch LISH Console** |
| **OVH / OVHcloud** | Server Dashboard → **KVM** |
| **Diğerleri** | "Console", "VNC" veya "KVM" başlıklı bir buton arayın |

---

## 2. TTY Giriş Ekranında Oturum Açın

Web konsolu açıldığında siyah arka planlı aşağıdaki gibi bir ekran görürsünüz:

```
Ubuntu 22.04.5 LTS 31-57-77-166 tty1

31-57-77-166 login: _
```

**Adım adım ne yapmalısınız:**

### Adım 2a — Kullanıcı adını girin

Klavyeden `root` yazın ve **Enter** tuşuna basın:

```
31-57-77-166 login: root   ← bunu yazıp Enter'a basın
```

### Adım 2b — Şifreyi girin

Şifrenizi yazın ve **Enter** tuşuna basın:

```
Password:                  ← şifreyi yazın (ekranda görünmez, bu normaldir)
```

> ⚠️ **Önemli:** Şifre yazarken ekranda hiçbir karakter görünmez.
> Şifreyi körü körüne yazıp Enter'a basın.

### Adım 2c — Başarılı giriş

Giriş başarılıysa aşağıdaki gibi bir komut satırı görünür:

```
Welcome to Ubuntu 22.04.5 LTS ...

root@31-57-77-166:~#
```

Artık sunucuda **root** olarak bağlısınız.

---

> **Şifrenizi mi unuttunuz?**
> VPS sağlayıcısının panelinde **"Reset Password"** veya **"Rescue Mode"**
> seçeneğini bulun. Yeni bir root şifresi belirleyin, ardından 2a–2c adımlarını tekrarlayın.

---

## 3. SSH Erişimini Kurtarın

Sunucuda komut satırı açıkken aşağıdaki komutu çalıştırın:

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/ssh-recover.sh | bash
```

Bu script otomatik olarak:
- `PermitRootLogin yes` ayarlar (SSH root girişini açar)
- SSH servisini yeniden başlatır
- UFW'de 22 numaralı portun açık olduğunu doğrular
- fail2ban ban listesini temizler

**curl yoksa** aşağıdaki komutları tek tek kopyalayıp yapıştırın:

```bash
# 1. SSH root girişini aç
sed -i 's/^\s*PermitRootLogin\s.*/PermitRootLogin yes/' /etc/ssh/sshd_config
grep -q 'PermitRootLogin' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config

# 2. SSH servisini yeniden başlat
systemctl restart sshd

# 3. UFW port 22 açık bırak
ufw allow 22/tcp && ufw reload 2>/dev/null || true

# 4. fail2ban ban listesini temizle
fail2ban-client unban --all 2>/dev/null || true
```

---

## 4. PuTTY / VS Code ile Tekrar Bağlanın

Script tamamlandıktan sonra normal SSH bağlantısı çalışmalıdır:

| Alan | Değer |
|------|-------|
| Host / IP | `31.57.77.166` |
| Port | `22` |
| Kullanıcı | `root` |

**PuTTY:** Host Name alanına `31.57.77.166` yazın, Port `22`, Open tıklayın.

**VS Code (Remote-SSH):** `Ctrl+Shift+P` → `Remote-SSH: Connect to Host` → `root@31.57.77.166`

**Terminal:**
```bash
ssh root@31.57.77.166
```

---

## 5. Hâlâ Bağlanamıyorsanız

Web konsolda şu kontrolleri yapın:

```bash
# SSH servisi çalışıyor mu?
systemctl status sshd

# SSH hangi portları dinliyor?
ss -tlnp | grep sshd

# UFW durumu — 22/tcp açık mı?
ufw status

# Son SSH bağlantı denemelerini gör
journalctl -u sshd -n 30 --no-pager
```

**VPS sağlayıcısı tarafında güvenlik duvarı varsa:**
Hetzner, DigitalOcean, OVH gibi sağlayıcılar VPS dışında ek bir "Cloud Firewall"
sunabilir. Bu güvenlik duvarında da **TCP 22** portuna izin verildiğinden
emin olun.

---

## 6. Kuruluma Devam Edin

SSH erişimi geri geldikten sonra VoiceAI kurulumuna kaldığınız yerden devam edin:

```bash
# Repoyu klonla (eğer /opt/voiceai silindiyse)
git clone https://github.com/ugurhan6161/voiceai.git /opt/voiceai
cd /opt/voiceai

# Kurulumu başlat
bash scripts/setup.sh
```

Daha fazla bilgi için [INSTALL.md](INSTALL.md) dosyasına bakın.
