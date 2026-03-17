"""
VoiceAI Platform — Multi-Tenant Middleware

Her istekte JWT'den firma_id'yi alır ve PostgreSQL search_path'i ayarlar.
Bu sayede her firma kendi schema'sında çalışır (firma_1, firma_2, vb.)
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import os

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant middleware
    
    İstek akışı:
    1. Authorization header'dan JWT token'ı al
    2. Token'ı decode et, firma_id'yi çıkar
    3. Request state'e firma_id ve rol ekle
    4. PostgreSQL bağlantısında search_path ayarla
    """
    
    async def dispatch(self, request: Request, call_next):
        # Public endpoint'ler (auth gerektirmez)
        public_paths = [
            "/health",
            "/api/health",
            "/",
            "/auth/login",
            "/auth/refresh",
            "/auth/health",
            "/api/auth/login",
            "/api/auth/refresh",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/sablonlar",
        ]
        
        # Public path kontrolü
        path = request.url.path
        if any(path.startswith(public_path) for public_path in public_paths):
            return await call_next(request)
        
        # Authorization header kontrolü
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header eksik veya geçersiz",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Token'ı decode et
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Firma bilgilerini request state'e ekle
            request.state.user_id = payload.get("user_id")
            request.state.firma_id = payload.get("firma_id")
            request.state.rol = payload.get("rol")
            request.state.email = payload.get("sub")
            
            # Schema adını belirle
            if request.state.firma_id:
                request.state.schema_name = f"firma_{request.state.firma_id}"
            else:
                # Super admin için shared schema
                request.state.schema_name = "shared"
            
            logger.debug(
                f"Tenant: {request.state.schema_name} | "
                f"User: {request.state.email} | "
                f"Role: {request.state.rol}"
            )
            
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # İsteği işle
        response = await call_next(request)
        return response


async def set_search_path(conn, firma_id: Optional[int]):
    """
    PostgreSQL search_path'i ayarla
    
    Args:
        conn: asyncpg connection
        firma_id: Firma ID (None ise super_admin)
    
    Örnek:
        SET search_path TO firma_1, shared;
    """
    if firma_id:
        schema_name = f"firma_{firma_id}"
        await conn.execute(f"SET search_path TO {schema_name}, shared")
        logger.debug(f"Search path set: {schema_name}, shared")
    else:
        # Super admin - sadece shared
        await conn.execute("SET search_path TO shared")
        logger.debug("Search path set: shared")


def get_tenant_schema(request: Request) -> str:
    """
    Request'ten tenant schema adını al
    
    Usage:
        schema = get_tenant_schema(request)
        # "firma_1" veya "shared"
    """
    return getattr(request.state, "schema_name", "shared")


def get_current_firma_id(request: Request) -> Optional[int]:
    """
    Request'ten firma_id'yi al
    
    Usage:
        firma_id = get_current_firma_id(request)
    """
    return getattr(request.state, "firma_id", None)


def get_current_user_role(request: Request) -> str:
    """
    Request'ten kullanıcı rolünü al
    
    Usage:
        rol = get_current_user_role(request)
    """
    return getattr(request.state, "rol", "")


# ── Kullanım Örneği ──────────────────────────────────────────
"""
# main.py'de:
from middleware.tenant_middleware import TenantMiddleware
app.add_middleware(TenantMiddleware)

# Router'da:
from middleware.tenant_middleware import get_tenant_schema, set_search_path

@router.get("/rezervasyonlar")
async def get_rezervasyonlar(request: Request, pool: Pool = Depends(get_db_pool)):
    firma_id = get_current_firma_id(request)
    
    async with pool.acquire() as conn:
        await set_search_path(conn, firma_id)
        
        # Artık firma_1.rezervasyonlar tablosuna erişebilirsin
        rows = await conn.fetch("SELECT * FROM rezervasyonlar")
        return rows
"""
