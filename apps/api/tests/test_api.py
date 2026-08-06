import pytest
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sezhi-api",
        "db": "ok"
    }

def test_create_user(db_session=None):
    from app.models.user import User
    import uuid
    
    db = TestingSessionLocal()
    unique_suffix = uuid.uuid4().hex[:8]
    new_user = User(
        phone_number=f"123-{unique_suffix}",
        name="Test User",
        email=f"test_{unique_suffix}@example.com"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    assert new_user.id is not None
    assert new_user.name == "Test User"
    
    # cleanup
    db.delete(new_user)
    db.commit()
    db.close()
