import uuid
from fastapi.testclient import TestClient

from tests.test_api import client, TestingSessionLocal, engine
from app.models.base import Base
from app.models.user import User

Base.metadata.create_all(bind=engine)

def test_register_success():
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "name": "Test User",
            "phone_number": "1234567890"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_register_duplicate_email():
    # Attempt to register again with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "name": "Test User 2",
            "phone_number": "0987654321"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success():
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_protected_endpoint_no_token():
    response = client.get("/bills")
    assert response.status_code == 401

def test_protected_endpoint_with_token():
    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/bills",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
