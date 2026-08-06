import uuid
from fastapi.testclient import TestClient

from tests.test_api import client, TestingSessionLocal, engine
from app.models.base import Base
from app.models.user import User

Base.metadata.create_all(bind=engine)

_test_suffix = uuid.uuid4().hex[:8]
_test_email = f"test_{_test_suffix}@example.com"
_test_phone = f"123-{_test_suffix}"
_test_password = "strongpassword123"

def test_register_success():
    response = client.post(
        "/auth/register",
        json={
            "email": _test_email,
            "password": _test_password,
            "name": "Test User",
            "phone_number": _test_phone
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "csrf_token" in response.cookies
    assert response.json()["message"] == "Registered successfully"

def test_register_duplicate_email():
    # Attempt to register again with same email
    response = client.post(
        "/auth/register",
        json={
            "email": _test_email,
            "password": _test_password,
            "name": "Test User 2",
            "phone_number": f"098-{_test_suffix}"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success():
    response = client.post(
        "/auth/login",
        json={
            "email": _test_email,
            "password": _test_password
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "csrf_token" in response.cookies
    assert response.json()["message"] == "Logged in successfully"

def test_login_failure():
    response = client.post(
        "/auth/login",
        json={
            "email": _test_email,
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
            "email": _test_email,
            "password": _test_password
        }
    )
    access_token = login_response.cookies.get("access_token")
    
    # Access protected endpoint using cookie (no CSRF needed for GET)
    response = client.get(
        "/bills",
        cookies={"access_token": access_token}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_csrf_protection_missing_header():
    login_response = client.post(
        "/auth/login",
        json={
            "email": _test_email,
            "password": _test_password
        }
    )
    access_token = login_response.cookies.get("access_token")
    csrf_token = login_response.cookies.get("csrf_token")
    
    # Missing CSRF header
    response = client.post(
        "/auth/logout",
        cookies={"access_token": access_token, "csrf_token": csrf_token}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token validation failed"

def test_csrf_protection_success():
    login_response = client.post(
        "/auth/login",
        json={
            "email": _test_email,
            "password": _test_password
        }
    )
    access_token = login_response.cookies.get("access_token")
    csrf_token = login_response.cookies.get("csrf_token")
    
    # With CSRF header
    response = client.post(
        "/auth/logout",
        cookies={"access_token": access_token, "csrf_token": csrf_token},
        headers={"x-csrf-token": csrf_token}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
