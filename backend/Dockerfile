FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    asyncpg \
    redis \
    celery \
    kombu \
    pydantic \
    "pydantic[email]" \
    python-jose[cryptography] \
    "passlib[bcrypt]" \
    httpx \
    cryptography \
    python-multipart \
    # LiveKit API — token üretimi ve oda yönetimi için
    livekit-api

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
