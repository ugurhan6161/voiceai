"""
VoiceAI Platform — AES-256-GCM Şifreleme Servisi
Tüm hassas veriler (API anahtarları, şifreler) bu servis üzerinden şifrelenir.

Kullanım:
    from crypto import encrypt, decrypt

    sifreli = encrypt("netgsm-api-sifrem")
    orijinal = decrypt(sifreli)
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_key() -> bytes:
    """
    Şifreleme anahtarını .env'den alır.
    ENCRYPTION_KEY: 64 karakter hex string (32 byte = 256 bit)
    Üretmek için: python -c "import secrets; print(secrets.token_hex(32))"
    """
    key_hex = os.getenv("ENCRYPTION_KEY")
    if not key_hex:
        raise RuntimeError(
            "ENCRYPTION_KEY ortam değişkeni tanımlı değil! "
            ".env dosyasına ekleyin."
        )
    if len(key_hex) != 64:
        raise RuntimeError(
            "ENCRYPTION_KEY 64 karakter hex string olmalı (32 byte)."
        )
    return bytes.fromhex(key_hex)


def encrypt(deger: str) -> str:
    """
    Verilen string değeri AES-256-GCM ile şifreler.

    Args:
        deger: Şifrelenecek düz metin

    Returns:
        Base64 kodlanmış şifreli metin (nonce + ciphertext formatı)

    Raises:
        ValueError: Boş değer verilirse
        RuntimeError: ENCRYPTION_KEY tanımlı değilse
    """
    if not deger:
        raise ValueError("Şifrelenecek değer boş olamaz.")

    anahtar = _get_key()
    nonce = os.urandom(12)  # 96-bit nonce (GCM için standart)
    aesgcm = AESGCM(anahtar)
    sifreli = aesgcm.encrypt(nonce, deger.encode("utf-8"), None)
    # Format: base64(nonce[12] + ciphertext + auth_tag[16])
    return base64.b64encode(nonce + sifreli).decode("utf-8")


def decrypt(sifreli_deger: str) -> str:
    """
    Şifreli değeri çözer.

    Args:
        sifreli_deger: encrypt() ile şifrelenmiş base64 string

    Returns:
        Orijinal düz metin

    Raises:
        ValueError: Geçersiz şifreli veri
        RuntimeError: ENCRYPTION_KEY tanımlı değilse
    """
    if not sifreli_deger:
        raise ValueError("Çözülecek değer boş olamaz.")

    try:
        anahtar = _get_key()
        veri = base64.b64decode(sifreli_deger)
        nonce = veri[:12]
        sifreli = veri[12:]
        aesgcm = AESGCM(anahtar)
        cozulmus = aesgcm.decrypt(nonce, sifreli, None)
        return cozulmus.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Şifre çözme başarısız: {e}")


def guvenli_goster(sifreli_deger: str, karakter_sayisi: int = 4) -> str:
    """
    Şifreli değerin son N karakterini gösterir, gerisini maskeler.
    Panel'de "••••••••1234" formatında göstermek için.

    Args:
        sifreli_deger: Şifreli değer
        karakter_sayisi: Gösterilecek son karakter sayısı

    Returns:
        Maskelenmiş string
    """
    try:
        orijinal = decrypt(sifreli_deger)
        if len(orijinal) <= karakter_sayisi:
            return "•" * len(orijinal)
        return "•" * (len(orijinal) - karakter_sayisi) + orijinal[-karakter_sayisi:]
    except Exception:
        return "••••••••"


def anahtar_uret() -> str:
    """
    Yeni bir şifreleme anahtarı üretir.
    Sadece kurulum sırasında kullanılır.

    Returns:
        64 karakter hex string
    """
    import secrets
    return secrets.token_hex(32)


# ── Kullanım Örnekleri ─────────────────────────────────────────
if __name__ == "__main__":
    print("Yeni ENCRYPTION_KEY üretiliyor...")
    print(f"ENCRYPTION_KEY={anahtar_uret()}")
    print()
    print("Test şifreleme:")
    test_deger = "netgsm-test-sifre-12345"
    sifreli = encrypt(test_deger)
    cozulmus = decrypt(sifreli)
    print(f"Orijinal  : {test_deger}")
    print(f"Şifreli   : {sifreli[:30]}...")
    print(f"Çözülmüş  : {cozulmus}")
    print(f"Maskeli   : {guvenli_goster(sifreli)}")
    print(f"Eşleşiyor : {test_deger == cozulmus}")
