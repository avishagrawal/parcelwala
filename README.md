# ParcelWalaa

Milestone 1 monorepo: FastAPI authentication service, PostgreSQL, SQLAlchemy, Alembic, Docker Compose, and a minimal frontend shell.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

The API is available at http://localhost:8000 and Swagger UI at http://localhost:8000/docs.

To seed the development administrator:

```bash
docker compose exec backend python -m app.seed
```

Run tests locally with `cd backend && pip install -r requirements.txt && pytest`.

Development demo credentials are controlled by `.env` (`SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`) and are never committed.
