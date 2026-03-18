FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    # Web framework
    fastapi \
    uvicorn \
    python-multipart \
    # HTTP clients
    httpx \
    aiohttp \
    # Database / cache
    redis \
    asyncpg \
    # WebSocket support
    websockets \
    # LiveKit Agents — gerçek zamanlı sesli AI framework
    "livekit-agents[openai,silero]~=1.0" \
    livekit

COPY . .

EXPOSE 8001

# Varsayılan: FastAPI REST API sunucusu
# LiveKit agent başlatmak için: python livekit_agent.py start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
