"""
VoiceAI — Asterisk ARI Client

Asterisk REST Interface üzerinden WebSocket bağlantısı kurar ve
gelen çağrıları yönetir.
"""

import asyncio
import logging
import json
import os
from typing import Optional, Callable
import aiohttp
from aiohttp import ClientSession, WSMsgType

logger = logging.getLogger(__name__)


class ARIClient:
    """Asterisk ARI WebSocket istemcisi"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        app_name: str = "voiceai"
    ):
        self.host = host or os.getenv("ASTERISK_HOST", "asterisk")
        self.port = port or int(os.getenv("ASTERISK_ARI_PORT", "8088"))
        self.username = username or os.getenv("ASTERISK_ARI_USER", "voiceai")
        self.password = password or os.getenv("ASTERISK_ARI_PASSWORD", "Asterisk2026!")
        self.app_name = app_name
        
        self.base_url = f"http://{self.host}:{self.port}/ari"
        self.ws_url = f"ws://{self.host}:{self.port}/ari/events?app={self.app_name}&api_key={self.username}:{self.password}"
        
        self.session: Optional[ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.running = False
        
        # Event handlers
        self.handlers = {
            "StasisStart": [],
            "StasisEnd": [],
            "ChannelDtmfReceived": [],
            "ChannelStateChange": [],
            "ChannelDestroyed": [],
            "PlaybackFinished": [],
            "RecordingFinished": [],
        }
        
        logger.info(f"ARI Client initialized: {self.host}:{self.port}")
    
    async def connect(self):
        """ARI WebSocket bağlantısını başlat"""
        try:
            self.session = aiohttp.ClientSession()
            
            logger.info(f"Connecting to ARI WebSocket: {self.ws_url}")
            self.ws = await self.session.ws_connect(
                self.ws_url,
                auth=aiohttp.BasicAuth(self.username, self.password),
                heartbeat=30
            )
            
            self.running = True
            logger.info("✅ ARI WebSocket connected successfully")
            
        except Exception as e:
            logger.error(f"❌ ARI connection failed: {e}")
            raise
    
    async def disconnect(self):
        """ARI bağlantısını kapat"""
        self.running = False
        
        if self.ws:
            await self.ws.close()
            logger.info("ARI WebSocket closed")
        
        if self.session:
            await self.session.close()
            logger.info("ARI session closed")
    
    def on(self, event_type: str, handler: Callable):
        """Event handler kaydet"""
        if event_type in self.handlers:
            self.handlers[event_type].append(handler)
            logger.debug(f"Handler registered for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    async def listen(self):
        """WebSocket'ten gelen eventleri dinle"""
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")
        
        logger.info("🎧 Listening for ARI events...")
        
        try:
            async for msg in self.ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                    
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break
                    
                elif msg.type == WSMsgType.CLOSED:
                    logger.warning("WebSocket closed by server")
                    break
                    
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
        finally:
            self.running = False
    
    async def _handle_message(self, data: str):
        """Gelen ARI mesajını işle"""
        try:
            event = json.loads(data)
            event_type = event.get("type")
            
            logger.debug(f"📨 ARI Event: {event_type}")
            
            # Event handler'ları çağır
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error in handler for {event_type}: {e}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from ARI: {e}")
        except Exception as e:
            logger.error(f"Error handling ARI message: {e}")
    
    async def answer_channel(self, channel_id: str):
        """Kanalı cevapla"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/answer"
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with self.session.post(url, auth=auth) as resp:
                if resp.status == 204:
                    logger.info(f"✅ Channel answered: {channel_id}")
                else:
                    logger.error(f"Failed to answer channel: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error answering channel: {e}")
    
    async def play_audio(self, channel_id: str, media_uri: str):
        """Kanala ses dosyası çal"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/play"
            auth = aiohttp.BasicAuth(self.username, self.password)
            params = {"media": media_uri}
            
            logger.info(f"🎵 ARI Play Request: {url} | media={media_uri}")
            
            async with self.session.post(url, auth=auth, params=params) as resp:
                response_text = await resp.text()
                logger.info(f"🎵 ARI Play Response: status={resp.status}, body={response_text}")
                
                if resp.status == 201:
                    logger.info(f"✅ Playing audio on channel: {channel_id}")
                    return json.loads(response_text) if response_text else None
                else:
                    logger.error(f"❌ Failed to play audio: {resp.status} - {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error playing audio: {e}", exc_info=True)
            return None
    
    async def hangup_channel(self, channel_id: str):
        """Kanalı kapat"""
        try:
            url = f"{self.base_url}/channels/{channel_id}"
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with self.session.delete(url, auth=auth) as resp:
                if resp.status == 204:
                    logger.info(f"✅ Channel hung up: {channel_id}")
                else:
                    logger.error(f"Failed to hangup channel: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")
    
    async def get_channel_variable(self, channel_id: str, variable: str) -> Optional[str]:
        """Kanal değişkenini oku"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/variable"
            auth = aiohttp.BasicAuth(self.username, self.password)
            params = {"variable": variable}
            
            async with self.session.get(url, auth=auth, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("value")
                else:
                    logger.error(f"Failed to get variable: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error getting channel variable: {e}")
        
        return None
    
    async def set_channel_variable(self, channel_id: str, variable: str, value: str):
        """Kanal değişkenini ayarla"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/variable"
            auth = aiohttp.BasicAuth(self.username, self.password)
            params = {"variable": variable, "value": value}
            
            async with self.session.post(url, auth=auth, params=params) as resp:
                if resp.status == 204:
                    logger.debug(f"Variable set: {variable}={value}")
                else:
                    logger.error(f"Failed to set variable: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error setting channel variable: {e}")
    
    async def start_external_media(self, channel_id: str, external_host: str, format: str = "slin16"):
        """External Media başlat (ses akışı için)"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/externalMedia"
            auth = aiohttp.BasicAuth(self.username, self.password)
            data = {
                "app": self.app_name,
                "external_host": external_host,
                "format": format
            }
            
            async with self.session.post(url, auth=auth, json=data) as resp:
                if resp.status == 200:
                    logger.info(f"✅ External media started: {channel_id}")
                    return await resp.json()
                else:
                    logger.error(f"Failed to start external media: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error starting external media: {e}")
        
        return None
    
    async def health_check(self) -> bool:
        """ARI sağlık kontrolü"""
        try:
            url = f"{self.base_url}/asterisk/info"
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"✅ Asterisk ARI healthy: {data.get('system_name')}")
                        return True
                    else:
                        logger.error(f"ARI health check failed: {resp.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"ARI health check error: {e}")
            return False
