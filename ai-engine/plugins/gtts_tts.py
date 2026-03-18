"""
VoiceAI — gTTS / XTTS TTS Plugin (LiveKit Agents uyumlu)
HTTP tabanlı TTS servisini LiveKit TTS arayüzüne bağlar.
Çok dilli: TR / EN / AR / RU
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import httpx
from livekit.agents import tts, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.tts import (
    AudioEmitter,
    ChunkedStream,
    TTSCapabilities,
)

logger = logging.getLogger(__name__)

# Desteklenen diller
SUPPORTED_LANGUAGES = {"tr", "en", "ar", "ru", "de", "fr"}

# TTS servisi çıktı: 8kHz mono PCM WAV
_SAMPLE_RATE = 8000
_NUM_CHANNELS = 1


@dataclass
class GttsTTSOptions:
    base_url: str = "http://xtts:5002"
    language: str = "tr"
    timeout: float = 30.0


class GttsTTS(tts.TTS):
    """
    LiveKit TTS eklentisi — gTTS / XTTS HTTP servisi.

    Kullanım:
        tts_engine = GttsTTS(base_url="http://xtts:5002", language="tr")
    """

    def __init__(
        self,
        *,
        base_url: str = "http://xtts:5002",
        language: str = "tr",
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=_SAMPLE_RATE,
            num_channels=_NUM_CHANNELS,
        )
        self._options = GttsTTSOptions(
            base_url=base_url.rstrip("/"),
            language=language if language in SUPPORTED_LANGUAGES else "tr",
            timeout=timeout,
        )

    @property
    def model(self) -> str:
        return "gtts"

    @property
    def provider(self) -> str:
        return "voiceai-tts"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "GttsChunkedStream":
        return GttsChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            options=self._options,
        )

    async def aclose(self) -> None:
        pass


class GttsChunkedStream(ChunkedStream):
    """
    gTTS HTTP servisinden ses alarak LiveKit AudioEmitter'a aktarır.
    TTS servisi WAV (8kHz, mono, PCM 16-bit) döndürür.
    """

    def __init__(
        self,
        *,
        tts: GttsTTS,
        input_text: str,
        conn_options: APIConnectOptions,
        options: GttsTTSOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._options = options

    async def _run(self, output_emitter: AudioEmitter) -> None:
        """HTTP servisinden ses al ve AudioEmitter'a gönder."""
        request_id = str(uuid.uuid4())

        output_emitter.initialize(
            request_id=request_id,
            sample_rate=_SAMPLE_RATE,
            num_channels=_NUM_CHANNELS,
            mime_type="audio/wav",
        )

        async with httpx.AsyncClient(timeout=self._options.timeout) as client:
            try:
                resp = await client.post(
                    f"{self._options.base_url}/synthesize",
                    json={
                        "text": self._input_text,
                        "language": self._options.language,
                        "voice": "default",
                    },
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"TTS servisi hata döndürdü (HTTP {exc.response.status_code}). "
                    f"Servis durumunu kontrol edin: {self._options.base_url}/health"
                ) from exc
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"TTS servisine bağlanılamadı ({self._options.base_url}). "
                    f"Servisin çalışıp çalışmadığını doğrulayın."
                ) from exc

        data = resp.json()
        audio_b64: str = data.get("audio_base64", "")

        if not audio_b64:
            logger.warning("TTS servisi boş ses döndürdü: '%s'", self._input_text[:40])
            output_emitter.end_input()
            return

        import base64
        wav_bytes = base64.b64decode(audio_b64)

        # WAV header'ını atla (44 byte standart WAV header)
        pcm_data = _strip_wav_header(wav_bytes)

        output_emitter.push(pcm_data)
        output_emitter.end_input()

        logger.debug(
            "TTS tamamlandı: '%s...' → %d bytes PCM (dil: %s)",
            self._input_text[:30],
            len(pcm_data),
            self._options.language,
        )


def _strip_wav_header(wav_bytes: bytes) -> bytes:
    """
    WAV dosyasını ayrıştırarak ham PCM verisini döndür.
    wave modülünü kullanarak header'ı dinamik olarak işler.
    Asterisk uyumlu 8kHz mono WAV formatını destekler.
    """
    import wave
    import io

    try:
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            pcm = wf.readframes(wf.getnframes())
        return pcm
    except Exception:
        # Header parse başarısız — tüm veriyi döndür
        return wav_bytes
