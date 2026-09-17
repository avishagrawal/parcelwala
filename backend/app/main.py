from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.auth import router as auth_router
from app.dependencies import get_current_user, require_roles
from app.models import User

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "parcelwala-api"}


@app.get("/rbac-test", tags=["rbac"])
def rbac_test(user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN"))):
    return {
        "message": "RBAC check passed",
        "email": user.email,
        "roles": [role.name for role in user.roles],
    }
