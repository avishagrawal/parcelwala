from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.v1.auth import router as auth_router

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "parcelwala-api"}
