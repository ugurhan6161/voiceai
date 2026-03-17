# VoiceAI Paneli Kullanım Kılavuzu

VoiceAI, yapay zeka destekli Türkçe sesli resepsiyonist SaaS platformudur. Bu kılavuz, sistemin genel kullanımı, kurulumu ve yönetimi hakkında detaylı bilgi sağlar.

## 1. Giriş Bilgileri ve URL'ler

Platforma aşağıdaki adresler üzerinden erişebilirsiniz:

- **Admin Paneli:** [http://31.57.77.166/admin/login](http://31.57.77.166/admin/login)
- **Firma Paneli:** [http://31.57.77.166/firma/login](http://31.57.77.166/firma/login)
- **Super Admin Giriş Bilgileri:**
  - **Email:** `admin@voiceai.com`
  - **Şifre:** `Admin2026!`

## 2. Admin Paneli

Super Admin olarak aşağıdaki işlemleri gerçekleştirebilirsiniz:

- **Firma Yönetimi:** Yeni firma ekleme, düzenleme, durdurma veya silme işlemleri.
- **Sistem Ayarları:** Global API anahtarları, şifreleme ayarları ve sistem genelindeki parametrelerin yönetimi.
- **Şablon Yönetimi:** Otel, Klinik, Halı Yıkama gibi 40+ sektör şablonunun sistem promptlarının güncellenmesi.
- **Raporlar ve Faturalar:** Tüm firmaların çağrı istatistiklerini ve faturalandırma süreçlerini izleme.

## 3. Firma Paneli

Firma yöneticileri için sunulan özellikler:

- **Onboarding Sihirbazı:** Sisteme ilk girişte ajanın çalışma şeklini (rezervasyon, sipariş vb.) belirleme.
- **Ajan Ayarları:** Ajanın ismini, çalışma saatlerini ve ses tonunu özelleştirme.
- **Yönlendirme Ayarları:** Yapay zekanın çağrıyı kime (dahili hat veya dış numara) aktaracağının seçilmesi.
- **Zoiper Kurulumu:** Çağrıları bilgisayar veya telefondan yanıtlamak için SIP bilgilerine erişim.
- **Çağrı Geçmişi:** Yapılan tüm görüşmelerin transkriptleri ve yapay zeka tarafından çıkarılan özetleri.

## 4. SIP / Zoiper Bağlantı Bilgileri

Çağrıları gerçek zamanlı yanıtlamak için SIP istemcisi (Zoiper, MicroSIP) kullanmalısınız:

- **Domain / Host:** `31.57.77.166`
- **Port:** `5060`
- **Kullanıcı Adı:** `firma_{firma_id}_dahili` (örn: `firma_1_dahili`)
- **Şifre:** Panelde "SIP Ayarları" bölümünde belirtilen şifre.
- **Protokol:** UDP

## 5. Çok Dilli Kullanım

VoiceAI şu dilleri destekler:
- 🇹🇷 **Türkçe** (Varsayılan)
- 🇺🇸 **İngilizce**
- 🇸🇦 **Arapça**
- 🇷🇺 **Rusça**

Çağrı başında yapılan KVKK bilgilendirmesinden sonra müşteri, dilediği dili tuşlayarak seçebilir. AI ajan otomatik olarak seçilen dilde konuşmaya devam eder.

## 6. Fatura ve Ödeme

- Faturalandırma, aylık sabit ücret + çağrı başı aşım ücreti üzerinden hesaplanır.
- Ödemeler iyzico entegrasyonu ile güvenli bir şekilde panel üzerinden yapılır.
- Ödemesi geciken firmaların ajanları otomatik olarak "Beklemede" moduna alınır.

## 7. Sık Sorulan Sorular

**S: Ses gecikmesi yaşıyorum, ne yapmalıyım?**
C: İnternet bağlantınızı kontrol edin. SIP için UDP tercih edin ve Zoiper ayarlarında STUN sunucusu olarak `31.57.77.166` kullanın.

**S: Ajan müşteriyi yanlış anlıyor?**
C: Firma panelinden "Ajan Talimatları" bölümünü daha spesifik bilgilerle güncelleyin.
