"""
VoiceAI Platform — LiveKit Gerçek Zamanlı Konuşma Ajanı
=========================================================
LiveKit Agents framework kullanarak gerçek zamanlı sesli AI konuşması.
STT: Faster-Whisper (HTTP)
LLM: Ollama (OpenAI uyumlu API)
TTS: gTTS / XTTS (HTTP)
VAD: Silero

Çalıştırmak için:
  python livekit_agent.py start
  python livekit_agent.py dev   # geliştirme modu
"""
from __future__ import annotations

import json
import logging
import os
import sys

# Proje modüllerine erişim için path ayarla
sys.path.insert(0, "/app")

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    function_tool,
)
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import openai as lk_openai
from livekit.plugins import silero

from plugins import GttsTTS, WhisperSTT

logger = logging.getLogger(__name__)

# ── Ortam değişkenleri ─────────────────────────────────────────────────────
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://livekit:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")

WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:9000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
XTTS_URL = os.getenv("XTTS_URL", "http://xtts:5002")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "tr")

# ── Varsayılan sistem promptu ──────────────────────────────────────────────
_DEFAULT_INSTRUCTIONS = """Sen profesyonel bir yapay zeka sesli asistanısın.
Kullanıcılara Türkçe yardımcı oluyorsun. Kısa, net ve kibar cevaplar ver.
Gerektiğinde randevu al, bilgi ver ve yönlendir."""


def _load_instructions(room_metadata: str | None, default_lang: str) -> tuple[str, str]:
    """
    Oda meta verisinden firma ayarlarını yükle.

    room_metadata JSON formatında beklenir:
    {
        "firma_id": "firma_1",
        "template": "otel",
        "firma_adi": "Örnek Otel",
        "asistan_adi": "Ayşe",
        "language": "tr"
    }

    Returns:
        (instructions, language)
    """
    lang = default_lang
    instructions = _DEFAULT_INSTRUCTIONS

    if not room_metadata:
        return instructions, lang

    try:
        meta = json.loads(room_metadata)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Oda meta verisi JSON değil, varsayılan ayarlar kullanılıyor")
        return instructions, lang

    lang = meta.get("language", default_lang)
    template_id = meta.get("template", "")
    firma_adi = meta.get("firma_adi", "")
    asistan_adi = meta.get("asistan_adi", "Asistan")

    if template_id:
        try:
            from templates.registry import get_template

            tmpl = get_template(template_id)
            if tmpl and firma_adi:
                instructions = tmpl.get_system_prompt(firma_adi, asistan_adi)
                logger.info(
                    "Şablon yüklendi: %s (firma: %s, asistan: %s)",
                    template_id,
                    firma_adi,
                    asistan_adi,
                )
            elif tmpl:
                instructions = tmpl.get_system_prompt(template_id, asistan_adi)
        except Exception as exc:
            logger.warning("Şablon yüklenemedi (%s): %s", template_id, exc)

    return instructions, lang


# ── AgentServer kurulumu ───────────────────────────────────────────────────
server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """
    Her yeni LiveKit oturumu için çağrılan giriş noktası.
    Oda meta verisinden firma ayarlarını okur ve ajan başlatır.
    """
    logger.info("Yeni oturum başladı — oda: %s", ctx.room.name)

    # Oda meta verisinden ayarları yükle
    instructions, lang = _load_instructions(
        ctx.room.metadata, DEFAULT_LANGUAGE
    )

    logger.info("Dil: %s | İlk prompt: %s...", lang, instructions[:60])

    # ── STT ───────────────────────────────────────────────────
    stt_engine = WhisperSTT(
        base_url=WHISPER_URL,
        language=lang,
    )

    # ── LLM (Ollama — OpenAI uyumlu API) ─────────────────────
    # Ollama'nın OpenAI uyumlu endpoint'ini kullan.
    # api_key değeri Ollama tarafından doğrulanmaz, ancak
    # OpenAI SDK arayüzü için zorunlu bir parametre olduğundan
    # "ollama" placeholder değeri geçilir.
    llm_engine = lk_openai.LLM(
        base_url=f"{OLLAMA_URL}/v1",
        api_key="ollama",  # SDK zorunlu parametre; Ollama bu değeri doğrulamaz
        model=OLLAMA_MODEL,
    )

    # ── TTS ───────────────────────────────────────────────────
    tts_engine = GttsTTS(
        base_url=XTTS_URL,
        language=lang,
    )

    # ── VAD (Ses Aktivite Algılama) ───────────────────────────
    vad_engine = silero.VAD.load()

    # ── Ajan ve Oturum ────────────────────────────────────────
    agent = Agent(instructions=instructions)

    session = AgentSession(
        stt=stt_engine,
        llm=llm_engine,
        tts=tts_engine,
        vad=vad_engine,
        allow_interruptions=True,
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
    )

    await session.start(agent=agent, room=ctx.room)

    # İlk karşılama mesajı
    await session.generate_reply(
        instructions=_greeting_instructions(lang)
    )

    logger.info("Ajan hazır — oturum dinleniyor")


def _greeting_instructions(lang: str) -> str:
    """Dile göre karşılama talimatı üret."""
    greetings = {
        "tr": "Kullanıcıyı Türkçe sıcak bir şekilde karşıla ve nasıl yardımcı olabileceğini sor.",
        "en": "Greet the user warmly in English and ask how you can help.",
        "ar": "استقبل المستخدم بدفء باللغة العربية واسأل كيف يمكنك المساعدة.",
        "ru": "Тепло поприветствуйте пользователя на русском языке и спросите, как вы можете помочь.",
    }
    return greetings.get(lang, greetings["tr"])


# ── Giriş noktası ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    cli.run_app(server)
