import os
import uuid
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.services.bill_parser import parse_line_items, extract_text
from app.models.bill import Bill
from app.models.bill_line_item import BillLineItem
import app.services.bill_explainer

# We import the test client and engine from our existing test_api setup
# But we need to make sure the db is created and passed around.
# For simplicity, we'll configure a TestClient directly here or import it from test_api if possible.
from tests.test_api import client, TestingSessionLocal, engine
from app.models.base import Base

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def test_parse_line_items():
    raw_text = """
    Patient: John Doe
    Date: 2023-10-12
    
    Consultation Fee    $150.00
    Blood Test 1       45.50
    X-Ray Scan         120.00
    Total              $315.50
    """
    items = parse_line_items(raw_text)
    
    assert len(items) == 4
    assert items[0]["description"] == "Consultation Fee"
    assert items[0]["amount"] == 150.0
    assert items[1]["description"] == "Blood Test 1"
    assert items[1]["amount"] == 45.50
    assert items[2]["description"] == "X-Ray Scan"
    assert items[2]["amount"] == 120.0
    assert items[3]["description"] == "Total"
    assert items[3]["amount"] == 315.5

def test_extract_text(tmp_path):
    # Generate a tiny dummy image
    img_path = tmp_path / "dummy.png"
    img = Image.new('RGB', (100, 30), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Test", fill=(0,0,0))
    img.save(img_path)
    
    try:
        text = extract_text(str(img_path))
        assert isinstance(text, str)
    except Exception as e:
        pytest.skip(f"Tesseract may not be installed locally: {e}")

@patch('app.services.bill_parser.extract_text')
def test_upload_bill(mock_extract, tmp_path):
    mock_extract.return_value = "Consultation Fee  150.00\nX-Ray Scan  120.00"
    
    # Create dummy file
    test_file_path = tmp_path / "test_bill.jpg"
    test_file_path.write_text("dummy image content")
    
    # Create a dummy user in db
    db = TestingSessionLocal()
    from app.models.user import User
    import uuid
    from app.services.auth import create_access_token
    new_user = User(
        phone_number=f"555-{uuid.uuid4().hex[:6]}",
        name="Test Upload User",
        email=f"upload_{uuid.uuid4().hex[:6]}@example.com"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(str(new_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(test_file_path, "rb") as f:
        response = client.post(
            "/bills/upload",
            headers=headers,
            files={"file": ("test_bill.jpg", f, "image/jpeg")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "parsed"
    assert data["total_amount"] == 270.0
    assert len(data["line_items"]) == 2
    
    db.close()

def test_upload_invalid_extension(tmp_path):
    test_file_path = tmp_path / "test_bill.txt"
    test_file_path.write_text("hello")
    
    # Create a dummy user in db
    db = TestingSessionLocal()
    from app.models.user import User
    import uuid
    from app.services.auth import create_access_token
    new_user = User(
        phone_number=f"555-{uuid.uuid4().hex[:6]}",
        name="Test Upload User 2",
        email=f"upload2_{uuid.uuid4().hex[:6]}@example.com"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(str(new_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(test_file_path, "rb") as f:
        response = client.post(
            "/bills/upload",
            headers=headers,
            files={"file": ("test_bill.txt", f, "text/plain")}
        )
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]
    db.close()

@patch('app.services.bill_explainer.anthropic_client')
def test_explain_line_item_success(mock_anthropic):
    from app.services.bill_explainer import explain_line_item
    import json
    
    # Mock Anthropic Response
    mock_message = mock_anthropic.messages.create.return_value
    mock_message.content = [type('obj', (object,), {'text': '{"explanation": "A common blood test", "flagged": false, "reasoning": "Standard charge"}'})]
    
    result = explain_line_item("Blood Test", 50.0)
    assert result["explanation"] == "A common blood test"
    assert result["flagged"] is False

@patch('app.services.bill_explainer.anthropic_client')
def test_explain_line_item_malformed(mock_anthropic):
    from app.services.bill_explainer import explain_line_item
    
    # Mock Malformed Response
    mock_message = mock_anthropic.messages.create.return_value
    mock_message.content = [type('obj', (object,), {'text': 'not valid json'})]
    
    result = explain_line_item("Blood Test", 50.0)
    assert "Failed to generate explanation" in result["explanation"]

@patch('app.services.bill_explainer.anthropic_client')
@patch('app.services.bill_parser.extract_text')
def test_explain_bill_endpoint(mock_extract, mock_anthropic, tmp_path):
    mock_extract.return_value = "Consultation Fee  150.00"
    
    mock_message = mock_anthropic.messages.create.return_value
    mock_message.content = [type('obj', (object,), {'text': '{"explanation": "Doctor visit", "flagged": true, "reasoning": "Too high"}'})]
    
    test_file_path = tmp_path / "test_bill2.jpg"
    test_file_path.write_text("dummy")
    
    db = TestingSessionLocal()
    from app.models.user import User
    import uuid
    from app.services.auth import create_access_token
    new_user = User(
        phone_number=f"555-{uuid.uuid4().hex[:6]}",
        name="Test Explain",
        email=f"explain_{uuid.uuid4().hex[:6]}@example.com"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(str(new_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(test_file_path, "rb") as f:
        upload_resp = client.post(
            "/bills/upload",
            headers=headers,
            files={"file": ("test_bill2.jpg", f, "image/jpeg")}
        )
    
    bill_id = upload_resp.json()["id"]
    
    # Call explain
    explain_resp = client.post(f"/bills/{bill_id}/explain", headers=headers)
    assert explain_resp.status_code == 200
    
    data = explain_resp.json()
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["explanation"] == "Doctor visit"
    assert data["line_items"][0]["flagged_overcharge"] is True
    
    db.close()
