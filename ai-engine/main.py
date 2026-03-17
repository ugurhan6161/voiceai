from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import httpx
import logging
import os
import asyncio
from contextlib import asynccontextmanager

from ari import ARIClient, AudioHandler
from ari.call_manager import CallManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
ari_client: ARIClient = None
audio_handler: AudioHandler = None
call_manager: CallManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    global ari_client, audio_handler, call_manager
    
    logger.info("🚀 Starting VoiceAI Engine...")
    
    try:
        # ARI Client başlat
        ari_client = ARIClient()
        await ari_client.connect()
        
        # AudioHandler başlat
        audio_handler = AudioHandler()
        
        # CallManager başlat
        call_manager = CallManager(ari_client, audio_handler)
        
        # AudioHandler callback'ini CallManager'a bağla
        audio_handler.set_audio_callback(call_manager.on_audio_complete)
        logger.info("🔗 AudioHandler callback connected to CallManager")
        
        # Background tasks başlat
        asyncio.create_task(ari_client.listen())
        asyncio.create_task(audio_handler.start())
        
        logger.info("✅ VoiceAI Engine started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start VoiceAI Engine: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down VoiceAI Engine...")
    
    if ari_client:
        await ari_client.disconnect()
    
    if audio_handler:
        await audio_handler.stop()
    
    logger.info("✅ VoiceAI Engine stopped")


app = FastAPI(title="VoiceAI Engine", lifespan=lifespan)

# Servis URL'leri
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:8001")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
XTTS_URL = os.getenv("XTTS_URL", "http://xtts:8002")

class ChatRequest(BaseModel):
    message: str
    template_id: str
    context: dict = {}

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "default"
    language: str = "tr"

@app.get("/health")
async def health():
    """Tüm AI servislerinin sağlık durumunu kontrol et"""
    services = {}
    
    # ARI kontrolü
    if ari_client:
        ari_healthy = await ari_client.health_check()
        services["ari"] = {"status": "ok" if ari_healthy else "error"}
    else:
        services["ari"] = {"status": "not_initialized"}
    
    # AudioSocket kontrolü
    if audio_handler:
        active_calls = audio_handler.get_active_calls()
        services["audiosocket"] = {
            "status": "ok",
            "active_calls": len(active_calls)
        }
    else:
        services["audiosocket"] = {"status": "not_initialized"}
    
    # Whisper kontrolü
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{WHISPER_URL}/health")
            services["whisper"] = resp.json() if resp.status_code == 200 else {"status": "error"}
    except Exception as e:
        services["whisper"] = {"status": "error", "error": str(e)}
    
    # Ollama kontrolü
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                services["ollama"] = {
                    "status": "ok",
                    "models": [m["name"] for m in models]
                }
            else:
                services["ollama"] = {"status": "error"}
    except Exception as e:
        services["ollama"] = {"status": "error", "error": str(e)}
    
    # XTTS kontrolü
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{XTTS_URL}/health")
            services["xtts"] = resp.json() if resp.status_code == 200 else {"status": "error"}
    except Exception as e:
        services["xtts"] = {"status": "error", "error": str(e)}
    
    all_ok = all(s.get("status") == "ok" for s in services.values())
    
    return {
        "status": "ok" if all_ok else "degraded",
        "service": "ai-engine",
        "services": services
    }

@app.post("/stt/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Ses dosyasını metne çevir (Speech-to-Text)
    
    Args:
        audio: Ses dosyası (WAV/MP3/OGG)
        
    Returns:
        {
            "text": "Transkript metni",
            "language": "tr",
            "duration": 2.5
        }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"audio": (audio.filename, await audio.read(), audio.content_type)}
            response = await client.post(f"{WHISPER_URL}/transcribe", files=files)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Whisper servisi hatası")
            
            return response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Whisper servisi zaman aşımı")
    except Exception as e:
        logger.error(f"STT hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm/chat")
async def chat_with_llm(request: ChatRequest):
    """
    LLM ile sohbet et (Türkçe)
    
    Args:
        message: Kullanıcı mesajı
        template_id: Şablon ID (otel, klinik, hali_yikama vb.)
        context: Konuşma bağlamı
        
    Returns:
        {
            "response": "AI yanıtı",
            "function_call": {...},
            "context": {...}
        }
    """
    try:
        # Şablon bazlı sistem promptu yükle
        system_prompt = get_system_prompt(request.template_id)
        
        # Ollama API çağrısı
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": "llama3.1:8b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 512
                }
            }
            
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Ollama servisi hatası")
            
            result = response.json()
            ai_response = result.get("message", {}).get("content", "")
            
            return {
                "response": ai_response,
                "model": "llama3.1:8b",
                "context": request.context
            }
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM servisi zaman aşımı")
    except Exception as e:
        logger.error(f"LLM hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Metni sese çevir (Text-to-Speech)
    
    Args:
        text: Sentezlenecek metin
        voice_id: Ses ID
        language: Dil kodu (tr)
        
    Returns:
        Audio stream (WAV)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{XTTS_URL}/synthesize",
                json={
                    "text": request.text,
                    "voice_id": request.voice_id,
                    "language": request.language
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="XTTS servisi hatası")
            
            return response.content
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="TTS servisi zaman aşımı")
    except Exception as e:
        logger.error(f"TTS hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipeline/process")
async def process_call(audio: UploadFile = File(...), template_id: str = "otel"):
    """
    Tam AI pipeline: STT → LLM → TTS
    
    Telefon çağrısı için end-to-end işlem
    """
    try:
        # 1. STT: Ses → Metin
        logger.info("1/3 STT başlatılıyor...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"audio": (audio.filename, await audio.read(), audio.content_type)}
            stt_response = await client.post(f"{WHISPER_URL}/transcribe", files=files)
            
            if stt_response.status_code != 200:
                raise HTTPException(status_code=500, detail="STT hatası")
            
            transcript = stt_response.json()
            user_text = transcript.get("text", "")
            logger.info(f"✅ STT: {user_text}")
        
        # 2. LLM: Metin → Yanıt
        logger.info("2/3 LLM başlatılıyor...")
        system_prompt = get_system_prompt(template_id)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_payload = {
                "model": "llama3.1:8b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "stream": False
            }
            
            llm_response = await client.post(f"{OLLAMA_URL}/api/chat", json=llm_payload)
            
            if llm_response.status_code != 200:
                raise HTTPException(status_code=500, detail="LLM hatası")
            
            ai_text = llm_response.json().get("message", {}).get("content", "")
            logger.info(f"✅ LLM: {ai_text}")
        
        # 3. TTS: Yanıt → Ses
        logger.info("3/3 TTS başlatılıyor...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            tts_response = await client.post(
                f"{XTTS_URL}/synthesize",
                json={"text": ai_text, "language": "tr"}
            )
            
            if tts_response.status_code != 200:
                raise HTTPException(status_code=500, detail="TTS hatası")
            
            logger.info("✅ Pipeline tamamlandı")
        
        return {
            "success": True,
            "transcript": user_text,
            "response": ai_text,
            "audio_generated": True
        }
        
    except Exception as e:
        logger.error(f"Pipeline hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_system_prompt(template_id: str) -> str:
    """Şablon ID'sine göre sistem promptu döndür"""
    
    prompts = {
        "otel": """Sen bir otel resepsiyonistisin. Türkçe konuşuyorsun.
Görevin: Rezervasyon almak, oda bilgisi vermek, müşteri sorularını yanıtlamak.
Kibar, profesyonel ve yardımsever ol. Kısa ve net cevaplar ver.""",
        
        "klinik": """Sen bir klinik asistanısın. Türkçe konuşuyorsun.
Görevin: Randevu almak, doktor bilgisi vermek, hasta sorularını yanıtlamak.
Kibar, empatik ve profesyonel ol. Tıbbi tavsiye verme.""",
        
        "hali_yikama": """Sen bir halı yıkama firması çalışanısın. Türkçe konuşuyorsun.
Görevin: Sipariş almak, fiyat bilgisi vermek, teslimat ayarlamak.
Samimi, güler yüzlü ve yardımsever ol.""",
        
        "su_bayii": """Sen bir su bayii çalışanısın. Türkçe konuşuyorsun.
Görevin: Su siparişi almak, teslimat saati ayarlamak.
Hızlı, net ve güler yüzlü ol."""
    }
    
    return prompts.get(template_id, prompts["otel"])


@app.get("/calls/active")
async def get_active_calls():
    """Aktif çağrıları listele"""
    if not call_manager:
        raise HTTPException(status_code=503, detail="CallManager not initialized")
    
    return {
        "active_calls": call_manager.get_active_sessions(),
        "count": len(call_manager.get_active_sessions())
    }


@app.get("/calls/{channel_id}")
async def get_call_info(channel_id: str):
    """Çağrı bilgisini getir"""
    if not call_manager:
        raise HTTPException(status_code=503, detail="CallManager not initialized")
    
    session = call_manager.get_session(channel_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return session.to_dict()


@app.post("/ari/test")
async def test_ari_connection():
    """ARI bağlantısını test et"""
    if not ari_client:
        raise HTTPException(status_code=503, detail="ARI client not initialized")
    
    healthy = await ari_client.health_check()
    
    return {
        "status": "ok" if healthy else "error",
        "connected": ari_client.running,
        "host": ari_client.host,
        "port": ari_client.port
    }
