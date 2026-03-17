from fastapi import FastAPI, File, UploadFile, HTTPException
from faster_whisper import WhisperModel
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper STT")

# Faster-Whisper Turbo INT8 modeli - CPU optimizasyonu
# Model: turbo (809M parametreli, en hızlı)
# Compute type: int8 (CPU için optimize)
# Device: cpu
# Threads: 4 (VPS'de 8 çekirdek var, 4'ünü kullan)
model = None

@app.on_event("startup")
async def startup_event():
    global model
    logger.info("Faster-Whisper Turbo INT8 modeli yükleniyor...")
    try:
        model = WhisperModel(
            "turbo",
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=2
        )
        logger.info("✅ Whisper modeli başarıyla yüklendi")
    except Exception as e:
        logger.error(f"❌ Model yükleme hatası: {e}")
        raise

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "whisper",
        "model": "faster-whisper-turbo",
        "compute_type": "int8",
        "device": "cpu",
        "ready": model is not None
    }

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Ses dosyasını Türkçe metne çevirir.
    
    Args:
        audio: WAV/MP3/OGG formatında ses dosyası
        
    Returns:
        {
            "text": "Transkript metni",
            "language": "tr",
            "segments": [...],
            "duration": 2.5
        }
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model henüz yüklenmedi")
    
    try:
        # Geçici dosyaya kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Transkript başlatılıyor: {audio.filename}")
        
        # Faster-Whisper ile transkript
        # language="tr" -> Türkçe zorla
        # beam_size=5 -> Kalite/hız dengesi
        # vad_filter=True -> Sessiz kısımları atla
        segments, info = model.transcribe(
            tmp_file_path,
            language="tr",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        # Segmentleri topla
        full_text = ""
        segment_list = []
        
        for segment in segments:
            full_text += segment.text + " "
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
        
        result = {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segment_list
        }
        
        logger.info(f"✅ Transkript tamamlandı: {len(full_text)} karakter")
        
        # Geçici dosyayı sil
        os.unlink(tmp_file_path)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Transkript hatası: {e}")
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe-stream")
async def transcribe_stream(audio: UploadFile = File(...)):
    """
    Gerçek zamanlı ses akışı için transkript.
    Barge-in için kullanılır.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model henüz yüklenmedi")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Hızlı transkript - beam_size=1 (greedy)
        segments, info = model.transcribe(
            tmp_file_path,
            language="tr",
            beam_size=1,  # En hızlı mod
            vad_filter=True
        )
        
        # Sadece ilk segmenti al (gerçek zamanlı için)
        first_segment = next(segments, None)
        text = first_segment.text.strip() if first_segment else ""
        
        os.unlink(tmp_file_path)
        
        return {
            "text": text,
            "is_speech": len(text) > 0
        }
        
    except Exception as e:
        logger.error(f"❌ Stream transkript hatası: {e}")
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))
