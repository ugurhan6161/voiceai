"""
VoiceAI — Audio Handler

Asterisk'ten gelen ses akışını işler ve AI pipeline'a yönlendirir.
AudioSocket protokolü kullanır (basit TCP socket).
"""

import asyncio
import logging
import struct
import uuid
from typing import Optional, Callable
import io

logger = logging.getLogger(__name__)


class AudioHandler:
    """
    AudioSocket protokolü ile ses akışını yönetir.
    
    AudioSocket Format:
    - 16-bit signed linear PCM
    - 8000 Hz sample rate
    - Mono channel
    - 3-byte header: 0x00 (kind) + 2-byte length (big-endian)
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9092):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.active_calls = {}  # channel_id -> call_data
        self.audio_callback: Optional[Callable] = None  # Callback for audio processing
        self.vad = VADProcessor()
        
        logger.info(f"AudioHandler initialized: {host}:{port}")
    
    def set_audio_callback(self, callback: Callable):
        """
        Ses işleme callback'ini ayarla
        
        Callback signature: async def callback(call_id: str, audio_data: bytes)
        """
        self.audio_callback = callback
        logger.info("Audio callback registered")
    
    async def start(self):
        """AudioSocket sunucusunu başlat"""
        try:
            self.server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port
            )
            
            addr = self.server.sockets[0].getsockname()
            logger.info(f"✅ AudioSocket server started on {addr[0]}:{addr[1]}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"❌ AudioSocket server failed: {e}")
            raise
    
    async def stop(self):
        """AudioSocket sunucusunu durdur"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("AudioSocket server stopped")
    
    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Yeni AudioSocket bağlantısını işle"""
        addr = writer.get_extra_info('peername')
        call_id = str(uuid.uuid4())
        
        logger.info(f"📞 New AudioSocket connection from {addr} (call_id: {call_id})")
        
        # Call data
        call_data = {
            "call_id": call_id,
            "audio_buffer": io.BytesIO(),
            "audio_chunks": [],  # Son N chunk için VAD
            "packet_count": 0,
            "total_bytes": 0,
            "is_speaking": False,
            "silence_count": 0,
            "reader": reader,
            "writer": writer
        }
        
        self.active_calls[call_id] = call_data
        
        try:
            # UUID gönder (AudioSocket handshake)
            uuid_bytes = call_id.encode('utf-8')
            await self._send_packet(writer, 0x01, uuid_bytes)  # 0x01 = UUID kind
            
            # Ses paketlerini dinle
            while True:
                # Header oku (3 byte)
                header = await reader.readexactly(3)
                if not header:
                    break
                
                kind = header[0]
                length = struct.unpack('>H', header[1:3])[0]  # Big-endian 16-bit
                
                # Payload oku
                if length > 0:
                    payload = await reader.readexactly(length)
                    
                    if kind == 0x00:  # Audio data
                        await self._process_audio_packet(call_data, payload)
                    
                    elif kind == 0x10:  # Hangup
                        logger.info(f"📴 Hangup signal received for {call_id}")
                        break
                
        except asyncio.IncompleteReadError:
            logger.info(f"Connection closed by client: {call_id}")
        except Exception as e:
            logger.error(f"Error handling AudioSocket connection: {e}")
        finally:
            # Cleanup
            writer.close()
            await writer.wait_closed()
            
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            
            logger.info(f"✅ AudioSocket connection closed: {call_id}")
    
    async def _process_audio_packet(self, call_data: dict, audio_data: bytes):
        """Ses paketini işle"""
        call_data["packet_count"] += 1
        call_data["total_bytes"] += len(audio_data)
        
        # Buffer'a ekle
        call_data["audio_buffer"].write(audio_data)
        
        # Chunk'ı VAD için sakla (son 20 chunk)
        call_data["audio_chunks"].append(audio_data)
        if len(call_data["audio_chunks"]) > 20:
            call_data["audio_chunks"].pop(0)
        
        # VAD: Konuşma tespiti
        is_speech = self.vad.is_speech(audio_data)
        
        if is_speech:
            # Konuşma başladı
            if not call_data["is_speaking"]:
                call_data["is_speaking"] = True
                call_data["silence_count"] = 0
                logger.debug(f"🎤 Speech started: {call_data['call_id']}")
        else:
            # Sessizlik
            if call_data["is_speaking"]:
                call_data["silence_count"] += 1
                
                # 10 ardışık sessiz paket = konuşma bitti (~200ms @ 20ms/paket)
                if call_data["silence_count"] >= 10:
                    call_data["is_speaking"] = False
                    call_data["silence_count"] = 0
                    
                    logger.info(f"🔇 Speech ended: {call_data['call_id']}")
                    
                    # Buffer'daki sesi al
                    audio_buffer = call_data["audio_buffer"]
                    audio_buffer.seek(0)
                    complete_audio = audio_buffer.read()
                    
                    # Buffer'ı temizle
                    audio_buffer.seek(0)
                    audio_buffer.truncate()
                    
                    # Callback'i çağır (eğer varsa)
                    if self.audio_callback and len(complete_audio) > 1600:  # Min 100ms ses
                        try:
                            await self.audio_callback(call_data["call_id"], complete_audio)
                        except Exception as e:
                            logger.error(f"Audio callback error: {e}")
        
        # Her 100 paket logla
        if call_data["packet_count"] % 100 == 0:
            logger.debug(
                f"Call {call_data['call_id']}: "
                f"{call_data['packet_count']} packets, "
                f"{call_data['total_bytes']} bytes, "
                f"speaking={call_data['is_speaking']}"
            )
    
    async def _send_packet(self, writer: asyncio.StreamWriter, kind: int, payload: bytes):
        """AudioSocket paketi gönder"""
        length = len(payload)
        header = struct.pack('B', kind) + struct.pack('>H', length)
        
        writer.write(header + payload)
        await writer.drain()
    
    async def send_audio_to_channel(self, call_id: str, audio_data: bytes):
        """Kanala ses gönder (TTS çıktısı)"""
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return
        
        call_data = self.active_calls[call_id]
        writer = call_data["writer"]
        
        try:
            # Audio data gönder (kind=0x00)
            await self._send_packet(writer, 0x00, audio_data)
            logger.debug(f"Sent {len(audio_data)} bytes to {call_id}")
            
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
    
    async def hangup_call(self, call_id: str):
        """Çağrıyı kapat"""
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return
        
        call_data = self.active_calls[call_id]
        writer = call_data["writer"]
        
        try:
            # Hangup signal gönder (kind=0x10)
            await self._send_packet(writer, 0x10, b'')
            logger.info(f"Hangup signal sent to {call_id}")
            
        except Exception as e:
            logger.error(f"Error sending hangup: {e}")
    
    def get_audio_buffer(self, call_id: str) -> Optional[bytes]:
        """Çağrının ses buffer'ını al"""
        if call_id not in self.active_calls:
            return None
        
        call_data = self.active_calls[call_id]
        buffer = call_data["audio_buffer"]
        
        # Buffer'ı oku ve sıfırla
        buffer.seek(0)
        audio_data = buffer.read()
        buffer.seek(0)
        buffer.truncate()
        
        return audio_data
    
    def get_active_calls(self) -> list:
        """Aktif çağrıları listele"""
        return [
            {
                "call_id": call_id,
                "packet_count": data["packet_count"],
                "total_bytes": data["total_bytes"]
            }
            for call_id, data in self.active_calls.items()
        ]


class VADProcessor:
    """
    Voice Activity Detection (VAD) işlemcisi
    
    Ses akışında konuşma/sessizlik tespiti yapar.
    """
    
    def __init__(self, silence_threshold: int = 500, silence_duration_ms: int = 1000):
        """
        Args:
            silence_threshold: Sessizlik eşiği (RMS değeri)
            silence_duration_ms: Sessizlik süresi (ms)
        """
        self.silence_threshold = silence_threshold
        self.silence_duration_ms = silence_duration_ms
        self.sample_rate = 8000  # AudioSocket default
        
        logger.info(f"VAD initialized: threshold={silence_threshold}, duration={silence_duration_ms}ms")
    
    def calculate_rms(self, audio_data: bytes) -> float:
        """RMS (Root Mean Square) hesapla"""
        if len(audio_data) < 2:
            return 0.0
        
        # 16-bit signed PCM'i integer'lara çevir
        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
        
        # RMS hesapla
        sum_squares = sum(s * s for s in samples)
        rms = (sum_squares / len(samples)) ** 0.5
        
        return rms
    
    def is_speech(self, audio_data: bytes) -> bool:
        """Ses verisi konuşma mı?"""
        rms = self.calculate_rms(audio_data)
        return rms > self.silence_threshold
    
    def detect_silence_end(self, audio_chunks: list) -> bool:
        """
        Sessizlik bitişini tespit et
        
        Args:
            audio_chunks: Son N adet ses chunk'ı
            
        Returns:
            True = Konuşma bitti (sessizlik başladı)
        """
        if not audio_chunks:
            return False
        
        # Son chunk'ları kontrol et
        recent_chunks = audio_chunks[-10:]  # Son 10 chunk
        
        silence_count = sum(
            1 for chunk in recent_chunks
            if not self.is_speech(chunk)
        )
        
        # %70'i sessizse konuşma bitti
        return silence_count >= len(recent_chunks) * 0.7
