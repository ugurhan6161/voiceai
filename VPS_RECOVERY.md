# 🆘 VPS Acil Kurtarma Rehberi

> **Bu sayfayı ne zaman kullanmalısınız?**
> VPS sunucusuna SSH (PuTTY / VS Code) ile bağlanamıyorsanız bu rehberi takip edin.

---

## ⚡ Hızlı Cevap — Kendi Bilgisayarımdan Direk Bağlanabilir miyim?

**Evet, deneyebilirsiniz.** Kendi bilgisayarınızın terminalini açıp şunu çalıştırın:

```
ssh root@31.57.77.166
```

Aldığınız hataya göre ne yapacağınızı öğrenmek için → [Bölüm 0](#0-önce-dene--kendi-bilgisayarından-ssh)

---

## 0. Önce Dene — Kendi Bilgisayarından SSH

SSH genellikle kendi bilgisayarınızdan da çalışır; VPS web konsoluna hiç girmenize gerek kalmayabilir.

### Windows Kullanıyorsanız

**Seçenek A — Windows Terminal / PowerShell / CMD:**
```
ssh root@31.57.77.166
```
> Windows 10/11'de `ssh` komutu yerleşik olarak gelir. Açmak için:
> Başlat → "cmd" veya "PowerShell" arayın → çalıştırın.

**Seçenek B — PuTTY:**
1. [putty.org](https://www.putty.org) adresinden PuTTY'yi indirin ve kurun
2. Host Name: `31.57.77.166`, Port: `22`, Connection type: SSH
3. **Open** butonuna tıklayın

### Mac / Linux Kullanıyorsanız

Terminal uygulamasını açıp şunu çalıştırın:
```bash
ssh root@31.57.77.166
```

---

### SSH'nin Verdiği Hataya Göre Ne Yapmalısınız

| Aldığınız Hata / Durum | Anlamı | Yapmanız Gereken |
|------------------------|--------|-----------------|
| Şifre sorulur ve giriş başarılı ✅ | SSH çalışıyor | Giriş yapmaya devam edin |
| `Permission denied (publickey,password)` | SSH çalışıyor ama **root girişi engellenmiş** | → [Bölüm 1–3](#1-vps-sağlayıcısının-web-konsolunu-açın) (web konsol gerekli) |
| `Connection refused` | SSH servisi **çalışmıyor** | → [Bölüm 1–3](#1-vps-sağlayıcısının-web-konsolunu-açın) (web konsol gerekli) |
| `Connection timed out` | Güvenlik duvarı **port 22'yi blokluyor** | VPS sağlayıcısının panel güvenlik duvarında TCP 22 açın, sonra tekrar deneyin |
| `Host key verification failed` | SSH anahtarı değişmiş | `ssh-keygen -R 31.57.77.166` çalıştırın ve tekrar deneyin |

---

## 1. VPS Sağlayıcısının Web Konsolunu Açın

Doğrudan SSH çalışmadıysa, VPS sağlayıcınızın **web konsolu**na girin.
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

### Konsolunuz nasıl görünüyor?

#### Tür A — Tam Ekran Siyah Terminal (KVM / noVNC)

Siyah arka plan ve yanıp sönen imleçli tam ekran bir terminal görüyorsanız:

```
Ubuntu 22.04.5 LTS 31-57-77-166 tty1

31-57-77-166 login: _
```

**Yapmanız gerekenler:**
1. Önce **siyah alana fare ile tıklayın** (klavye odağı konsola geçer)
2. `root` yazın → klavyenizden **Enter** tuşuna basın
3. Root şifrenizi yazın → **Enter** tuşuna basın
   - ⚠️ Şifre yazarken ekranda hiçbir şey görünmez; bu normaldir
4. Giriş başarılıysa `root@31-57-77-166:~#` promptu gelir

---

#### Tür B — "Send Command" / Komut Gönder Kutusu

Bazı VPS panelleri tam ekran terminal yerine **bir metin kutusu ve "Send" / "Gönder" butonu** sunar.
Yazdığınız komut siyah ekranda görünmüyor olabilir — bu normaldir.

```
┌──────────────────────────────────┐
│  31-57-77-166 login: _           │   ← Siyah konsol ekranı
│                                  │
└──────────────────────────────────┘

[ root__________________ ] [Send]
       ↑ buraya yazın        ↑ tıklayın
```

**Adım adım:**

1. Metin kutusuna `root` yazın
2. **Send / Gönder / Enter** butonuna tıklayın (VEYA kutudayken klavyenizden Enter'a basın)
3. Siyah ekranda `Password:` çıkana kadar bekleyin (1–3 saniye)
4. Metin kutusunu **temizleyin**, root şifrenizi yazın
5. Tekrar **Send** butonuna tıklayın
   - ⚠️ Şifre kutuda görünse de konsol ekranında görünmez — bu normaldir
6. `root@31-57-77-166:~#` promptunu gördüğünüzde giriş başarılıdır

> **Hâlâ çalışmıyorsa:** Sağlayıcı panelinde farklı bir konsol türü arayın.
> "VNC", "KVM", "noVNC" veya "Web Terminal" butonları tam ekran konsol açar.

---

> **Şifrenizi mi unuttunuz?**
> VPS sağlayıcısının panelinde **"Reset Password"** veya **"Rescue Mode"**
> seçeneğini bulun. Yeni bir root şifresi belirleyin, ardından yukarıdaki adımları tekrarlayın.

---

## 3. SSH Erişimini Kurtarın

Sunucuda komut satırı açıkken (web konsolda root@... promptu görünüyorken)
aşağıdaki komutu çalıştırın:

```bash
curl -fsSL https://raw.githubusercontent.com/ugurhan6161/voiceai/main/scripts/ssh-recover.sh | bash
```

Bu script otomatik olarak:
- `PermitRootLogin yes` ayarlar (SSH root girişini açar)
- SSH servisini yeniden başlatır
- UFW'de 22 numaralı portun açık olduğunu doğrular
- fail2ban ban listesini temizler

**"Send command" kutusuyla çalıştırıyorsanız:** Yukarıdaki komutu metin kutusuna yapıştırın ve Send butonuna basın. Uzun komut — tamamlanması 5–15 saniye sürebilir.

**curl yoksa** aşağıdaki komutları tek tek çalıştırın:

```bash
sed -i 's/^\s*PermitRootLogin\s.*/PermitRootLogin yes/' /etc/ssh/sshd_config
grep -q 'PermitRootLogin' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
systemctl restart sshd
ufw allow 22/tcp && ufw reload 2>/dev/null || true
fail2ban-client unban --all 2>/dev/null || true
```

---

## 4. Kendi Bilgisayarınızdan SSH ile Bağlanın

Script tamamlandıktan sonra **kendi bilgisayarınızdan** bağlanın:

**Windows (CMD / PowerShell / Terminal):**
```
ssh root@31.57.77.166
```

**Mac / Linux:**
```bash
ssh root@31.57.77.166
```

**PuTTY:** Host: `31.57.77.166` → Port: `22` → Open

**VS Code (Remote-SSH):** `Ctrl+Shift+P` → `Remote-SSH: Connect to Host` → `root@31.57.77.166`

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
sunabilir. Bu güvenlik duvarında da **TCP 22** portuna izin verildiğinden emin olun.

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
