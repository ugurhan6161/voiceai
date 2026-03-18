"""
VoiceAI — LiveKit Token ve Oda Yönetimi
Backend API endpoint'leri: token üretimi, oda oluşturma
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["LiveKit"])

# LiveKit ayarları — ortam değişkenlerinden
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://livekit:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")


# ── Pydantic modeller ──────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    firma_id: Optional[str] = None
    template: Optional[str] = None
    firma_adi: Optional[str] = None
    asistan_adi: Optional[str] = "Asistan"
    language: Optional[str] = "tr"


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str


class RoomRequest(BaseModel):
    firma_id: str
    template: str
    firma_adi: str
    asistan_adi: Optional[str] = "Asistan"
    language: Optional[str] = "tr"


class RoomResponse(BaseModel):
    room_name: str
    token: str
    livekit_url: str
    metadata: dict


# ── Yardımcı fonksiyonlar ──────────────────────────────────────────────────

def _create_livekit_token(
    room_name: str,
    participant_identity: str,
    participant_name: str,
    metadata: str = "",
) -> str:
    """
    LiveKit erişim token'ı oluştur.
    livekit-api paketi gereklidir.
    """
    try:
        from livekit.api import AccessToken, VideoGrants

        token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(participant_identity)
            .with_name(participant_name)
            .with_metadata(metadata)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
        )
        return token.to_jwt()

    except ImportError:
        logger.error("livekit-api paketi eksik: backend/Dockerfile'a 'livekit-api' ekleyin")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LiveKit token servisi yapılandırılmamış (livekit-api paketi gerekli)",
        )
    except Exception as exc:
        logger.error("LiveKit token oluşturma hatası: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token oluşturulamadı: {exc}",
        )


# ── API endpoint'leri ──────────────────────────────────────────────────────

@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest) -> TokenResponse:
    """
    LiveKit erişim token'ı oluştur.

    Kullanıcı bu token ile LiveKit odasına katılır ve
    gerçek zamanlı sesli AI konuşması başlatır.
    """
    metadata = json.dumps(
        {
            "firma_id": request.firma_id or "",
            "template": request.template or "",
            "firma_adi": request.firma_adi or "",
            "asistan_adi": request.asistan_adi or "Asistan",
            "language": request.language or "tr",
        }
    )

    token = _create_livekit_token(
        room_name=request.room_name,
        participant_identity=f"user_{uuid.uuid4().hex[:8]}",
        participant_name=request.participant_name,
        metadata=metadata,
    )

    return TokenResponse(
        token=token,
        room_name=request.room_name,
        livekit_url=LIVEKIT_URL,
    )


@router.post("/room", response_model=RoomResponse)
async def create_room(request: RoomRequest) -> RoomResponse:
    """
    Yeni bir LiveKit odası oluştur ve kullanıcı token'ı döndür.

    Firma ve şablon bilgilerini oda meta verisine yazar.
    LiveKit Agent bu meta veriyi okuyarak doğru sistem promptunu yükler.
    """
    room_name = f"voiceai_{request.firma_id}_{uuid.uuid4().hex[:8]}"

    metadata = {
        "firma_id": request.firma_id,
        "template": request.template,
        "firma_adi": request.firma_adi,
        "asistan_adi": request.asistan_adi or "Asistan",
        "language": request.language or "tr",
    }

    # Oda oluştur (LiveKit Server API)
    try:
        from livekit.api import LiveKitAPI, CreateRoomRequest

        async with LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        ) as lk_api:
            await lk_api.room.create_room(
                CreateRoomRequest(
                    name=room_name,
                    metadata=json.dumps(metadata),
                )
            )
            logger.info("LiveKit odası oluşturuldu: %s", room_name)

    except ImportError:
        logger.warning("livekit-api paketi eksik, oda oluşturma atlandı")
    except Exception as exc:
        logger.warning("Oda oluşturulamadı (agent dispatch ile devam): %s", exc)

    # Kullanıcı token'ı oluştur
    token = _create_livekit_token(
        room_name=room_name,
        participant_identity=f"user_{uuid.uuid4().hex[:8]}",
        participant_name="Kullanıcı",
        metadata=json.dumps(metadata),
    )

    return RoomResponse(
        room_name=room_name,
        token=token,
        livekit_url=LIVEKIT_URL,
        metadata=metadata,
    )


@router.get("/config")
async def get_config() -> dict:
    """LiveKit sunucu yapılandırmasını döndür (public URL)."""
    return {
        "livekit_url": LIVEKIT_URL,
        "status": "ok",
    }
