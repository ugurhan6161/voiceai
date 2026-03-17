#!/usr/bin/env python3
"""
VoiceAI Platform — Şifreleme Anahtarı Rotasyon Scripti
Tüm şifreli değerleri eski anahtarla çözer, yeni anahtarla tekrar şifreler.

Kullanım:
  python3 scripts/rotate_encryption_key.py

Dikkat:
  - Bu işlem yapılmadan önce tam yedek alın!
  - İşlem sırasında servisleri durdurun
"""
import os
import sys
import asyncio
import secrets
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_with_key(deger: str, key: bytes) -> str:
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, deger.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")


def decrypt_with_key(sifreli: str, key: bytes) -> str:
    veri = base64.b64decode(sifreli)
    return AESGCM(key).decrypt(veri[:12], veri[12:], None).decode("utf-8")


async def rotate_keys():
    print("=" * 50)
    print("VoiceAI Şifreleme Anahtarı Rotasyonu")
    print("=" * 50)

    # Eski anahtarı al
    eski_key_hex = os.getenv("ENCRYPTION_KEY")
    if not eski_key_hex:
        print("HATA: ENCRYPTION_KEY bulunamadı!")
        sys.exit(1)

    eski_key = bytes.fromhex(eski_key_hex)

    # Yeni anahtar üret
    yeni_key_hex = secrets.token_hex(32)
    yeni_key = bytes.fromhex(yeni_key_hex)

    print(f"\nYeni anahtar üretildi.")
    print(f"ÖNEMLİ: Aşağıdaki anahtarı .env dosyasına kaydedin!")
    print(f"\nYENİ ENCRYPTION_KEY={yeni_key_hex}\n")

    onay = input("Devam etmek istiyor musunuz? (evet/hayır): ")
    if onay.lower() != "evet":
        print("İşlem iptal edildi.")
        sys.exit(0)

    # DB bağlantısı
    try:
        import asyncpg
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"DB bağlantı hatası: {e}")
        sys.exit(1)

    # Sistem ayarlarını rotate et
    print("\nSistem ayarları rotate ediliyor...")
    satirlar = await conn.fetch(
        "SELECT id, deger FROM shared.sistem_ayarlari WHERE sifirli = TRUE AND deger IS NOT NULL"
    )
    for satir in satirlar:
        try:
            cozulmus = decrypt_with_key(satir["deger"], eski_key)
            yeni_sifreli = encrypt_with_key(cozulmus, yeni_key)
            await conn.execute(
                "UPDATE shared.sistem_ayarlari SET deger = $1 WHERE id = $2",
                yeni_sifreli, satir["id"]
            )
        except Exception as e:
            print(f"  HATA (id={satir['id']}): {e}")

    print(f"  {len(satirlar)} sistem ayarı rotate edildi.")

    # Firma entegrasyon ayarlarını rotate et
    print("\nFirma entegrasyon ayarları rotate ediliyor...")
    firmalar = await conn.fetch("SELECT schema_adi FROM shared.firmalar WHERE is_deleted = FALSE")
    toplam = 0

    for firma in firmalar:
        schema = firma["schema_adi"]
        try:
            firma_satirlar = await conn.fetch(
                f"SELECT id, deger FROM {schema}.entegrasyon_ayarlari WHERE sifirli = TRUE AND deger IS NOT NULL"
            )
            for satir in firma_satirlar:
                cozulmus = decrypt_with_key(satir["deger"], eski_key)
                yeni_sifreli = encrypt_with_key(cozulmus, yeni_key)
                await conn.execute(
                    f"UPDATE {schema}.entegrasyon_ayarlari SET deger = $1 WHERE id = $2",
                    yeni_sifreli, satir["id"]
                )
                toplam += 1
        except Exception as e:
            print(f"  HATA ({schema}): {e}")

    print(f"  {toplam} firma ayarı rotate edildi.")

    await conn.close()

    print("\n" + "=" * 50)
    print("✅ Rotasyon tamamlandı!")
    print("\nŞimdi yapmanız gerekenler:")
    print(f"1. .env dosyasındaki ENCRYPTION_KEY değerini güncelleyin:")
    print(f"   ENCRYPTION_KEY={yeni_key_hex}")
    print("2. Servisleri yeniden başlatın:")
    print("   docker-compose restart backend ai-engine celery-worker")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(rotate_keys())
