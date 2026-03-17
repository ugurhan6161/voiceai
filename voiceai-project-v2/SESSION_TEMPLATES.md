# Claude Oturum Başlatma Şablonları v2.0

---

## ŞABLON 1 — Genel Oturum

```
Aşağıda VoiceAI platformu için CLAUDE.md ve PROGRESS.md dosyalarım var.
Bunları okuyup projeye hakim ol, sonra bugünkü göreve geçelim.

=== CLAUDE.md ===
[CLAUDE.md içeriğini yapıştır]
=== CLAUDE.md BİTİŞ ===

=== PROGRESS.md ===
[PROGRESS.md içeriğini yapıştır]
=== PROGRESS.md BİTİŞ ===

Bugün yapmak istediğim: [GÖREV]
```

---

## ŞABLON 2 — Hata Çözme

```
VoiceAI projesinde bir sorun var.

=== CLAUDE.md ===
[kısa versiyon yapıştır]
=== CLAUDE.md BİTİŞ ===

Hata:
[HATA MESAJI]

Log (docker logs voiceai-[servis] --tail 50):
[LOG ÇIKTISI]

İlgili dosya: [DOSYA YOLU]
```

---

## ŞABLON 3 — Skill ile Oturum

```
Bu konuşmada [SKILL ADI] rolünü üstlen.

[CLAUDE.md] [PROGRESS.md]

Görev: [GÖREV]
```

**Mevcut Skill'ler:**
- Proje Mimarı *(her zaman aktif)*
- Asterisk / VoIP Uzmanı
- Güvenlik ve Şifreleme Uzmanı ← YENİ
- Ayarlar ve Entegrasyon Uzmanı ← YENİ
- Şablon Motoru Uzmanı ← YENİ
- Hizmet Sektörü Şablon Uzmanı ← YENİ
- Python / FastAPI Backend Uzmanı
- PostgreSQL Veritabanı Mimarı
- Next.js / Frontend Uzmanı
- Faturalama Uzmanı
- Docker / DevOps Uzmanı
- Türkçe Dil / AI Optimizasyon Uzmanı
- Hızlı Sorun Çözme Uzmanı

---

## ŞABLON 4 — Yeni Şablon Ekleme

```
Şablon Motoru Uzmanı ve Hizmet Sektörü Uzmanı rollerini üstlen.
[CLAUDE.md] [PROGRESS.md]

[SEKTÖR ADI] sektörü için yeni şablon ekleyeceğiz.

Bu sektördeki tipik telefon konuşmaları:
- [ÖRNEK 1]
- [ÖRNEK 2]

Müşterilerin en çok sormak istediği şeyler:
- [SORU 1]
- [SORU 2]
```

---

## ŞABLON 5 — Oturum Sonu Güncelleme

```
Bu oturumda şunları yaptık:
- [YAPILAN 1]
- [YAPILAN 2]

Sorunlar ve çözümler:
- [SORUN]: [ÇÖZÜM]

Sonraki oturumda:
- [SONRAKI]

Bu bilgilerle PROGRESS.md güncellemesini ve
tamamlanan checkbox'ları işaretleyerek yazar mısın?
```

---

## Hızlı VPS Komutları

```bash
# Tüm servisleri başlat
docker-compose up -d

# Durum
docker-compose ps

# Log izle
docker logs voiceai-[servis] --tail 50 -f

# Güncelle
git pull && docker-compose up -d --build

# Yeniden başlat
docker-compose restart [servis]

# Sağlık kontrolü
bash scripts/health_check.sh

# Yedekleme
bash scripts/backup.sh

# ENCRYPTION_KEY üret
python3 -c "import secrets; print(secrets.token_hex(32))"

# Şifreleme rotasyonu
python3 scripts/rotate_encryption_key.py

# Model indir
docker exec voiceai-ollama ollama pull atasoglu/Turkish-Llama-3-8B-function-calling

# DB bağlan
docker exec -it voiceai-postgres psql -U voiceai_user -d voiceai
```
