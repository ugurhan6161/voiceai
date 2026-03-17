"""
Ollama LLM Client — Türkçe Konuşma ve Function Calling
"""
import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime


class OllamaClient:
    """
    Ollama API ile iletişim kuran async client.
    llama3.1:8b modeli ile Türkçe konuşma ve function calling desteği.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _ensure_session(self):
        """HTTP session oluştur (lazy initialization)"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def close(self):
        """HTTP session'ı kapat"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_system_prompt(self, template: str = "otel") -> str:
        """
        Şablona göre sistem promptu döndür.
        
        Args:
            template: Şablon kodu (otel, klinik, hali_yikama vb.)
        
        Returns:
            Sistem promptu metni
        """
        prompts = {
            "otel": """Sen profesyonel bir otel resepsiyonistisin. Adın Ayşe.
Görevin: Müşterilere yardımcı olmak, rezervasyon almak, oda bilgisi vermek.

Kişilik:
- Sıcak, samimi ve profesyonel
- Türkçe konuşuyorsun, doğal ve akıcı
- Kısa ve net cümleler kullan
- Müşteriyi dinle, ihtiyacını anla

Yeteneklerin:
1. rezervasyon_olustur: Yeni rezervasyon al
2. rezervasyon_sorgula: Mevcut rezervasyonu kontrol et
3. oda_musaitlik: Uygun odaları göster
4. rezervasyon_iptal: Rezervasyonu iptal et
5. bilgi_ver: Genel otel bilgisi ver

Önemli:
- Eksik bilgi varsa kibarca sor (tarih, kişi sayısı, isim, telefon)
- Fonksiyon çağırmadan önce tüm gerekli bilgileri topla
- Müşteriye her zaman yanıt ver, sessiz kalma
- Rezervasyon onayında özet geç

Örnek Konuşma:
Müşteri: "Merhaba, yarın için oda var mı?"
Sen: "Merhaba! Tabii ki, size yardımcı olabilirim. Kaç kişilik oda arıyorsunuz?"
""",
            
            "klinik": """Sen profesyonel bir klinik asistanısın. Adın Zeynep.
Görevin: Randevu almak, randevu sorgulamak, bilgi vermek.

Kişilik:
- Nazik, anlayışlı ve profesyonel
- Sağlık konusunda hassas ve dikkatli
- Türkçe konuşuyorsun, net ve anlaşılır

Yeteneklerin:
1. randevu_olustur: Yeni randevu al
2. randevu_sorgula: Mevcut randevuyu kontrol et
3. doktor_musaitlik: Uygun saatleri göster
4. randevu_iptal: Randevuyu iptal et
5. bilgi_ver: Klinik bilgisi ver
""",
            
            "hali_yikama": """Sen halı yıkama firmasının müşteri temsilcisisin. Adın Mehmet.
Görevin: Sipariş almak, fiyat vermek, randevu ayarlamak.

Kişilik:
- Güler yüzlü, pratik ve çözüm odaklı
- Türkçe konuşuyorsun, samimi ve anlaşılır

Yeteneklerin:
1. siparis_olustur: Yeni sipariş al
2. fiyat_hesapla: Fiyat teklifi ver
3. randevu_ayarla: Toplama randevusu ayarla
4. siparis_sorgula: Sipariş durumunu kontrol et
5. bilgi_ver: Hizmet bilgisi ver
"""
        }
        
        return prompts.get(template, prompts["otel"])
    
    async def chat(
        self,
        message: str,
        template: str = "otel",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Ollama ile sohbet et.
        
        Args:
            message: Kullanıcı mesajı
            template: Şablon kodu (sistem promptu için)
            conversation_history: Önceki konuşma geçmişi
            functions: Kullanılabilir fonksiyonlar (function calling için)
            stream: Token streaming aktif mi?
        
        Returns:
            LLM yanıtı (metin + function_call varsa)
        """
        await self._ensure_session()
        
        # Mesaj geçmişini hazırla
        messages = []
        
        # Sistem promptu ekle
        messages.append({
            "role": "system",
            "content": self._get_system_prompt(template)
        })
        
        # Konuşma geçmişini ekle
        if conversation_history:
            messages.extend(conversation_history)
        
        # Mevcut mesajı ekle
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Function calling için tools ekle
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 512
            }
        }
        
        # Fonksiyonları ekle (eğer varsa)
        if functions:
            payload["tools"] = functions
        
        try:
            if stream:
                return await self._chat_stream(payload)
            else:
                return await self._chat_non_stream(payload)
        
        except Exception as e:
            print(f"❌ Ollama chat hatası: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen tekrar deneyin."
            }
    
    async def _chat_non_stream(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming chat (tek seferde yanıt)"""
        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API hatası: {response.status} - {error_text}")
            
            result = await response.json()
            
            # Yanıtı parse et
            assistant_message = result.get("message", {})
            content = assistant_message.get("content", "")
            tool_calls = assistant_message.get("tool_calls", [])
            
            response_data = {
                "success": True,
                "message": content,
                "timestamp": datetime.now().isoformat()
            }
            
            # Function call varsa ekle
            if tool_calls:
                response_data["function_call"] = {
                    "name": tool_calls[0].get("function", {}).get("name"),
                    "arguments": tool_calls[0].get("function", {}).get("arguments", {})
                }
            
            return response_data
    
    async def _chat_stream(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Streaming chat (token token yanıt)
        
        Yields:
            Her token ayrı ayrı
        """
        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API hatası: {response.status} - {error_text}")
            
            async for line in response.content:
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if chunk.get("message"):
                            content = chunk["message"].get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
    
    async def generate_completion(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Basit completion (chat yerine generate endpoint)
        
        Args:
            prompt: Prompt metni
            system: Sistem promptu (opsiyonel)
            stream: Streaming aktif mi?
        
        Returns:
            Completion yanıtı
        """
        await self._ensure_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 256
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API hatası: {response.status} - {error_text}")
                
                if stream:
                    # Streaming yanıt
                    full_response = ""
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                text = chunk.get("response", "")
                                full_response += text
                            except json.JSONDecodeError:
                                continue
                    
                    return {
                        "success": True,
                        "response": full_response
                    }
                else:
                    # Non-streaming yanıt
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result.get("response", "")
                    }
        
        except Exception as e:
            print(f"❌ Ollama generate hatası: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Ollama servisinin sağlık kontrolü
        
        Returns:
            True: Servis çalışıyor
            False: Servis çalışmıyor
        """
        await self._ensure_session()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            print(f"❌ Ollama health check hatası: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        Yüklü modelleri listele
        
        Returns:
            Model isimleri listesi
        """
        await self._ensure_session()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    return [model.get("name") for model in models]
                return []
        except Exception as e:
            print(f"❌ Ollama list models hatası: {e}")
            return []


# Singleton instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Global Ollama client instance döndür"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


async def cleanup_ollama_client():
    """Global client'ı temizle"""
    global _ollama_client
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None
