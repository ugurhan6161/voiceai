# VoiceAI Platform — Proje Bağlamı (CLAUDE.md) v3.0

> Bu dosyayı her yeni Claude konuşmasının başında yapıştır.
> PROGRESS.md dosyasını da yanına ekle.

---

## 🎯 Proje Nedir?

Türkiye'ye özel, VPS tabanlı, açık kaynaklı **çok kiracılı (multi-tenant)
yapay zeka sesli resepsiyonist SaaS platformu.**

- Netgsm / Verimor SIP trunk üzerinden gelen çağrıları karşılar
- **Çok dilli destek:** TR/EN/AR/RU — tuşlama ile dil seçimi
- Türkçe/İngilizce/Arapça/Rusça konuşur, anlar, rezervasyon / randevu / sipariş alır
- 40+ sektör şablonu — otel, klinik, halı yıkama, su bayii ve daha fazlası
- **Çağrı yönlendirme:** Gerçek telefona VEYA Zoiper/SIP uygulamasına
- Her firma kendi SIP dahili hattıyla Zoiper'dan çağrı alabilir
- Tüm API anahtarları ve şifreler AES-256-GCM ile şifreli DB'de saklanır
- Faturalama, abonelik, SMS bildirimi tam otomatik
- Tüm veriler yerli VPS'de — KVKK uyumlu

---

## 🖥️ VPS

| Kaynak | Değer |
|--------|-------|
| IP | 31.57.77.166 |
| CPU | 8 Çekirdek Xeon |
| RAM | 16 GB DDR4 |
| Disk | 100 GB NVMe |
| OS | Ubuntu 22.04 LTS |

---

## 🌍 Çok Dilli Sistem Mimarisi

### Dil Seçim Akışı
```
Müşteri arar
    ↓
KVKK onay (Türkçe)
    ↓
Karşılama: "Türkçe için 1, English 2, العربية 3, Русский 4"
    ↓
Tuşlama (DTMF)
    ↓
Seçilen dilde AI Ajan başlar
```

### Desteklenen Diller
| Tuş | Dil | LLM Prompt | TTS |
|-----|-----|-----------|-----|
| 1 | Türkçe | TR sistem promptu | gTTS tr |
| 2 | İngilizce | EN sistem promptu | gTTS en |
| 3 | Arapça | AR sistem promptu | gTTS ar |
| 4 | Rusça | RU sistem promptu | gTTS ru |

### Dil Konfigürasyonu
Her şablonun get_system_prompt(lang) metodu dil parametresi alır.
Varsayılan: Türkçe (1 veya zaman aşımı)

---

## 📞 Çağrı Yönlendirme Mimarisi

### Yönlendirme Seçenekleri (Firma Panelinden Seçilir)
```
AI Ajan → Yönlendirme kararı
            ├── TELEFON: Gerçek numaraya ARI transfer
            └── UYGULAMA: SIP dahili → Zoiper/MicroSIP'e
```

### SIP Dahili Hat Sistemi
- Her firma bir SIP dahili hat alır (örn: firma_1 → dahili 101)
- Asterisk pjsip.conf'a firma dahilisi eklenir
- Firma çalışanı Zoiper/MicroSIP ile bu dahiliye bağlanır
- AI yönlendirince çalışanın uygulaması çalar

### SIP Dahili Bilgileri Formatı
```
Sunucu   : 31.57.77.166
Port     : 5060
Kullanıcı: firma_{id}_dahili
Şifre    : [otomatik üretilen güvenli şifre]
Domain   : 31.57.77.166
```

### Zoiper Kurulum Adımları (Müşteriye Tarif)
```
1. zoiper.com → ücretsiz indir (iOS/Android/PC)
2. Hesap Ekle → SIP seç
3. Sunucu: 31.57.77.166
4. Kullanıcı: [firma dahili kullanıcı adı]
5. Şifre: [firma dahili şifre]
6. Domain: 31.57.77.166
7. Kaydet → Bağlan (yeşil ışık)
```

---

## 🧠 AI Stack

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| STT | Faster-Whisper Turbo INT8 | Çok dilli |
| LLM | llama3.1:8b (Ollama) | TR/EN/AR/RU |
| TTS | gTTS (geçici) → XTTS-v2 | Çok dilli |
| VAD | Yerleşik VAD | Barge-in |
| RAG | ChromaDB | Belge tabanlı |
| Pipeline | Pipecat + LangGraph | Slot filling |

---

## 🏗️ Altyapı Stack

| Katman | Teknoloji |
|--------|-----------|
| Telefoni | Asterisk 18+ native VPS |
| ARI | http://172.17.0.1:8088 |
| Backend | FastAPI Python 3.11+ |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| DB | PostgreSQL 16 multi-tenant |
| Cache | Redis 7 |
| Kuyruk | Celery + Redis |
| Şifreleme | AES-256-GCM |
| Ödeme | iyzico |
| SMS | Netgsm |
| Proxy | Nginx (80/443) |
| Compose | /usr/local/bin/docker-compose-v2 |

---

## 📁 Klasör Yapısı

```
/opt/voiceai/
├── CLAUDE.md / PROGRESS.md
├── docker-compose.yml / .env
├── asterisk/
│   ├── pjsip.conf          — SIP endpoint'ler + firma dahilileri
│   ├── extensions.conf     — Dialplan (KVKK + dil seçim + yönlendirme)
│   ├── ari.conf
│   └── http.conf
├── ai-engine/
│   ├── ari/
│   │   ├── ari_client.py
│   │   ├── call_manager.py  — Çok dilli pipeline
│   │   ├── audio_handler.py
│   │   ├── transfer_handler.py — Tel + SIP yönlendirme
│   │   └── kvkk_handler.py
│   ├── llm/
│   │   ├── ollama_client.py  — lang parametreli
│   │   ├── function_calling.py
│   │   ├── slot_filling.py
│   │   └── memory_manager.py
│   ├── tts/
│   │   └── xtts_service.py   — Çok dilli gTTS
│   └── stt/
│       └── whisper_service.py
├── backend/
│   ├── main.py
│   ├── crypto.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── firmalar.py
│   │   ├── firma_panel.py
│   │   ├── ayarlar.py
│   │   ├── sablon_yonetimi.py
│   │   └── sip_dahili.py    — Firma dahili SIP yönetimi
│   └── services/
│       ├── sms_service.py
│       ├── billing_service.py
│       ├── usage_service.py
│       ├── payment_service.py
│       ├── callback_service.py
│       └── sip_provision_service.py — Dahili hat provisioning
├── frontend/
│   └── src/app/
│       ├── admin/           — Super admin paneli
│       └── firma/           — Firma paneli
│           └── zoiper-kurulum/ — Kurulum rehberi sayfası
├── database/
├── nginx/
├── monitoring/
└── scripts/
```

---

## 🏗️ Mimari Kararlar (Değiştirilemez)

1. PostgreSQL schema izolasyonu — firma başına ayrı schema
2. Asterisk ARI + AudioSocket — AGI kullanılmaz
3. Token streaming — ilk token gelince TTS başlar
4. Barge-in aktif — kullanıcı konuşursa TTS durur
5. Ses kaydı yok — sadece GZIP transkript + AI özeti
6. Hard-code yasak — tüm değerler DB veya .env'den
7. Docker zorunlu — direkt kurulum yapılmaz (Asterisk hariç)
8. AES-256-GCM zorunlu — tüm API anahtarları şifreli
9. Test butonu zorunlu — her entegrasyon ayarında olmalı
10. Şablon registry — yeni şablonlar registry.py'ye kayıt zorunlu
11. Çok dilli zorunlu — her şablonun TR/EN/AR/RU promptu olmalı
12. Yönlendirme seçimi — tel veya SIP dahili, firma panelden seçer

---

## 👥 Roller

| Yetki | Super Admin | Firma Admin | Kullanıcı |
|-------|:-----------:|:-----------:|:---------:|
| Sistem ayarları | ✅ | ❌ | ❌ |
| Şablon yönetimi | ✅ | ❌ | ❌ |
| Tüm firmaları gör | ✅ | ❌ | ❌ |
| Firma durdur/aktif | ✅ | ❌ | ❌ |
| Kendi SIP dahili | ✅ | ✅ | ❌ |
| Yönlendirme ayarı | ✅ | ✅ | ❌ |
| Zoiper kurulum | ✅ | ✅ | ✅ |
| Fatura görüntüle | Tümü | Kendi | ❌ |
| Raporlar | Tümü | Kendi | Kendi |

---

## 🔑 Servis Adresleri

```
VPS IP        : 31.57.77.166
Admin Panel   : http://31.57.77.166/admin/login
Firma Panel   : http://31.57.77.166/firma/login
Admin Giriş   : admin@voiceai.com / Admin2026!
Asterisk ARI  : http://172.17.0.1:8088
XTTS/gTTS     : http://172.18.0.7:5002 (IP değişebilir!)
Whisper       : voiceai-whisper:9000
Ollama        : voiceai-ollama:11434
Compose CMD   : /usr/local/bin/docker-compose-v2 -f /opt/voiceai/docker-compose.yml
```

---

## ⚠️ Kritik Notlar

- Asterisk VPS'te native çalışıyor — Docker'da değil
- XTTS container IP restart'ta değişebilir — her zaman kontrol et:
  `docker inspect voiceai-xtts | grep IPAddress`
- UFW: 172.17/18.0.0/16 → 8088 açık (Docker→Asterisk)
- gTTS geçici TTS — XTTS-v2 ileride entegre edilecek
- Ses sorunu (MicroSIP NAT) — Netgsm SIP trunk ile çözülecek
- Zoiper testi için: testuser / test1234 / 31.57.77.166

---

## 🔄 Bu Konuşmada Bana Söyle

1. Hangi fazdayız?
2. Bugün ne yapacağız?
3. Aktif hata var mı?
4. PROGRESS.md'yi de yapıştır.