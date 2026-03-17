#!/usr/bin/env python3
"""
VoiceAI Platform — IVR Ses Dosyaları Oluşturucu
KVKK ve dil seçim ses dosyalarını gTTS ile üretir.
Format: 8kHz mono ulaw WAV (Asterisk uyumlu)

Kullanım: python3 /opt/voiceai/scripts/create_ivr_sounds.py
"""
import os
import subprocess
import tempfile
import sys

try:
    from gtts import gTTS
except ImportError:
    print("gTTS kurulu değil. Yükleniyor...")
    subprocess.run([sys.executable, "-m", "pip", "install", "gtts", "-q"])
    from gtts import gTTS

SOUNDS_DIR = "/var/lib/asterisk/sounds/voiceai"
os.makedirs(SOUNDS_DIR, exist_ok=True)

# Üretilecek ses dosyaları
IVR_SESLER = {
    # KVKK bildirimi
    "kvkk_tr": {
        "lang": "tr",
        "text": (
            "Merhaba. Bu görüşme yapay zeka destekli sesli asistan tarafından yürütülmektedir. "
            "Kişisel Verilerin Korunması Kanunu kapsamında bilgileriniz işlenecektir. "
            "Görüşmeye devam etmek ve onay vermek için 1'e basınız."
        )
    },
    # Dil seçim menüsü
    "dil_secim": {
        "lang": "tr",
        "text": (
            "Türkçe için 1'e basınız. "
            "For English, press 2. "
            "للعربية، اضغط 3. "
            "Для русского нажмите 4."
        )
    },
    # Karşılama (TR)
    "karsilama_tr": {
        "lang": "tr",
        "text": "Merhaba, size nasıl yardımcı olabilirim?"
    },
    # Karşılama (EN)
    "karsilama_en": {
        "lang": "en",
        "text": "Hello, how can I help you?"
    },
    # Karşılama (AR)
    "karsilama_ar": {
        "lang": "ar",
        "text": "مرحبا، كيف يمكنني مساعدتك؟"
    },
    # Karşılama (RU)
    "karsilama_ru": {
        "lang": "ru",
        "text": "Здравствуйте, чем могу помочь?"
    },
    # Transfer bekleme
    "transfer_bekliyor": {
        "lang": "tr",
        "text": "Sizi yetkili personelimize bağlıyorum, lütfen bekleyiniz."
    },
    # Meşgul - geri arama
    "mesgul_geri_arama": {
        "lang": "tr",
        "text": "Şu an meşgulüz. En kısa sürede sizi geri arayacağız."
    },
    # Cevapsız - geri arama
    "cevapsiz_geri_arama": {
        "lang": "tr",
        "text": "Şu an cevap veremiyoruz. En kısa sürede sizi geri arayacağız."
    },
    # Aktarım başarısız
    "aktarim_basarisiz": {
        "lang": "tr",
        "text": "Üzgünüz, şu an bağlanamıyoruz. Lütfen daha sonra tekrar arayınız."
    },
    # Geri arama karşılama
    "geri_arama_karsilama": {
        "lang": "tr",
        "text": "Merhaba, sizi daha önce aramıştık. Size nasıl yardımcı olabilirim?"
    },
    # KVKK onay
    "kvkk_onay": {
        "lang": "tr",
        "text": "Teşekkürler, onayınız alındı. Sizi asistanımıza bağlıyorum."
    },
    # KVKK red
    "kvkk_red": {
        "lang": "tr",
        "text": "Anlaşıldı. Görüşmeyi sonlandırıyoruz. İyi günler."
    },
}


def mp3_to_wav(mp3_path: str, wav_path: str) -> bool:
    """MP3'ü Asterisk uyumlu WAV'a çevir"""
    cmd = [
        "ffmpeg", "-i", mp3_path,
        "-ar", "8000",
        "-ac", "1",
        "-acodec", "pcm_mulaw",
        "-f", "wav",
        "-y",
        wav_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0


def ses_olustur(dosya_adi: str, lang: str, text: str) -> bool:
    """Tek bir ses dosyası oluştur"""
    wav_path = os.path.join(SOUNDS_DIR, f"{dosya_adi}.wav")

    # Zaten varsa atla
    if os.path.exists(wav_path):
        print(f"  ⏭️  Mevcut: {dosya_adi}.wav")
        return True

    try:
        # gTTS ile MP3 üret
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_path = f.name

        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(mp3_path)

        # WAV'a çevir
        if mp3_to_wav(mp3_path, wav_path):
            # İzinleri ayarla
            try:
                os.chown(wav_path, 14, 119)  # asterisk:asterisk
                os.chmod(wav_path, 0o644)
            except Exception:
                os.chmod(wav_path, 0o644)

            print(f"  ✅ Oluşturuldu: {dosya_adi}.wav")
            return True
        else:
            print(f"  ❌ WAV dönüşümü başarısız: {dosya_adi}")
            return False

    except Exception as e:
        print(f"  ❌ Hata ({dosya_adi}): {e}")
        return False
    finally:
        if os.path.exists(mp3_path):
            os.unlink(mp3_path)


def main():
    print(f"\n🎵 VoiceAI IVR Ses Dosyaları Oluşturuluyor")
    print(f"📁 Hedef: {SOUNDS_DIR}\n")

    # ffmpeg kontrolü
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        print("❌ ffmpeg bulunamadı! Yükleniyor...")
        subprocess.run(["apt-get", "install", "-y", "ffmpeg", "-q"])

    basarili = 0
    basarisiz = 0

    for dosya_adi, bilgi in IVR_SESLER.items():
        if ses_olustur(dosya_adi, bilgi["lang"], bilgi["text"]):
            basarili += 1
        else:
            basarisiz += 1

    print(f"\n📊 Sonuç: {basarili} başarılı, {basarisiz} başarısız")
    print(f"📁 Dosyalar: {SOUNDS_DIR}/")

    # Asterisk reload
    print("\n🔄 Asterisk yeniden yükleniyor...")
    result = subprocess.run(
        ["asterisk", "-rx", "core reload"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ Asterisk yeniden yüklendi")
    else:
        print(f"⚠️  Asterisk reload: {result.stderr}")

    print("\n✅ IVR ses dosyaları hazır!")


if __name__ == "__main__":
    main()
