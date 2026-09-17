from datetime import datetime, timedelta, timezone

import jwt as jose_jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.seed import ROLE_NAMES

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def override_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        for role_name in ROLE_NAMES:
            db.add(Role(name=role_name))
        db.commit()

    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def create_user(email: str = "user@example.com", password: str = "Password123!", full_name: str = "Test User"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login_user(email: str = "user@example.com", password: str = "Password123!"):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_seed_roles_are_complete_in_db():
    with TestingSessionLocal() as db:
        stored = {role.name for role in db.query(Role).all()}
    assert stored == set(ROLE_NAMES)
    assert len(ROLE_NAMES) == 8


def test_register_login_and_me():
    payload = create_user()
    assert payload["email"] == "user@example.com"
    assert payload["roles"] == ["CUSTOMER"]

    tokens = login_user()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
    assert me.json()["roles"] == ["CUSTOMER"]


def test_duplicate_registration_and_bad_login():
    payload = {"email": "dup@example.com", "password": "Password123!", "full_name": "Dup User"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "wrong-password"}).status_code == 401


def test_missing_and_invalid_access_tokens_are_rejected():
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}).status_code == 401


def test_refresh_token_rotation_and_revoked_reuse():
    create_user(email="refresh@example.com")
    tokens = login_user(email="refresh@example.com")
    old_refresh = tokens["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200, rotated.text
    rotated_body = rotated.json()
    assert rotated_body["refresh_token"] != old_refresh
    assert rotated_body["access_token"] != tokens["access_token"]

    second_try = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert second_try.status_code == 401

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {rotated_body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "refresh@example.com"


def test_invalid_and_expired_refresh_tokens_are_rejected():
    create_user(email="expired@example.com")
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-token"}).status_code == 401

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "expired@example.com").one()

    expired_payload = {
        "sub": user.id,
        "type": "refresh",
        "jti": "expired-token-123",
        "iat": datetime.now(timezone.utc) - timedelta(hours=3),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jose_jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_token})
    assert response.status_code == 401


def test_inactive_user_cannot_login_or_refresh():
    create_user(email="inactive@example.com")
    login = login_user(email="inactive@example.com")

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "inactive@example.com").one()
        user.is_active = False
        db.commit()

    assert client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "Password123!"},
    ).status_code == 401

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refresh_response.status_code == 401


def test_rbac_protected_endpoint_accepts_allowed_roles_and_denies_others():
    create_user(email="super@example.com", full_name="Super Admin")
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "super@example.com").one()
        user.roles = [db.query(Role).filter(Role.name == "SUPER_ADMIN").one()]
        db.commit()

    super_tokens = login_user(email="super@example.com")
    super_response = client.get(
        "/rbac-test",
        headers={"Authorization": f"Bearer {super_tokens['access_token']}"},
    )
    assert super_response.status_code == 200, super_response.text
    assert super_response.json()["message"] == "RBAC check passed"

    create_user(email="customer@example.com", full_name="Plain Customer")
    customer_tokens = login_user(email="customer@example.com")
    customer_response = client.get(
        "/rbac-test",
        headers={"Authorization": f"Bearer {customer_tokens['access_token']}"},
    )
    assert customer_response.status_code == 403


def test_admin_role_is_also_allowed_by_rbac_endpoint():
    create_user(email="admin@example.com", full_name="Platform Admin")
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "admin@example.com").one()
        user.roles = [db.query(Role).filter(Role.name == "ADMIN").one()]
        db.commit()

    tokens = login_user(email="admin@example.com")
    response = client.get(
        "/rbac-test",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_authentication_and_authorization_coverages():
    create_user(email="authz@example.com")
    login = login_user(email="authz@example.com")
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert me.status_code == 200

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "authz@example.com").one()
        user.is_active = False
        db.commit()

    protected = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert protected.status_code == 401
