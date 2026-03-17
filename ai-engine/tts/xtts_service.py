"""
VoiceAI Platform — TTS Servisi (Çok Dilli gTTS)
TR / EN / AR / RU dil desteği
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import tempfile
import base64
import subprocess
import logging
import time
import hashlib
from pathlib import Path

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

app = FastAPI(title="VoiceAI TTS Service")
logger = logging.getLogger(__name__)

# Desteklenen diller ve gTTS kodları
DESTEKLENEN_DILLER = {
    "tr": "tr",   # Türkçe
    "en": "en",   # English
    "ar": "ar",   # العربية
    "ru": "ru",   # Русский
    "de": "de",   # Deutsch
    "fr": "fr",   # Français
}

# Dil bazlı karşılama metinleri
KARSILAMA_METINLERI = {
    "tr": "Merhaba, otel resepsiyonumuza hoş geldiniz. Size nasıl yardımcı olabilirim?",
    "en": "Hello, welcome to our hotel reception. How can I help you?",
    "ar": "مرحبا، أهلا بكم في استقبال فندقنا. كيف يمكنني مساعدتك؟",
    "ru": "Здравствуйте, добро пожаловать на ресепшн нашего отеля. Чем могу помочь?",
}


class TTSRequest(BaseModel):
    text: str
    language: str = "tr"
    voice: str = "default"


class TTSResponse(BaseModel):
    status: str
    text: str
    language: str = "tr"
    audio_base64: str = None
    audio_path: str = None
    format: str = "wav"
    sample_rate: int = 8000


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "tts",
        "tts_engine": "gTTS" if gTTS else "none",
        "supported_languages": list(DESTEKLENEN_DILLER.keys()),
        "ffmpeg_available": _check_ffmpeg()
    }


@app.post("/synthesize", response_model=TTSResponse)
async def synthesize(request: TTSRequest):
    """
    Metni sese çevir - çok dilli gTTS
    Desteklenen diller: tr, en, ar, ru, de, fr
    Format: 8kHz mono ulaw WAV (Asterisk uyumlu)
    """
    if not gTTS:
        raise HTTPException(status_code=500, detail="gTTS kurulu değil. pip install gtts")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Metin boş olamaz")

    # Dil kodunu normalize et
    lang = request.language.lower().strip()
    if lang not in DESTEKLENEN_DILLER:
        logger.warning(f"Desteklenmeyen dil: {lang}, Türkçe kullanılıyor")
        lang = "tr"

    gtts_lang = DESTEKLENEN_DILLER[lang]

    try:
        logger.info(f"TTS isteği: '{request.text[:50]}...' (dil: {lang})")

        # Asterisk sounds klasörü
        voiceai_sounds_dir = "/var/lib/asterisk/sounds/voiceai"
        os.makedirs(voiceai_sounds_dir, exist_ok=True)

        # Benzersiz dosya adı
        timestamp = int(time.time() * 1000)
        text_hash = hashlib.md5(f"{request.text}{lang}".encode()).hexdigest()[:8]
        filename = f"tts_{lang}_{timestamp}_{text_hash}"

        # Geçici MP3 dosyası
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            mp3_path = mp3_file.name

        wav_path = os.path.join(voiceai_sounds_dir, f"{filename}.wav")

        try:
            # 1. gTTS ile MP3 üret (dil parametreli)
            tts = gTTS(text=request.text, lang=gtts_lang, slow=False)
            tts.save(mp3_path)
            logger.info(f"✅ MP3 üretildi: {mp3_path} (dil: {gtts_lang})")

            # 2. ffmpeg ile Asterisk uyumlu WAV'a çevir
            ffmpeg_cmd = [
                "ffmpeg", "-i", mp3_path,
                "-ar", "8000",          # 8kHz
                "-ac", "1",             # Mono
                "-acodec", "pcm_s16le", # PCM 16-bit signed (Asterisk wav uyumlu)
                "-f", "wav",
                "-y",                   # Üzerine yaz
                wav_path
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"ffmpeg hatası: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"Ses dönüşümü başarısız: {result.stderr}")

            logger.info(f"✅ WAV dönüştürüldü: {wav_path}")

            # Dosya izinleri (Asterisk okuyabilmesi için)
            try:
                os.chown(wav_path, 14, 119)  # asterisk:asterisk
                os.chmod(wav_path, 0o644)
            except Exception as perm_err:
                logger.warning(f"İzin ayarlanamadı: {perm_err}")

            # 3. Base64 encode
            with open(wav_path, "rb") as f:
                audio_data = f.read()

            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            logger.info(f"✅ TTS tamamlandı: {len(audio_data)} bytes, dil: {lang}")

            return TTSResponse(
                status="ok",
                text=request.text,
                language=lang,
                audio_base64=audio_base64,
                audio_path=wav_path,
                format="wav",
                sample_rate=8000
            )

        finally:
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Ses dönüşümü zaman aşımı")
    except Exception as e:
        logger.error(f"TTS hatası: {e}")
        raise HTTPException(status_code=500, detail=f"TTS başarısız: {str(e)}")


@app.get("/voices")
async def voices():
    """Desteklenen diller"""
    return {
        "voices": ["default"],
        "languages": list(DESTEKLENEN_DILLER.keys()),
        "language_names": {
            "tr": "Türkçe",
            "en": "English",
            "ar": "العربية",
            "ru": "Русский",
            "de": "Deutsch",
            "fr": "Français",
        },
        "engine": "gTTS"
    }


@app.get("/karsilama/{lang}")
async def karsilama_metni(lang: str = "tr"):
    """Dile göre karşılama metnini döndür"""
    return {
        "lang": lang,
        "text": KARSILAMA_METINLERI.get(lang, KARSILAMA_METINLERI["tr"])
    }


def _check_ffmpeg() -> bool:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False
