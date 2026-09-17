from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.platform import router as platform_router

app = FastAPI(title=settings.app_name, version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(platform_router)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "parcelwala-api"}
