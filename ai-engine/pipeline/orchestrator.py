"""
Pipeline Orchestrator — STT→LLM→TTS Tam Akış
Ses → Metin → LLM → Fonksiyon → TTS → Ses
"""
import os
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

# LLM ve diğer modülleri import et
import sys
sys.path.insert(0, '/app')
from llm.ollama_client import get_ollama_client
from llm.function_calling import FunctionCallingEngine
from llm.slot_filling import SlotFillingEngine


class PipelineOrchestrator:
    """
    Tam AI pipeline'ı yöneten orchestrator.
    STT → LLM → Function Calling → Slot Filling → TTS
    """
    
    def __init__(
        self,
        firma_id: str = "firma_1",
        template: str = "otel"
    ):
        self.firma_id = firma_id
        self.template = template
        
        # Servis URL'leri
        self.whisper_url = os.getenv("WHISPER_URL", "http://whisper:8001")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.xtts_url = os.getenv("XTTS_URL", "http://xtts:8002")
        
        # LLM client
        self.llm_client = get_ollama_client()
        
        # Function calling ve slot filling
        self.function_engine = FunctionCallingEngine()
        self.slot_engine = SlotFillingEngine()
        
        # Konuşma geçmişi (session bazlı)
        self.conversation_history: List[Dict[str, str]] = []
        
        # HTTP client
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def _ensure_http_client(self):
        """HTTP client oluştur"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Kaynakları temizle"""
        if self.http_client:
            await self.http_client.aclose()
        await self.llm_client.close()
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Ses verisini metne çevir (STT - Whisper)
        
        Args:
            audio_data: Ses verisi (bytes)
        
        Returns:
            Transkript sonucu
        """
        await self._ensure_http_client()
        
        try:
            # Whisper servisine ses gönder
            files = {"file": ("audio.wav", audio_data, "audio/wav")}
            response = await self.http_client.post(
                f"{self.whisper_url}/transcribe",
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "language": result.get("language", "tr"),
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Whisper hatası: {response.status_code}"
                }
        
        except Exception as e:
            print(f"❌ STT hatası: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_text_with_llm(
        self,
        user_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Metni LLM ile işle ve yanıt üret
        
        Args:
            user_text: Kullanıcı metni
            context: Ek bağlam bilgisi (müşteri bilgisi, slot durumu vb.)
        
        Returns:
            LLM yanıtı + function call varsa
        """
        try:
            # Kullanıcı mesajını geçmişe ekle
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })
            
            # Fonksiyon tanımlarını al (şimdilik boş liste)
            available_functions = []
            
            # LLM'e gönder
            response = await self.llm_client.chat(
                message=user_text,
                template=self.template,
                conversation_history=self.conversation_history[:-1],  # Son mesaj hariç
                functions=available_functions,
                stream=False
            )
            
            if not response.get("success"):
                return response
            
            # Asistan yanıtını geçmişe ekle
            assistant_message = response.get("message", "")
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Function call varsa işle
            if "function_call" in response:
                function_result = await self._execute_function_call(
                    response["function_call"]
                )
                response["function_result"] = function_result
            
            return response
        
        except Exception as e:
            print(f"❌ LLM işleme hatası: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Üzgünüm, bir sorun oluştu. Lütfen tekrar deneyin."
            }
    
    async def _execute_function_call(
        self,
        function_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Function call'u çalıştır
        
        Args:
            function_call: Fonksiyon adı ve parametreleri
        
        Returns:
            Fonksiyon sonucu
        """
        function_name = function_call.get("name")
        arguments = function_call.get("arguments", {})
        
        print(f"🔧 Fonksiyon çağrılıyor: {function_name}")
        print(f"📋 Parametreler: {json.dumps(arguments, ensure_ascii=False)}")
        
        try:
            # Slot filling kontrolü
            slot_check = self.slot_engine.check_slots(function_name, arguments)
            
            if not slot_check["complete"]:
                # Eksik slotlar var
                missing = slot_check["missing_slots"]
                print(f"⚠️ Eksik bilgiler: {missing}")
                return {
                    "success": False,
                    "error": "missing_slots",
                    "missing_slots": missing,
                    "message": f"Lütfen şu bilgileri de verin: {', '.join(missing)}"
                }
            
            # Fonksiyonu çalıştır
            result = await self.function_engine.parse_and_execute(
                json.dumps({"function_call": {"name": function_name, "arguments": arguments}}),
                firma_id=int(self.firma_id.split('_')[1]) if '_' in self.firma_id else 1,
                call_context={}
            )
            
            print(f"✅ Fonksiyon sonucu: {result.get('success')}")
            return result
        
        except Exception as e:
            print(f"❌ Fonksiyon çalıştırma hatası: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "tr_female_1"
    ) -> Dict[str, Any]:
        """
        Metni sese çevir (TTS - XTTS)
        
        Args:
            text: Konuşulacak metin
            voice: Ses profili
        
        Returns:
            Ses verisi
        """
        await self._ensure_http_client()
        
        try:
            # XTTS servisine metin gönder
            payload = {
                "text": text,
                "voice": voice,
                "language": "tr"
            }
            
            response = await self.http_client.post(
                f"{self.xtts_url}/synthesize",
                json=payload
            )
            
            if response.status_code == 200:
                audio_data = response.content
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "format": "wav"
                }
            else:
                return {
                    "success": False,
                    "error": f"TTS hatası: {response.status_code}"
                }
        
        except Exception as e:
            print(f"❌ TTS hatası: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_audio_to_audio(
        self,
        audio_data: bytes,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        TAM PIPELINE: Ses → Metin → LLM → Fonksiyon → TTS → Ses
        
        Args:
            audio_data: Gelen ses verisi
            context: Bağlam bilgisi
        
        Returns:
            Yanıt sesi + metadata
        """
        pipeline_start = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"🎙️ YENİ ÇAĞRI İŞLENİYOR - {pipeline_start.isoformat()}")
        print(f"{'='*60}\n")
        
        # 1. STT: Ses → Metin
        print("📝 ADIM 1: Ses metne çevriliyor (STT)...")
        stt_result = await self.transcribe_audio(audio_data)
        
        if not stt_result.get("success"):
            return {
                "success": False,
                "error": "STT başarısız",
                "details": stt_result
            }
        
        user_text = stt_result.get("text", "")
        print(f"✅ Kullanıcı: {user_text}\n")
        
        # 2. LLM: Metin → Yanıt + Fonksiyon
        print("🤖 ADIM 2: LLM işliyor...")
        llm_result = await self.process_text_with_llm(user_text, context)
        
        if not llm_result.get("success"):
            return {
                "success": False,
                "error": "LLM başarısız",
                "details": llm_result
            }
        
        assistant_text = llm_result.get("message", "")
        print(f"✅ Asistan: {assistant_text}\n")
        
        # 3. Function Call (varsa)
        function_result = None
        if "function_call" in llm_result:
            print("🔧 ADIM 3: Fonksiyon çalıştırılıyor...")
            function_result = llm_result.get("function_result")
            
            if function_result and function_result.get("success"):
                print(f"✅ Fonksiyon başarılı: {function_result.get('message', '')}\n")
            else:
                print(f"⚠️ Fonksiyon hatası: {function_result.get('error', '')}\n")
        
        # 4. TTS: Metin → Ses
        print("🔊 ADIM 4: Yanıt sese çevriliyor (TTS)...")
        tts_result = await self.synthesize_speech(assistant_text)
        
        if not tts_result.get("success"):
            # TTS başarısız olsa bile metni döndür
            print("⚠️ TTS başarısız, sadece metin dönülüyor\n")
            return {
                "success": True,
                "text": assistant_text,
                "audio_data": None,
                "function_result": function_result,
                "stt_result": stt_result,
                "llm_result": llm_result
            }
        
        print("✅ Ses hazır\n")
        
        # Pipeline tamamlandı
        pipeline_end = datetime.now()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        print(f"{'='*60}")
        print(f"✅ PIPELINE TAMAMLANDI - Süre: {duration:.2f}s")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "text": assistant_text,
            "audio_data": tts_result.get("audio_data"),
            "function_result": function_result,
            "stt_result": stt_result,
            "llm_result": llm_result,
            "tts_result": tts_result,
            "duration_seconds": duration
        }
    
    async def process_text_to_text(
        self,
        user_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sadece metin bazlı işlem (test için)
        
        Args:
            user_text: Kullanıcı metni
            context: Bağlam
        
        Returns:
            Yanıt metni + metadata
        """
        print(f"\n💬 Kullanıcı: {user_text}")
        
        llm_result = await self.process_text_with_llm(user_text, context)
        
        if not llm_result.get("success"):
            return llm_result
        
        assistant_text = llm_result.get("message", "")
        print(f"🤖 Asistan: {assistant_text}\n")
        
        return {
            "success": True,
            "text": assistant_text,
            "function_result": llm_result.get("function_result"),
            "llm_result": llm_result
        }
    
    def reset_conversation(self):
        """Konuşma geçmişini sıfırla"""
        self.conversation_history = []
        print("🔄 Konuşma geçmişi sıfırlandı")


# Singleton instance
_orchestrator: Optional[PipelineOrchestrator] = None


def get_orchestrator(
    firma_id: str = "firma_1",
    template: str = "otel"
) -> PipelineOrchestrator:
    """Global orchestrator instance döndür"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator(
            firma_id=firma_id,
            template=template
        )
    return _orchestrator


async def cleanup_orchestrator():
    """Global orchestrator'ı temizle"""
    global _orchestrator
    if _orchestrator:
        await _orchestrator.close()
        _orchestrator = None
