from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from app.main import app
from app.database import Base, get_db
from app.models import Role

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)

def override_db():
    db = TestingSession()
    try: yield db
    finally: db.close()

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    db = TestingSession(); db.add(Role(name="CUSTOMER")); db.commit(); db.close()
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

def test_register_login_and_me():
    response = client.post("/api/v1/auth/register", json={"email":"user@example.com","password":"Password123!","full_name":"Test User"})
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email":"user@example.com","password":"Password123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization":f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["roles"] == ["CUSTOMER"]

def test_duplicate_and_bad_login():
    payload = {"email":"user@example.com","password":"Password123!","full_name":"Test User"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email":payload["email"],"password":"wrong-password"}).status_code == 401

def test_authentication_and_authorization():
    assert client.get("/api/v1/auth/me").status_code == 401
    response = client.post("/api/v1/auth/register", json={"email":"user@example.com","password":"Password123!","full_name":"Test User"})
    login = client.post("/api/v1/auth/login", json={"email":"user@example.com","password":"Password123!"})
    assert client.get("/api/v1/auth/me", headers={"Authorization":f"Bearer {login.json()['access_token']}"}).status_code == 200
