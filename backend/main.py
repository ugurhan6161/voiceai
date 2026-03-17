"""
VoiceAI Platform — FastAPI Ana Uygulama
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, admin, firma_panel
from routers.ayarlar import router as ayarlar_router
from routers.sablon_yonetimi import router as sablon_router
from routers.sip import router as sip_router
from middleware.tenant_middleware import TenantMiddleware

app = FastAPI(
    title="VoiceAI Backend API",
    description="Türkçe Sesli Resepsiyonist SaaS Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Router'lar ────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(firma_panel.router)

# Ayarlar ve şablon router'ları prefix düzeltmesiyle
try:
    app.include_router(ayarlar_router)
except Exception:
    pass

try:
    app.include_router(sablon_router)
except Exception:
    pass

try:
    app.include_router(sip_router)
except Exception:
    pass

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da frontend domain'i belirt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Multi-tenant Middleware (en son ekle) ─────────────────────
app.add_middleware(TenantMiddleware)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "backend",
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    return {
        "message": "VoiceAI Platform API",
        "docs": "/docs",
        "version": "2.0.0"
    }
