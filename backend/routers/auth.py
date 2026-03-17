"""
VoiceAI Platform — JWT Authentication Router

Kullanıcı girişi, token yönetimi ve yetkilendirme.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import asyncpg
from asyncpg.pool import Pool

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT Ayarları
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY ortam değişkeni tanımlı değil!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 saat
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 gün

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Pydantic Modeller ────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    firma_id: Optional[int] = None
    rol: Optional[str] = None


class User(BaseModel):
    id: int
    email: EmailStr
    ad: Optional[str] = None
    rol: str
    firma_id: Optional[int] = None
    aktif: bool


class UserInDB(User):
    sifre_hash: str


# ── Database Connection ──────────────────────────────────────
async def get_db_pool() -> Pool:
    """PostgreSQL connection pool"""
    return await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "voiceai_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "voiceai"),
        min_size=2,
        max_size=10
    )


# ── JWT Token Fonksiyonları ──────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Access token oluştur"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Refresh token oluştur"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_email(pool: Pool, email: str) -> Optional[UserInDB]:
    """Email ile kullanıcı getir"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, firma_id, email, sifre_hash, ad, rol, aktif
            FROM shared.kullanicilar
            WHERE email = $1 AND is_deleted = FALSE
            """,
            email
        )
        
        if row:
            return UserInDB(**dict(row))
        return None


async def verify_password(pool: Pool, email: str, password: str) -> bool:
    """Şifre doğrulama (PostgreSQL crypt fonksiyonu)"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT sifre_hash = crypt($2, sifre_hash) AS match
            FROM shared.kullanicilar
            WHERE email = $1 AND is_deleted = FALSE
            """,
            email, password
        )
        return result or False


async def authenticate_user(pool: Pool, email: str, password: str) -> Optional[UserInDB]:
    """Kullanıcı doğrulama"""
    user = await get_user_by_email(pool, email)
    if not user:
        return None
    if not await verify_password(pool, email, password):
        return None
    if not user.aktif:
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    pool: Pool = Depends(get_db_pool)
) -> User:
    """Token'dan mevcut kullanıcıyı getir"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "access":
            raise credentials_exception
        
        token_data = TokenData(
            email=email,
            user_id=payload.get("user_id"),
            firma_id=payload.get("firma_id"),
            rol=payload.get("rol")
        )
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(pool, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return User(**user.dict())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Aktif kullanıcı kontrolü"""
    if not current_user.aktif:
        raise HTTPException(status_code=400, detail="Kullanıcı aktif değil")
    return current_user


def require_role(allowed_roles: list[str]):
    """Rol kontrolü decorator"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok"
            )
        return current_user
    return role_checker


# ── API Endpoints ────────────────────────────────────────────
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    pool: Pool = Depends(get_db_pool)
):
    """
    Kullanıcı girişi
    
    - **username**: Email adresi
    - **password**: Şifre
    
    Returns:
        - access_token: 1 saat geçerli
        - refresh_token: 30 gün geçerli
    """
    user = await authenticate_user(pool, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Son giriş zamanını güncelle
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE shared.kullanicilar SET son_giris = NOW() WHERE id = $1",
            user.id
        )
    
    # Token payload
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "firma_id": user.firma_id,
        "rol": user.rol
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    pool: Pool = Depends(get_db_pool)
):
    """
    Refresh token ile yeni access token al
    
    - **refresh_token**: Geçerli refresh token
    
    Returns:
        - Yeni access_token ve refresh_token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Kullanıcıyı kontrol et
    user = await get_user_by_email(pool, email)
    if user is None or not user.aktif:
        raise credentials_exception
    
    # Yeni tokenlar oluştur
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "firma_id": user.firma_id,
        "rol": user.rol
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Mevcut kullanıcı bilgilerini getir
    
    Returns:
        - Kullanıcı bilgileri (şifre hariç)
    """
    return current_user


@router.get("/health")
async def auth_health():
    """Auth servisi sağlık kontrolü"""
    return {"status": "ok", "service": "auth"}
