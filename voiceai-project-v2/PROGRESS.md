# VoiceAI Platform — İlerleme Günlüğü (PROGRESS.md) v2.0

> Her oturum sonunda güncelle → git push → yeni konuşmada CLAUDE.md ile yapıştır.

---

## 📍 Şu Anki Durum

```
FAZ     : Başlangıç — Henüz kurulum yapılmadı
HAFTA   : 0
OTURUM  : —
SONRAKI : VPS alındıktan sonra Faz 1'e başla
```

---

## ✅ FAZ 1 — Çekirdek AI Motoru (Hafta 1-4)

### VPS Temel Kurulum
- [ ] Ubuntu 22.04 root şifre değiştir
- [ ] SSH key-based auth, root login kapat
- [ ] UFW firewall kuralları (22, 80, 443, 5060, 5061, 10000-10100)
- [ ] Fail2ban (SSH + SIP koruması)
- [ ] Otomatik güvenlik güncellemeleri
- [ ] Docker + Docker Compose kurulumu
- [ ] GitHub repo klonlama (`git clone`)
- [ ] `.env` dosyası oluşturma ve doldurma

### Asterisk / Telefoni
- [ ] Asterisk 18+ Docker container çalışıyor
- [ ] PJSIP modülü aktif
- [ ] Netgsm SIP Trunk bağlantısı test edildi ✅
- [ ] Verimor SIP Trunk bağlantısı test edildi ✅
- [ ] NAT ayarları (external_media_address)
- [ ] ARI (Asterisk REST Interface) çalışıyor
- [ ] AudioSocket protokolü kuruldu
- [ ] Test çağrısı alındı (ses gidiyor + geliyor)

### AI Servisleri
- [ ] Faster-Whisper Turbo INT8 Docker servisi çalışıyor
- [ ] Whisper Türkçe test başarılı (WER ölçüldü)
- [ ] Ollama Docker servisi çalışıyor
- [ ] Turkish-Llama-3-8B model indirildi
- [ ] LLM Türkçe fonksiyon çağırma testi başarılı
- [ ] XTTS-v2 Docker servisi çalışıyor
- [ ] XTTS-v2 Türkçe ses kalitesi test edildi
- [ ] TEN VAD entegre edildi

### Pipeline
- [ ] Pipecat pipeline kuruldu (STT→LLM→TTS)
- [ ] Barge-in çalışıyor
- [ ] Token streaming aktif
- [ ] **🎯 MİLESTONE: Telefon çalıyor, Türkçe konuşuyor**

---

## ✅ FAZ 2 — İş Mantığı ve Veritabanı (Hafta 5-7)

### Veritabanı
- [ ] PostgreSQL 16 Docker çalışıyor
- [ ] `shared.*` ortak şema oluşturuldu
- [ ] Otel şablonu DB şeması hazır
- [ ] Klinik şablonu DB şeması hazır
- [ ] Halı yıkama şablonu DB şeması hazır
- [ ] Su/tüp bayii şablonu DB şeması hazır
- [ ] Redis çalışıyor

### AI İş Mantığı
- [ ] Function Calling motoru (JSON→DB aksiyonu)
- [ ] Slot Filling akışı (LangGraph)
- [ ] Müşteri hafıza sistemi (kısa/orta/uzun)
- [ ] Çağrı log sistemi (GZIP + AI özeti)
- [ ] Duygu analizi entegrasyonu

### İletişim & Aktarım
- [ ] Netgsm SMS API entegrasyonu
- [ ] Otomatik SMS tetikleyicileri
- [ ] Celery + Redis görev kuyruğu
- [ ] Çağrı aktarım sistemi (Asterisk transfer)
- [ ] Aktarım öncesi AI özeti
- [ ] Geri arama kuyruğu
- [ ] **🎯 MİLESTONE: Rezervasyon alıyor, SMS gönderiyor**

---

## ✅ FAZ 3 — Paneller (Hafta 8-11)

### Backend API
- [ ] FastAPI iskelet + JWT auth
- [ ] Multi-tenant middleware
- [ ] AES-256-GCM şifreleme servisi (crypto.py)
- [ ] Sistem ayarları API (admin)
- [ ] Entegrasyon ayarları API (firma)
- [ ] "Test Et" servisi (integration_tester.py)
- [ ] Şablon motoru (template_engine.py)

### Admin Paneli
- [ ] Next.js kurulumu + TypeScript + Tailwind
- [ ] Admin giriş sayfası
- [ ] Dashboard (VPS sağlığı, firma sayısı, gelir)
- [ ] Firma listesi ve yönetimi
- [ ] Firma durdurma / aktif etme
- [ ] Paket yönetimi
- [ ] **Sistem Ayarları sayfası** (SIP, SMS, iyzico, SMTP)
- [ ] **Şablon Yönetimi sayfası**
- [ ] Gelir raporları

### Firma Paneli
- [ ] Firma giriş sayfası
- [ ] Dashboard (anlık çağrı, istatistik)
- [ ] Ajan ayarları (isim, kişilik)
- [ ] Ses seçimi ve klonlama
- [ ] Hizmet yönetimi
- [ ] Müsaitlik takvimi
- [ ] **Entegrasyon Ayarları sayfası** (SIP, PMS, Calendar)
- [ ] API anahtarı yönetimi (ApiKeyInput bileşeni)
- [ ] SMS şablon yönetimi
- [ ] Çağrı geçmişi
- [ ] Raporlama
- [ ] Onboarding sihirbazı (5 adım)
- [ ] **🎯 MİLESTONE: Firma 30 dakikada canlıya geçiyor**

---

## ✅ FAZ 4 — Faturalama (Hafta 12-14)

- [ ] Kullanım sayacı (Redis + PostgreSQL)
- [ ] Aşım hesaplama motoru
- [ ] Invoice Ninja OSS entegrasyonu
- [ ] PDF fatura üretimi
- [ ] iyzico ödeme entegrasyonu
- [ ] iyzico kart token saklama
- [ ] Gecikme otomasyon akışı (Gün 3/7/10/15)
- [ ] Finansal SMS bildirimleri (tam set)
- [ ] Kullanım eşiği SMS (%70/%85/%95/%100)
- [ ] Paket yükseltme öneri motoru
- [ ] Firma fatura sayfası
- [ ] Admin gelir raporları
- [ ] **🎯 MİLESTONE: Otomatik faturalama çalışıyor**

---

## ✅ FAZ 5 — Test ve Lansman (Hafta 15-16)

- [ ] Yük testi (3-4 eş zamanlı çağrı — SIPp)
- [ ] Türkçe WER ölçümü (hedef < %10)
- [ ] E2E gecikme ölçümü (hedef < 2.5sn)
- [ ] Güvenlik testi (OWASP ZAP)
- [ ] KVKK uyumluluk kontrolü
- [ ] SSL/TLS Let's Encrypt
- [ ] Günlük yedekleme testi
- [ ] Prometheus + Grafana dashboard
- [ ] Pilot firma testi (gerçek firma)
- [ ] Hata düzeltme ve optimizasyon
- [ ] **🎯 MİLESTONE: Üretim lansmanı**

---

## 📓 Oturum Günlükleri

### Oturum 1 — [TARİH]
**Yapılanlar:** Henüz başlanmadı
**Sorunlar:** —
**Çözümler:** —
**Sonraki:** VPS kurulumu ile başla

---

## 🐛 Bilinen Sorunlar

| # | Sorun | Dosya | Durum | Çözüm |
|---|-------|-------|-------|-------|
| — | Henüz sorun yok | — | — | — |

---

## 📌 Kritik Konfigürasyon Notları

```
Çözülen önemli sorunlar buraya eklenir.
Format:
[Tarih] [Servis] Sorun: ... Çözüm: ... Dosya: ...
```

---

## 🔑 Servis Adresleri (Kurulum Sonrası Doldur)

```
VPS IP           : [DOLDUR]
Domain           : [DOLDUR]
Admin Panel      : https://[DOMAIN]/admin
Firma Paneli     : https://[DOMAIN]/firma
API Docs         : https://[DOMAIN]/api/docs
Grafana          : http://[VPS-IP]:3001
```

---

## 📊 Performans Hedefleri

| Metrik | Hedef | Gerçek | Durum |
|--------|-------|--------|-------|
| E2E Gecikme | < 2.5 sn | — | ⏳ |
| Türkçe WER | < %10 | — | ⏳ |
| Rezervasyon Oranı | > %70 | — | ⏳ |
| Uptime | > %99 | — | ⏳ |
| Eş Zamanlı Çağrı | 3-4 | — | ⏳ |
