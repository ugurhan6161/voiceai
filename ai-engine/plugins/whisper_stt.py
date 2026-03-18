"""
VoiceAI — Whisper STT Plugin (LiveKit Agents uyumlu)
HTTP tabanlı Faster-Whisper servisini LiveKit STT arayüzüne bağlar.
Çok dilli: TR / EN / AR / RU
"""
from __future__ import annotations

import io
import wave
import logging
import asyncio
import uuid
from dataclasses import dataclass
from typing import Union

import httpx
from livekit import rtc
from livekit.agents import (
    stt,
    utils,
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)
from livekit.agents.stt import (
    SpeechData,
    SpeechEvent,
    SpeechEventType,
    STTCapabilities,
)
from livekit.agents.utils import is_given

logger = logging.getLogger(__name__)

# Dil kodu → Whisper dil kodu eşleşmesi
LANGUAGE_MAP: dict[str, str] = {
    "tr": "tr",
    "en": "en",
    "ar": "ar",
    "ru": "ru",
    "de": "de",
    "fr": "fr",
}


@dataclass
class WhisperSTTOptions:
    base_url: str = "http://whisper:9000"
    language: str = "tr"
    timeout: float = 30.0


class WhisperSTT(stt.STT):
    """
    LiveKit STT eklentisi — Faster-Whisper HTTP servisi.

    Kullanım:
        stt = WhisperSTT(base_url="http://whisper:9000", language="tr")
    """

    def __init__(
        self,
        *,
        base_url: str = "http://whisper:9000",
        language: str = "tr",
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            capabilities=STTCapabilities(
                streaming=False,
                interim_results=False,
            )
        )
        self._options = WhisperSTTOptions(
            base_url=base_url.rstrip("/"),
            language=LANGUAGE_MAP.get(language, language),
            timeout=timeout,
        )

    @property
    def model(self) -> str:
        return "faster-whisper-turbo"

    @property
    def provider(self) -> str:
        return "voiceai-whisper"

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> SpeechEvent:
        """Ses tamponunu metne çevir (HTTP POST → Whisper servisi)."""
        lang = (
            LANGUAGE_MAP.get(language, language)
            if is_given(language)
            else self._options.language
        )

        # AudioBuffer → WAV bytes
        wav_data = _audio_buffer_to_wav(buffer)

        async with httpx.AsyncClient(timeout=self._options.timeout) as client:
            try:
                resp = await client.post(
                    f"{self._options.base_url}/transcribe",
                    files={"audio": ("audio.wav", wav_data, "audio/wav")},
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Whisper servisi hata döndürdü (HTTP {exc.response.status_code}). "
                    f"Servis durumunu kontrol edin: {self._options.base_url}/health"
                ) from exc
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"Whisper servisine bağlanılamadı ({self._options.base_url}). "
                    f"Servisin çalışıp çalışmadığını doğrulayın."
                ) from exc

        result = resp.json()
        text = result.get("text", "").strip()
        detected_lang = result.get("language", lang)

        logger.debug(
            "Whisper transkript: '%s' (dil: %s, süre: %.2fs)",
            text[:60],
            detected_lang,
            result.get("duration", 0.0),
        )

        return SpeechEvent(
            type=SpeechEventType.FINAL_TRANSCRIPT,
            request_id=str(uuid.uuid4()),
            alternatives=[
                SpeechData(
                    language=detected_lang,
                    text=text,
                    confidence=result.get("language_probability", 1.0),
                )
            ],
        )

    async def aclose(self) -> None:
        pass


def _audio_buffer_to_wav(buffer: utils.AudioBuffer) -> bytes:
    """
    LiveKit AudioBuffer (AudioFrame listesi veya tek frame) → WAV bytes.
    Whisper 16kHz mono giriş tercih eder; aynı sample rate ile gönderilir.
    """
    frame: rtc.AudioFrame
    if isinstance(buffer, list):
        frame = rtc.combine_audio_frames(buffer)
    else:
        frame = buffer

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(frame.num_channels)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(frame.sample_rate)
        wf.writeframes(bytes(frame.data))

    return buf.getvalue()
