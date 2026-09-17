# ParcelWalaa

ParcelWalaa is a shared FastAPI/PostgreSQL delivery platform with role-aware applications for customers, delivery partners, restaurants, franchises, and administrators.

## Applications

The backend exposes shared `/api/v1` APIs for authentication, addresses, parcel booking/tracking, restaurants and menus, food orders, deliveries, notifications, support, and admin dashboard statistics. The existing `frontend/` Next.js shell remains the web entry point; client applications can consume these same APIs for web or mobile delivery.

## Setup

```bash
cp .env.example .env
# replace local placeholder values in .env
docker compose up --build
# in another terminal
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
docker compose exec backend pytest -q
```

Swagger: http://localhost:8000/docs. Production uses PostgreSQL; tests use isolated SQLite fixtures. Never commit `.env` or credentials.
