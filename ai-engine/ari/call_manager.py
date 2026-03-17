"""
VoiceAI — Call Manager (Çok Dilli)
TR / EN / AR / RU dil desteği
Çağrı yaşam döngüsünü yönetir ve AI pipeline ile entegre eder.
"""
import os
import asyncio
import logging
import time
import wave
import io
from typing import Optional, Dict
from datetime import datetime
import httpx
import aiohttp

from .ari_client import ARIClient
from .audio_handler import AudioHandler, VADProcessor

logger = logging.getLogger(__name__)

# Dil bazlı karşılama metinleri (şablon + dil kombinasyonu)
KARSILAMA_METINLERI = {
    "otel": {
        "tr": "Merhaba, otel resepsiyonumuza hoş geldiniz. Size nasıl yardımcı olabilirim?",
        "en": "Hello, welcome to our hotel reception. How can I help you?",
        "ar": "مرحبا، أهلا بكم في استقبال فندقنا. كيف يمكنني مساعدتك؟",
        "ru": "Здравствуйте, добро пожаловать на ресепшн нашего отеля. Чем могу помочь?",
    },
    "klinik_poliklinik": {
        "tr": "Merhaba, kliniğimizi aradığınız için teşekkür ederiz. Randevu almak ister misiniz?",
        "en": "Hello, thank you for calling our clinic. Would you like to make an appointment?",
        "ar": "مرحبا، شكرا لاتصالك بعيادتنا. هل تريد حجز موعد؟",
        "ru": "Здравствуйте, спасибо за звонок в нашу клинику. Хотите записаться на приём?",
    },
    "hali_yikama": {
        "tr": "Merhaba, halı yıkama hizmetimize hoş geldiniz. Nasıl yardımcı olabilirim?",
        "en": "Hello, welcome to our carpet cleaning service. How can I help you?",
        "ar": "مرحبا، أهلا بكم في خدمة تنظيف السجاد. كيف يمكنني مساعدتك؟",
        "ru": "Здравствуйте, добро пожаловать в нашу службу чистки ковров. Чем могу помочь?",
    },
    "su_bayii": {
        "tr": "Merhaba, su bayiimizi aradınız. Sipariş vermek ister misiniz?",
        "en": "Hello, you've reached our water delivery service. Would you like to place an order?",
        "ar": "مرحبا، اتصلت بخدمة توصيل المياه. هل تريد تقديم طلب؟",
        "ru": "Здравствуйте, вы позвонили в нашу службу доставки воды. Хотите сделать заказ?",
    },
}

# Dil bazlı sistem promptları
SISTEM_PROMPTLARI = {
    "tr": "Sen bir yapay zeka sesli asistanısın. Türkçe konuşuyorsun. Kısa ve net cevaplar ver. Maksimum 2 cümle kullan.",
    "en": "You are an AI voice assistant. Speak in English. Give short and clear answers. Use maximum 2 sentences.",
    "ar": "أنت مساعد صوتي بالذكاء الاصطناعي. تحدث باللغة العربية. أعط إجابات قصيرة وواضحة.",
    "ru": "Вы голосовой ИИ-ассистент. Говорите по-русски. Давайте короткие и чёткие ответы.",
}

# Hata mesajları (dil bazlı)
HATA_MESAJLARI = {
    "tr": "Üzgünüm, sizi anlayamadım. Tekrar eder misiniz?",
    "en": "I'm sorry, I didn't understand. Could you repeat that?",
    "ar": "آسف، لم أفهم. هل يمكنك التكرار؟",
    "ru": "Извините, я не понял. Не могли бы вы повторить?",
}


class CallSession:
    """Tek bir çağrı oturumu"""

    def __init__(
        self,
        channel_id: str,
        caller_number: str,
        firma_id: str = "1",
        template_id: str = "otel",
        lang: str = "tr"
    ):
        self.channel_id = channel_id
        self.caller_number = caller_number
        self.firma_id = firma_id
        self.template_id = template_id
        self.lang = lang

        self.call_id: Optional[str] = None
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.conversation_history = []
        self.context = {}
        self.state = "initialized"
        self.is_listening = False  # Dinleme durumu (çift tetikleme önleme)

        logger.info(f"CallSession: {channel_id} | {caller_number} | firma:{firma_id} | şablon:{template_id} | dil:{lang}")

    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_duration(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def get_karsilama(self) -> str:
        sablonlar = KARSILAMA_METINLERI.get(self.template_id, KARSILAMA_METINLERI["otel"])
        return sablonlar.get(self.lang, sablonlar.get("tr", "Merhaba!"))

    def get_sistem_promptu(self) -> str:
        return SISTEM_PROMPTLARI.get(self.lang, SISTEM_PROMPTLARI["tr"])

    def get_hata_mesaji(self) -> str:
        return HATA_MESAJLARI.get(self.lang, HATA_MESAJLARI["tr"])

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "caller_number": self.caller_number,
            "firma_id": self.firma_id,
            "template_id": self.template_id,
            "lang": self.lang,
            "call_id": self.call_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "state": self.state,
            "message_count": len(self.conversation_history)
        }


class CallManager:
    """Çağrı yöneticisi - ARI üzerinden ses dinleme ve AI pipeline"""

    def __init__(
        self,
        ari_client: ARIClient,
        audio_handler: AudioHandler,
        whisper_url: str = "http://voiceai-whisper:9000",
        ollama_url: str = "http://voiceai-ollama:11434",
        xtts_url: str = None
    ):
        self.ari = ari_client
        self.audio = audio_handler
        self.whisper_url = os.getenv("WHISPER_URL", whisper_url)
        self.ollama_url = os.getenv("OLLAMA_URL", ollama_url)
        self.xtts_url = os.getenv("XTTS_URL", xtts_url or "http://xtts:5002")

        self.sessions: Dict[str, CallSession] = {}
        self.vad = VADProcessor()

        # Aktif kayıtlar: recording_name -> channel_id
        self._active_recordings: Dict[str, str] = {}

        # ARI event handler'ları
        self.ari.on("StasisStart", self._on_stasis_start)
        self.ari.on("StasisEnd", self._on_stasis_end)
        self.ari.on("PlaybackFinished", self._on_playback_finished)
        self.ari.on("RecordingFinished", self._on_recording_finished)

        logger.info(f"CallManager başlatıldı | XTTS: {self.xtts_url}")

    # ── ARI EVENT HANDLERS ──────────────────────────────────

    async def _on_stasis_start(self, event: dict):
        """Yeni çağrı geldiğinde"""
        try:
            channel = event.get("channel", {})
            channel_id = channel.get("id")
            caller_number = channel.get("caller", {}).get("number", "Unknown")

            # ExternalMedia kanallarını atla
            if channel.get("name", "").startswith("UnicastRTP") or \
               channel.get("name", "").startswith("Snoop"):
                return

            logger.info(f"📞 Gelen çağrı: {caller_number} → {channel_id}")

            # Kanal değişkenlerini al
            firma_id = await self.ari.get_channel_variable(channel_id, "FIRMA_ID") or "1"
            template_id = await self.ari.get_channel_variable(channel_id, "TEMPLATE_ID") or "otel"
            lang = await self.ari.get_channel_variable(channel_id, "LANG") or "tr"

            lang = lang.lower().strip() if lang else "tr"
            if lang not in ["tr", "en", "ar", "ru"]:
                lang = "tr"

            logger.info(f"Firma: {firma_id} | Şablon: {template_id} | Dil: {lang}")

            session = CallSession(channel_id, caller_number, firma_id, template_id, lang)
            self.sessions[channel_id] = session

            await self.ari.answer_channel(channel_id)
            session.state = "active"

            # Karşılama mesajı çal
            await self._play_greeting(session)

        except Exception as e:
            logger.error(f"StasisStart hatası: {e}", exc_info=True)

    async def _on_stasis_end(self, event: dict):
        """Çağrı sonlandığında"""
        try:
            channel = event.get("channel", {})
            channel_id = channel.get("id")

            if channel_id not in self.sessions:
                return

            logger.info(f"📴 Çağrı bitti: {channel_id}")

            session = self.sessions[channel_id]
            session.end_time = datetime.now()
            session.state = "ended"
            await self._save_call_log(session)
            del self.sessions[channel_id]
            logger.info(f"✅ Session temizlendi: {channel_id} ({session.get_duration():.1f}s)")

        except Exception as e:
            logger.error(f"StasisEnd hatası: {e}")

    async def _on_playback_finished(self, event: dict):
        """Ses çalma bittiğinde → dinlemeye başla"""
        try:
            playback = event.get("playback", {})
            target_uri = playback.get("target_uri", "")

            if not target_uri.startswith("channel:"):
                return

            channel_id = target_uri.replace("channel:", "")

            if channel_id not in self.sessions:
                return

            session = self.sessions[channel_id]
            if session.state != "active":
                return

            # Çift tetikleme önleme
            if session.is_listening:
                logger.debug(f"Zaten dinleniyor, atlanıyor: {channel_id}")
                return

            logger.info(f"🎧 Playback bitti, ses dinleme başlıyor: {channel_id}")
            await self._start_recording(session)

        except Exception as e:
            logger.error(f"PlaybackFinished hatası: {e}", exc_info=True)

    async def _on_recording_finished(self, event: dict):
        """Kayıt tamamlandığında → ARI API ile ses dosyasını indir ve işle"""
        try:
            recording = event.get("recording", {})
            recording_name = recording.get("name", "")
            duration = recording.get("duration", 0)

            logger.info(f"📼 Kayıt tamamlandı event: {recording_name} ({duration}s)")

            # Bu kayıt bizim mi?
            if recording_name not in self._active_recordings:
                logger.debug(f"Bilinmeyen kayıt, atlanıyor: {recording_name}")
                return

            channel_id = self._active_recordings.pop(recording_name)

            if channel_id not in self.sessions:
                logger.info("Çağrı sonlanmış, kayıt işlenmiyor")
                return

            session = self.sessions[channel_id]
            session.is_listening = False

            # Çok kısa kayıtları atla (sessizlik / RTP yok)
            if duration < 1:
                logger.info(f"Kayıt çok kısa ({duration}s), 3s bekleyip tekrar dene")
                if session.state == "active":
                    await asyncio.sleep(3)
                    if session.channel_id in self.sessions and session.state == "active":
                        await self._start_recording(session)
                return

            # ARI REST API ile kayıt dosyasını indir
            audio_data = await self._download_recording(recording_name)

            if not audio_data or len(audio_data) < 500:
                logger.warning(f"Kayıt dosyası indirilemedi veya çok kısa, tekrar dinle")
                if session.state == "active":
                    await self._start_recording(session)
                return

            logger.info(f"🎯 Kayıt indirildi: {recording_name} ({len(audio_data)} bytes)")

            # Kaydı sil (temizlik)
            await self._delete_recording(recording_name)

            # STT → LLM → TTS döngüsü
            await self._process_user_audio(session, audio_data)

        except Exception as e:
            logger.error(f"RecordingFinished hatası: {e}", exc_info=True)

    # ── KAYIT (RECORD) ──────────────────────────────────────

    async def _start_recording(self, session: CallSession):
        """ARI Record API ile kullanıcı sesini kaydet.
        maxSilenceSeconds kullanmıyoruz çünkü RTP akışı yokken
        anında sessizlik algılayıp 0s'de kaydı sonlandırıyor.
        Bunun yerine sabit süre (8s) kayıt yapıp dosyayı işliyoruz.
        """
        try:
            session.is_listening = True
            record_name = f"voiceai_rec_{int(time.time()*1000)}"

            url = f"{self.ari.base_url}/channels/{session.channel_id}/record"
            auth = aiohttp.BasicAuth(self.ari.username, self.ari.password)
            params = {
                "name": record_name,
                "format": "wav",
                "maxDurationSeconds": "8",
                "beep": "false",
                "terminateOn": "#",
                "ifExists": "overwrite"
            }

            logger.info(f"🎤 Kayıt başlatılıyor (8s): {record_name}")

            async with self.ari.session.post(url, auth=auth, params=params) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    actual_name = result.get("name", record_name)
                    self._active_recordings[actual_name] = session.channel_id
                    logger.info(f"✅ Kayıt başladı: {actual_name}")
                else:
                    resp_text = await resp.text()
                    logger.error(f"❌ Kayıt başlatılamadı: {resp.status} - {resp_text}")
                    session.is_listening = False
                    # 404 = Channel not found → kanal kapanmış, tekrar deneme
                    if resp.status == 404:
                        logger.info(f"Kanal bulunamadı, session sonlandırılıyor: {session.channel_id}")
                        session.state = "ended"
                        if session.channel_id in self.sessions:
                            del self.sessions[session.channel_id]
                        return
                    # Diğer hatalar için 3 saniye bekleyip bir kez daha dene
                    if session.state == "active" and session.channel_id in self.sessions:
                        await asyncio.sleep(3)
                        if session.channel_id in self.sessions and session.state == "active":
                            await self._start_recording(session)

        except Exception as e:
            logger.error(f"Kayıt başlatma hatası: {e}", exc_info=True)
            session.is_listening = False

    async def _download_recording(self, recording_name: str) -> Optional[bytes]:
        """ARI REST API ile stored recording'i indir"""
        try:
            url = f"{self.ari.base_url}/recordings/stored/{recording_name}/file"
            auth = aiohttp.BasicAuth(self.ari.username, self.ari.password)

            async with self.ari.session.get(url, auth=auth) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    logger.info(f"✅ Kayıt indirildi: {recording_name} ({len(data)} bytes)")
                    return data
                else:
                    resp_text = await resp.text()
                    logger.error(f"❌ Kayıt indirilemedi: {resp.status} - {resp_text}")
        except Exception as e:
            logger.error(f"Kayıt indirme hatası: {e}", exc_info=True)
        return None

    async def _delete_recording(self, recording_name: str):
        """Stored recording'i sil (temizlik)"""
        try:
            url = f"{self.ari.base_url}/recordings/stored/{recording_name}"
            auth = aiohttp.BasicAuth(self.ari.username, self.ari.password)

            async with self.ari.session.delete(url, auth=auth) as resp:
                if resp.status == 204:
                    logger.debug(f"Kayıt silindi: {recording_name}")
                else:
                    logger.debug(f"Kayıt silinemedi: {resp.status}")
        except Exception:
            pass

    # ── KARŞILAMA ────────────────────────────────────────────

    async def _play_greeting(self, session: CallSession):
        """Dile göre karşılama mesajını çal"""
        try:
            greeting_text = session.get_karsilama()
            logger.info(f"🎤 Karşılama ({session.lang}): '{greeting_text[:60]}...'")

            tts_result = await self._text_to_speech(greeting_text, session.lang)

            if tts_result and tts_result.get("audio_path"):
                audio_path = tts_result["audio_path"]
                if audio_path.startswith("/var/lib/asterisk/sounds/"):
                    relative_path = audio_path.replace("/var/lib/asterisk/sounds/", "")
                    if relative_path.endswith(".wav"):
                        relative_path = relative_path[:-4]

                    # Dosyanın oluşmasını bekle
                    for _ in range(20):
                        if os.path.exists(audio_path):
                            break
                        await asyncio.sleep(0.1)

                    if os.path.exists(audio_path):
                        await self.ari.play_audio(
                            session.channel_id,
                            f"sound:/var/lib/asterisk/sounds/{relative_path}"
                        )
                        logger.info(f"🔊 Karşılama çalındı: {relative_path}")
                    else:
                        logger.error(f"Ses dosyası bulunamadı: {audio_path}")
                        # Dosya bulunamadıysa direkt dinlemeye başla
                        await self._start_recording(session)
            else:
                logger.error("TTS karşılama sesi üretemedi")
                # TTS başarısız olsa bile dinlemeye başla
                await self._start_recording(session)

            session.add_message("assistant", greeting_text)

        except Exception as e:
            logger.error(f"Karşılama hatası: {e}", exc_info=True)

    # ── STT → LLM → TTS DÖNGÜSÜ ────────────────────────────

    async def _process_user_audio(self, session: CallSession, audio_data: bytes):
        """Kullanıcı sesini işle: STT → LLM → TTS"""
        try:
            # 1. STT
            logger.info(f"1/3 🎤 STT ({session.lang})...")
            user_text = await self._speech_to_text(audio_data, session.lang)

            if not user_text or len(user_text.strip()) < 2:
                logger.warning("STT boş sonuç, tekrar dinlemeye başla")
                if session.channel_id in self.sessions and session.state == "active":
                    await self._start_recording(session)
                return

            logger.info(f"✅ STT: '{user_text}'")
            session.add_message("user", user_text)

            # Aktarım kontrolü
            try:
                from .transfer_handler import aktarim_gerekli_mi
                aktarim, hedef = aktarim_gerekli_mi(user_text)
                if aktarim:
                    logger.info(f"🔄 Aktarım tetiklendi: {hedef}")
                    from .transfer_handler import get_transfer_handler
                    handler = get_transfer_handler()
                    ozet = await handler.aktarim_metni_uret(session.conversation_history)
                    await handler.aktarim_yap(session.channel_id, hedef, ozet, int(session.firma_id))
                    return
            except Exception as e:
                logger.warning(f"Aktarım kontrolü hatası: {e}")

            # 2. LLM
            logger.info(f"2/3 🧠 LLM ({session.lang})...")
            ai_response = await self._get_llm_response(session, user_text)

            if not ai_response:
                ai_response = session.get_hata_mesaji()

            logger.info(f"✅ LLM: '{ai_response[:80]}'")
            session.add_message("assistant", ai_response)

            # 3. TTS → Çal
            logger.info(f"3/3 🔊 TTS ({session.lang})...")
            tts_result = await self._text_to_speech(ai_response, session.lang)

            if tts_result and tts_result.get("audio_path"):
                audio_path = tts_result["audio_path"]
                if audio_path.startswith("/var/lib/asterisk/sounds/"):
                    relative_path = audio_path.replace("/var/lib/asterisk/sounds/", "")
                    if relative_path.endswith(".wav"):
                        relative_path = relative_path[:-4]

                    # Dosyanın oluşmasını bekle
                    for _ in range(20):
                        if os.path.exists(audio_path):
                            break
                        await asyncio.sleep(0.1)

                    await self.ari.play_audio(
                        session.channel_id,
                        f"sound:/var/lib/asterisk/sounds/{relative_path}"
                    )
                    logger.info(f"✅ TTS çalındı: {relative_path}")
                    # PlaybackFinished event'i tekrar _start_recording'i tetikleyecek
            else:
                logger.error("TTS ses üretemedi, tekrar dinlemeye başla")
                if session.channel_id in self.sessions and session.state == "active":
                    await self._start_recording(session)

            logger.info(f"🎉 Tam döngü tamamlandı: {session.channel_id} (dil: {session.lang})")

        except Exception as e:
            logger.error(f"Ses işleme hatası: {e}", exc_info=True)

    # ── TTS ──────────────────────────────────────────────────

    async def _text_to_speech(self, text: str, lang: str = "tr") -> Optional[dict]:
        """Metni sese çevir"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.xtts_url}/synthesize",
                    json={"text": text, "language": lang}
                )
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ TTS başarılı: {result.get('format')} @ {result.get('sample_rate')}Hz (dil: {lang})")
                    return result
                else:
                    logger.error(f"TTS başarısız: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"TTS hatası: {e}")
        return None

    # ── STT ──────────────────────────────────────────────────

    async def _speech_to_text(self, audio_data: bytes, lang: str = "tr") -> Optional[str]:
        """Ses verisini metne çevir (WAV dosyası olarak gönder)"""
        try:
            # audio_data zaten WAV formatında (ARI'den indirildi)
            # Eğer RIFF header varsa direkt gönder, yoksa WAV header ekle
            if audio_data[:4] == b'RIFF':
                wav_bytes = audio_data
            else:
                # Raw PCM → WAV
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(8000)
                    wav_file.writeframes(audio_data)
                wav_buffer.seek(0)
                wav_bytes = wav_buffer.read()

            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"audio": ("audio.wav", wav_bytes, "audio/wav")}
                data = {}
                if lang and lang != "tr":
                    data["language"] = lang

                response = await client.post(
                    f"{self.whisper_url}/transcribe",
                    files=files,
                    data=data
                )
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "").strip()
                    logger.info(f"Whisper ({lang}): '{text}'")
                    return text
                else:
                    logger.error(f"STT başarısız: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"STT hatası: {e}", exc_info=True)
        return None

    # ── LLM ──────────────────────────────────────────────────

    async def _get_llm_response(self, session: CallSession, user_text: str) -> Optional[str]:
        """LLM'den dil bazlı yanıt al"""
        try:
            system_prompt = session.get_sistem_promptu()

            sablon_promptlari = {
                "tr": {
                    "otel": "Otel resepsiyonistisin. Rezervasyon al, oda bilgisi ver.",
                    "klinik_poliklinik": "Klinik asistanısın. Randevu al, doktor bilgisi ver.",
                    "hali_yikama": "Halı yıkama firması çalışanısın. Sipariş al.",
                    "su_bayii": "Su bayii çalışanısın. Su siparişi al.",
                },
                "en": {
                    "otel": "You are a hotel receptionist. Take reservations, provide room info.",
                    "klinik_poliklinik": "You are a clinic assistant. Schedule appointments.",
                    "hali_yikama": "You work at a carpet cleaning company. Take orders.",
                    "su_bayii": "You work at a water delivery company. Take water orders.",
                },
                "ar": {
                    "otel": "أنت موظف استقبال فندق. خذ الحجوزات وقدم معلومات الغرف.",
                    "klinik_poliklinik": "أنت مساعد عيادة. حدد المواعيد.",
                    "hali_yikama": "تعمل في شركة تنظيف سجاد. خذ الطلبات.",
                    "su_bayii": "تعمل في شركة توصيل مياه. خذ طلبات المياه.",
                },
                "ru": {
                    "otel": "Вы администратор отеля. Принимайте бронирования.",
                    "klinik_poliklinik": "Вы ассистент клиники. Записывайте на приём.",
                    "hali_yikama": "Вы работаете в компании по чистке ковров.",
                    "su_bayii": "Вы работаете в компании по доставке воды.",
                },
            }

            lang_promptlari = sablon_promptlari.get(session.lang, sablon_promptlari["tr"])
            sablon_prompt = lang_promptlari.get(session.template_id, "")
            full_system = f"{system_prompt}\n{sablon_prompt}"

            messages = [{"role": "system", "content": full_system}]
            for msg in session.conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_text})

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={"model": "llama3.1:8b", "messages": messages, "stream": False}
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    logger.error(f"LLM başarısız: {response.status_code}")
        except Exception as e:
            logger.error(f"LLM hatası: {e}")
        return None

    # ── YARDIMCI ─────────────────────────────────────────────

    async def on_audio_complete(self, call_id: str, audio_data: bytes):
        """AudioSocket callback (eski yöntem, artık kullanılmıyor ama uyumluluk için)"""
        logger.info(f"🎯 AudioSocket ses: {call_id} ({len(audio_data)} bytes)")

    async def _save_call_log(self, session: CallSession):
        """Çağrı logunu kaydet"""
        try:
            logger.info(
                f"Çağrı logu kaydedildi: {session.channel_id} | "
                f"{session.get_duration():.1f}s | dil:{session.lang} | "
                f"mesaj:{len(session.conversation_history)}"
            )
        except Exception as e:
            logger.error(f"Log kayıt hatası: {e}")

    def get_active_sessions(self) -> list:
        return [session.to_dict() for session in self.sessions.values()]

    def get_session(self, channel_id: str) -> Optional[CallSession]:
        return self.sessions.get(channel_id)
