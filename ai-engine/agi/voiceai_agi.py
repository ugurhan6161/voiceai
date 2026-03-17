#!/usr/bin/env python3
"""
VoiceAI — AGI Tabanlı Sesli Resepsiyonist
==========================================
Asterisk AGI üzerinden çalışır. Ses kayıt/çalma AGI ile yapılır.
TTS: XTTS (Docker container)
STT: Whisper (Docker container)
LLM: Ollama (Docker container)

Bu script Asterisk dialplan'dan çağrılır:
  exten => 100,1,Answer()
  exten => 100,n,AGI(voiceai_agi.py,${FIRMA_ID},${TEMPLATE_ID},${LANG})
"""
import sys
import os
import json
import subprocess
import time
import re
import hashlib
import threading
import queue

# ─── YAPILANDIRMA ────────────────────────────────────────
LOG_FILE = "/var/log/asterisk/voiceai_conv.log"
CACHE_DIR = "/tmp/tts_cache"
SOUNDS_DIR = "/var/lib/asterisk/sounds/voiceai"
MIN_BYTES = 4000  # Minimum ses dosyası boyutu (sessizlik filtresi)

# Servis URL'leri (Docker container'lar)
XTTS_URL = os.getenv("XTTS_URL", "http://172.18.0.7:5002")
WHISPER_URL = os.getenv("WHISPER_URL", "http://172.18.0.11:9000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://172.18.0.8:11434")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(SOUNDS_DIR, exist_ok=True)

# ─── DİL AYARLARI ────────────────────────────────────────
KARSILAMA = {
    "otel": {
        "tr": "Merhaba, otel resepsiyonumuza hoş geldiniz. Size nasıl yardımcı olabilirim?",
        "en": "Hello, welcome to our hotel reception. How can I help you?",
        "ar": "مرحبا، أهلا بكم في استقبال فندقنا. كيف يمكنني مساعدتك؟",
        "ru": "Здравствуйте, добро пожаловать на ресепшн нашего отеля. Чем могу помочь?",
    },
    "klinik_poliklinik": {
        "tr": "Merhaba, kliniğimizi aradığınız için teşekkür ederiz. Nasıl yardımcı olabilirim?",
        "en": "Hello, thank you for calling our clinic. How can I help you?",
        "ar": "مرحبا، شكرا لاتصالك بعيادتنا. كيف يمكنني مساعدتك؟",
        "ru": "Здравствуйте, спасибо за звонок в нашу клинику. Чем могу помочь?",
    },
}

SISTEM_PROMPTLARI = {
    "tr": "Sen bir yapay zeka sesli asistanısın. Türkçe konuşuyorsun. Kısa ve net cevaplar ver. Maksimum 2 cümle kullan.",
    "en": "You are an AI voice assistant. Speak in English. Give short and clear answers. Use maximum 2 sentences.",
    "ar": "أنت مساعد صوتي بالذكاء الاصطناعي. تحدث باللغة العربية. أعط إجابات قصيرة وواضحة.",
    "ru": "Вы голосовой ИИ-ассистент. Говорите по-русски. Давайте короткие и чёткие ответы.",
}

TEKRAR_MSG = {
    "tr": "Sizi duyamadım, tekrar eder misiniz?",
    "en": "I couldn't hear you, could you repeat?",
    "ar": "لم أسمعك، هل يمكنك الإعادة؟",
    "ru": "Я вас не расслышал, повторите пожалуйста?",
}

HATA_MSG = {
    "tr": "Üzgünüm, sizi anlayamadım. Tekrar eder misiniz?",
    "en": "I'm sorry, I didn't understand. Could you repeat that?",
    "ar": "آسف، لم أفهم. هل يمكنك التكرار؟",
    "ru": "Извините, я не понял. Не могли бы вы повторить?",
}

VEDA_MSG = {
    "tr": "İyi günler, görüşmek üzere!",
    "en": "Have a great day, goodbye!",
    "ar": "أتمنى لك يوماً سعيداً، وداعاً!",
    "ru": "Хорошего дня, до свидания!",
}

FILLER_MSG = {
    "tr": ["Tabii.", "Anlıyorum.", "Bir saniye.", "Peki."],
    "en": ["Sure.", "Got it.", "One moment.", "Okay."],
    "ar": ["حسناً.", "فهمت.", "لحظة.", "طيب."],
    "ru": ["Конечно.", "Понял.", "Секунду.", "Хорошо."],
}


# ─── AGI YARDIMCI FONKSİYONLAR ──────────────────────────
def log(msg, pid=None):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}][{pid}] {msg}" if pid else f"[{ts}] {msg}"
    sys.stderr.write(line + "\n")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def agi_send(cmd):
    """AGI komutu gönder ve yanıt al"""
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def read_env():
    """AGI ortam değişkenlerini oku"""
    env = {}
    while True:
        line = sys.stdin.readline().strip()
        if not line:
            break
        if ":" in line:
            key, val = line.split(":", 1)
            env[key.strip()] = val.strip()
    return env


def get_caller_number():
    """Arayan numarayı al"""
    result = agi_send("GET VARIABLE CALLERID(num)")
    match = re.search(r'\(([+\d]+)\)', result)
    if match:
        return match.group(1)
    return "Unknown"


# ─── TTS (XTTS) ─────────────────────────────────────────
def tts_to_wav(text, lang, outfile, pid=None):
    """XTTS ile metni sese çevir"""
    if not text or not text.strip():
        return False

    clean = text.replace('"', '').replace("'", '').replace('\n', ' ').strip()[:400]
    if not clean:
        return False

    # Cache kontrol
    cache_key = hashlib.md5(f"{clean}{lang}".encode()).hexdigest()
    cache_file = f"{CACHE_DIR}/{cache_key}.wav"
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
        subprocess.run(f"cp {cache_file} {outfile}", shell=True)
        log(f"[TTS-CACHE] '{clean[:50]}'", pid)
        return True

    t0 = time.time()
    try:
        import requests
        resp = requests.post(
            f"{XTTS_URL}/synthesize",
            json={"text": clean, "language": lang},
            timeout=30
        )
        if resp.status_code == 200:
            result = resp.json()
            audio_path = result.get("audio_path", "")
            if audio_path and os.path.exists(audio_path):
                # Asterisk formatına dönüştür (8kHz mono PCM)
                subprocess.run(
                    f"ffmpeg -y -i {audio_path} -ar 8000 -ac 1 -acodec pcm_s16le {outfile} -loglevel quiet",
                    shell=True
                )
                size = os.path.getsize(outfile) if os.path.exists(outfile) else 0
                if size > 100:
                    subprocess.run(f"cp {outfile} {cache_file}", shell=True)
                log(f"[TTS-XTTS] {time.time()-t0:.2f}sn | '{clean[:60]}' | {size}b", pid)
                return size > 100
            else:
                log(f"[TTS-XTTS] Dosya bulunamadı: {audio_path}", pid)
        else:
            log(f"[TTS-XTTS HATA] {resp.status_code} - {resp.text[:100]}", pid)
    except Exception as e:
        log(f"[TTS-XTTS HATA] {e}", pid)

    # Fallback: gTTS
    try:
        from gtts import gTTS
        mp3 = outfile.replace('.wav', '.mp3')
        gTTS(text=clean, lang=lang if lang in ['tr', 'en', 'ar'] else 'tr').save(mp3)
        subprocess.run(
            f"ffmpeg -y -i {mp3} -ar 8000 -ac 1 -acodec pcm_s16le {outfile} -loglevel quiet",
            shell=True
        )
        try:
            os.remove(mp3)
        except:
            pass
        size = os.path.getsize(outfile) if os.path.exists(outfile) else 0
        log(f"[TTS-GTTS] {time.time()-t0:.2f}sn | '{clean[:60]}' | {size}b", pid)
        return size > 100
    except Exception as e:
        log(f"[TTS-GTTS HATA] {e}", pid)

    return False


def say(text, lang, pid, tag, interruptible=False):
    """Ses çal. interruptible=True → tuşa basılınca dur"""
    wav = f"/tmp/{tag}_{pid}.wav"
    if not tts_to_wav(text, lang, wav, pid):
        return None

    base = wav.replace('.wav', '')
    if interruptible:
        result = agi_send(f'STREAM FILE {base} "0123456789#*"')
        try:
            os.remove(wav)
        except:
            pass
        m = re.search(r'result=(\d+)', result)
        if m:
            code = int(m.group(1))
            if code > 0:
                return chr(code)
        return None
    else:
        agi_send(f'STREAM FILE {base} ""')
        try:
            os.remove(wav)
        except:
            pass
        return None


def get_digit(timeout_ms=6000):
    """Kullanıcıdan tek tuş bekle"""
    result = agi_send(f"WAIT FOR DIGIT {timeout_ms}")
    match = re.search(r'result=(-?\d+)', result)
    if match:
        code = int(match.group(1))
        if code > 0:
            return chr(code)
    return None


# ─── STT (Whisper) ───────────────────────────────────────
def stt_whisper(audio_file, lang, pid=None):
    """Whisper ile ses → metin"""
    t0 = time.time()

    # Normalize audio
    norm = f"/tmp/norm_{pid}_{int(time.time())}.wav"
    subprocess.run(
        f"ffmpeg -y -i {audio_file} -ar 16000 -ac 1 -acodec pcm_s16le "
        f"-af 'highpass=f=80,lowpass=f=8000,volume=2.0' "
        f"{norm} -loglevel quiet",
        shell=True
    )
    if not os.path.exists(norm) or os.path.getsize(norm) < 200:
        norm = audio_file

    try:
        import requests
        with open(norm, 'rb') as f:
            resp = requests.post(
                f"{WHISPER_URL}/transcribe",
                files={"audio": (f"audio_{lang}.wav", f, "audio/wav")},
                data={"language": lang} if lang != "tr" else {},
                timeout=30
            )

        if norm != audio_file:
            try:
                os.remove(norm)
            except:
                pass

        if resp.status_code == 200:
            result = resp.json()
            text = result.get("text", "").strip()
            # Garbage filter
            if len(text) < 2:
                return ""
            text = text.strip('.,!? ')
            log(f"[STT] {time.time()-t0:.2f}sn | '{text}'", pid)
            return text
        else:
            log(f"[STT HATA] {resp.status_code}", pid)
    except Exception as e:
        log(f"[STT HATA] {e}", pid)

    return ""


# ─── LLM (Ollama) ────────────────────────────────────────
def get_ai_response(user_text, lang, template_id, history, pid):
    """Ollama ile AI yanıt al"""
    t0 = time.time()

    system_prompt = SISTEM_PROMPTLARI.get(lang, SISTEM_PROMPTLARI["tr"])

    sablon_promptlari = {
        "tr": {
            "otel": "Otel resepsiyonistisin. Rezervasyon al, oda bilgisi ver, müşteriye yardımcı ol.",
            "klinik_poliklinik": "Klinik asistanısın. Randevu al, doktor bilgisi ver.",
            "hali_yikama": "Halı yıkama firması çalışanısın. Sipariş al, fiyat bilgisi ver.",
            "su_bayii": "Su bayii çalışanısın. Su siparişi al.",
        },
        "en": {
            "otel": "You are a hotel receptionist. Take reservations, provide room info.",
            "klinik_poliklinik": "You are a clinic assistant. Schedule appointments.",
        },
    }

    lang_prompts = sablon_promptlari.get(lang, sablon_promptlari.get("tr", {}))
    sablon_prompt = lang_prompts.get(template_id, "Müşteriye yardımcı ol.")
    full_system = f"{system_prompt}\n{sablon_prompt}"

    messages = [{"role": "system", "content": full_system}]
    for msg in history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    try:
        import requests
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "llama3.1:8b",
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        if resp.status_code == 200:
            result = resp.json()
            ai_text = result.get("message", {}).get("content", "")
            log(f"[LLM] {time.time()-t0:.2f}sn | '{ai_text[:80]}'", pid)
            return ai_text
        else:
            log(f"[LLM HATA] {resp.status_code}", pid)
    except Exception as e:
        log(f"[LLM HATA] {e}", pid)

    return HATA_MSG.get(lang, HATA_MSG["tr"])


# ─── TRANSFER KONTROLÜ ──────────────────────────────────
TRANSFER_KEYWORDS = {
    "tr": ["yetkili", "müdür", "operatör", "bağla", "aktarım", "insan", "gerçek kişi"],
    "en": ["manager", "operator", "transfer", "human", "real person", "connect"],
    "ar": ["مدير", "موظف", "تحويل", "شخص حقيقي"],
    "ru": ["менеджер", "оператор", "перевод", "человек"],
}


def check_transfer(text, lang):
    """Transfer gerekli mi kontrol et"""
    keywords = TRANSFER_KEYWORDS.get(lang, TRANSFER_KEYWORDS["tr"])
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


# ─── KONUŞMA DÖNGÜSÜ ────────────────────────────────────
def conversation_loop(firma_id, template_id, lang, pid, max_turns=15, silence_limit=3):
    """Ana konuşma döngüsü — AGI RECORD FILE ile ses kayıt"""
    history = []
    turn = 0
    silence_count = 0
    filler_idx = 0
    fillers = FILLER_MSG.get(lang, FILLER_MSG["tr"])

    # Karşılama
    templates = KARSILAMA.get(template_id, KARSILAMA.get("otel", {}))
    greeting = templates.get(lang, templates.get("tr", "Merhaba!"))
    say(greeting, lang, pid, "greeting")
    history.append({"role": "assistant", "content": greeting})

    while turn < max_turns:
        turn += 1

        # AGI RECORD FILE — bu çalışan yöntem!
        rec = f"/tmp/rec_{pid}_{turn}"
        # s=1 → 1 saniye sessizlik sonrası dur
        # 8000 → max 8 saniye
        # # → # tuşu ile bitir
        agi_send(f'RECORD FILE {rec} wav "#" 8000 0 s=1')
        audio = rec + ".wav"

        size = os.path.getsize(audio) if os.path.exists(audio) else 0
        log(f"[REC] turn={turn} size={size}b", pid)

        if size < MIN_BYTES:
            silence_count += 1
            try:
                os.remove(audio)
            except:
                pass
            if silence_count >= silence_limit:
                log(f"[SESSIZLIK] {silence_count} kez sessiz, çıkış", pid)
                break
            if silence_count == 1:
                say(TEKRAR_MSG.get(lang, TEKRAR_MSG["tr"]), lang, pid, f"repeat_{turn}")
            continue

        silence_count = 0

        # STT
        text = stt_whisper(audio, lang, pid)
        try:
            os.remove(audio)
        except:
            pass

        if not text or len(text.strip()) < 2:
            continue

        log(f"[MÜŞTERİ#{turn}] '{text}'", pid)

        # Transfer kontrolü
        if check_transfer(text, lang):
            transfer_msg = {
                "tr": "Sizi yetkili kişiye bağlıyorum, lütfen bekleyin.",
                "en": "I'm connecting you to a representative, please hold.",
                "ar": "أقوم بتحويلك إلى المسؤول، يرجى الانتظار.",
                "ru": "Соединяю вас с ответственным лицом, подождите.",
            }
            say(transfer_msg.get(lang, transfer_msg["tr"]), lang, pid, "transfer")
            # Firma dahilisine transfer
            agi_send(f"EXEC Transfer PJSIP/firma_{firma_id}_dahili")
            return

        # Filler (kısa bekleme sesi)
        short_acks = {'evet', 'hayır', 'tamam', 'olur', 'peki', 'yes', 'no', 'okay'}
        if not (len(text.split()) <= 2 and any(w in text.lower() for w in short_acks)):
            say(fillers[filler_idx % len(fillers)], lang, pid, f"filler_{turn}")
            filler_idx += 1

        # LLM yanıt al
        ai_response = get_ai_response(text, lang, template_id, history, pid)

        # Yanıtı çal
        say(ai_response, lang, pid, f"ai_{turn}")

        # Geçmişe ekle
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": ai_response})

    # Veda
    say(VEDA_MSG.get(lang, VEDA_MSG["tr"]), lang, pid, "bye")


# ─── ANA FONKSİYON ──────────────────────────────────────
def main():
    os.environ['HOME'] = '/tmp'
    env = read_env()
    args = sys.argv[1:]

    firma_id = args[0] if len(args) > 0 else "1"
    template_id = args[1] if len(args) > 1 else "otel"
    lang = args[2] if len(args) > 2 else "tr"

    pid = os.getpid()
    t0 = time.time()

    log(f"{'='*50}", pid)
    log(f"[BASLADI] firma={firma_id} şablon={template_id} dil={lang}", pid)

    caller = get_caller_number()
    log(f"[ARAYAN] {caller}", pid)

    # KVKK bildirimi
    kvkk_msg = {
        "tr": "Bu hattı arayarak kişisel verilerinizin işlenmesini kabul etmiş sayılırsınız. KVKK metnini dinlemek için 9'a basın.",
        "en": "By calling this line, you accept the processing of your personal data. Press 9 to hear the privacy policy.",
    }
    pressed = say(kvkk_msg.get(lang, kvkk_msg["tr"]), lang, pid, "kvkk", interruptible=True)
    if pressed == "9":
        kvkk_full = {
            "tr": "Kişisel verileriniz yalnızca hizmet sunumu amacıyla işlenmekte, üçüncü kişilerle paylaşılmamakta ve yasal süreler sonunda silinmektedir.",
            "en": "Your personal data is processed only for service delivery, not shared with third parties, and deleted after legal periods.",
        }
        say(kvkk_full.get(lang, kvkk_full["tr"]), lang, pid, "kvkk_full")

    log(f"[KVKK] bildirildi", pid)

    # Konuşma döngüsü
    conversation_loop(firma_id, template_id, lang, pid)

    log(f"[SONU] {time.time()-t0:.1f}sn | dil:{lang}", pid)
    log(f"{'='*50}", pid)


if __name__ == "__main__":
    main()
