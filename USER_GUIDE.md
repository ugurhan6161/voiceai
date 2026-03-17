# VoiceAI Platform — Sistem Kullanım Kılavuzu

VoiceAI, işletmeler için 7/24 çalışan Türkçe sesli asistan (AI Resepsiyonist) SaaS platformudur.

## 🚀 Hızlı Başlangıç

- **Admin Paneli**: [http://31.57.77.166/admin/login](http://31.57.77.166/admin/login)
- **Kullanıcı**: `admin@voiceai.com`
- **Şifre**: `Admin2026!`

## 🛠️ Yönetim Paneli (Super Admin)

### 1. Dashboard
Sistem genelindeki toplam firma sayısını, günlük ve aylık çağrı istatistiklerini ve sunucu sağlığını takip edebilirsiniz.

### 2. Firma Yönetimi
- **Firma Ekleme**: Yeni bir firma oluştururken sektör (otel, klinik vb.) seçimi yapın. Sistem otomatik olarak o firmaya özel veritabanı şemasını ve AI ajanını hazırlar.
- **Durdur/Aktif Et**: Ödemesi geciken veya bakımı gereken firmaların çağrı almasını anlık olarak durdurabilirsiniz.

### 3. Sistem Ayarları
- **SIP Ayarları**: Asterisk/PJSIP üzerinden dış hat bağlantılarını yapılandırın.
- **SMS Ayarları**: Netgsm API anahtarlarını buraya girerek asistanın onay SMS'leri atmasını sağlayın.
- **Iyzico/Ödeme**: Müşterilerinizden ödeme alabilmek için API anahtarlarını girin.

## 🏢 Firma Paneli

Firma adminleri kendi panellerine giriş yaparak aşağıdaki işlemleri yapabilir:

- **AI Ajan Ayarları**: Asistanın adını, karşılama metnini ve ses tonunu (Kadın/Erkek) değiştirebilir.
- **Çağrı Geçmişi**: Tüm görüşmelerin transkriptlerini (yazılı döküm), AI özetlerini ve sonuçlarını görebilir.
- **Onboarding**: Üyeliğini yeni başlatan firmalar için sihirbaz yardımıyla hizmet ve fiyat tanımlaması yapabilir.

## 🎙️ AI Asistan ve Asterisk

- **Arama Yapma/Alma**: Asterisk VPS üzerinde native çalışır. Docker içindeki `ai-engine` ARI üzerinden çağrıyı yakalar.
- **STT (Sesden Metne)**: OpenAI Whisper (Turbo model) kullanılarak en düşük gecikmeyle Türkçe anlama yapılır.
- **LLM (Akıllı Zeka)**: Llama 3.1:8b modeli işletme şablonuna göre müşteriye yanıt verir.
- **TTS (Metinden Sese)**: gTTS veya XTTS-v2 ile doğal Türkçe ses üretilir.

## 🖥️ Teknik Komutlar (SSH)

Sistemi yönetmek için `/opt/voiceai` klasöründe şu komutları kullanabilirsiniz:

```bash
# Tüm servisleri durdur ve yeniden başlat
docker-compose down && docker-compose up -d

# Backend loglarını canlı izle
docker logs -f voiceai-backend

# AI Engine (Arama akışı) loglarını izle
docker logs -f voiceai-ai-engine

# Veritabanına manuel giriş
docker exec -it voiceai-postgres psql -U voiceai_user -d voiceai
```

## ⚠️ Dikkat Edilmesi Gerekenler

1. **XTTS IP Adresi**: Docker restart sonrası XTTS servisinin IP'si değişirse `docker-compose.yml` içindeki `ai-engine` -> `XTTS_URL` kısmını güncellemeniz gerekebilir.
2. **Asterisk ARI**: Asterisk native VPS'te olduğu için Docker'dan Docker Gateway IP'si (172.17.0.1) üzerinden erişir.
3. **KVKK**: Tüm çağrılar başında otomatik KVKK onayı ister. Müşteri onay vermezse AI görüşmeyi sonlandırır.
