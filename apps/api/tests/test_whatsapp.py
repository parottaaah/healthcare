import pytest
from unittest.mock import patch, MagicMock, ANY
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db import get_db
from tests.test_api import TestingSessionLocal, engine
from app.models.base import Base

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_verify_webhook_success():
    # Setup mock verify token
    settings.whatsapp_verify_token = "secret_token"
    
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": 123456789,
            "hub.verify_token": "secret_token"
        }
    )
    assert response.status_code == 200
    assert response.text == "123456789"

def test_verify_webhook_fail():
    settings.whatsapp_verify_token = "secret_token"
    
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": 123456789,
            "hub.verify_token": "wrong_token"
        }
    )
    assert response.status_code == 403

@patch('app.routers.whatsapp.session_service')
@patch('app.routers.whatsapp.whatsapp_client')
@patch('app.routers.whatsapp.answer_question')
def test_webhook_text_message(mock_answer_question, mock_whatsapp_client, mock_session):
    mock_session.get_session.return_value = {"last_bill_id": "test_bill_id"}
    mock_answer_question.return_value = "This is a mock answer from the LLM."
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "type": "text",
                        "text": {"body": "Why is this bill so high?"}
                    }]
                }
            }]
        }]
    }
    
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    
    mock_answer_question.assert_called_once_with("test_bill_id", "Why is this bill so high?", ANY)
    mock_whatsapp_client.send_text_message.assert_called_once_with("1234567890", "This is a mock answer from the LLM.")

@patch('app.routers.whatsapp.storage_service')
@patch('app.routers.whatsapp.whatsapp_client')
@patch('app.routers.whatsapp.bill_parser')
@patch('app.routers.whatsapp.explain_bill')
@patch('app.routers.whatsapp.session_service')
def test_webhook_image_message(mock_session, mock_explain, mock_parser, mock_whatsapp_client, mock_storage):
    mock_whatsapp_client.download_media.return_value = b"dummy_image_data"
    mock_storage.save_bytes.return_value = "/mock/path/to/image.jpg"
    mock_parser.extract_text.return_value = "Mock parsed text"
    mock_parser.parse_line_items.return_value = [{"description": "Test", "amount": 100.0}]
    mock_explain.return_value = {"flagged_items": 1, "total_items": 1}
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "type": "image",
                        "image": {"id": "media_123"}
                    }]
                }
            }]
        }]
    }
    
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    
    mock_whatsapp_client.download_media.assert_called_once_with("media_123")
    mock_storage.save_bytes.assert_called_once_with(b"dummy_image_data", ext=".jpg")
    mock_whatsapp_client.send_text_message.assert_called_once()
    
    call_args = mock_whatsapp_client.send_text_message.call_args[0]
    assert call_args[0] == "1234567890"
    assert "1 potential overcharge(s)" in call_args[1]
