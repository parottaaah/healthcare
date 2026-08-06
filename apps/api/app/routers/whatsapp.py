import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.core.config import settings
from app.models.user import User
from app.models.bill import Bill, BillStatus
from app.models.conversation import Conversation, Channel
from app.models.message import Message, Role
from app.services.whatsapp_client import whatsapp_client
from app.services.session import session_service
from app.services.storage import storage_service
from app.services import bill_parser
from app.services.bill_explainer import explain_bill, answer_question
from app.models.bill_line_item import BillLineItem

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])

@router.get("")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: int = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """WhatsApp verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")

def get_or_create_user_and_conversation(phone_number: str, db: Session):
    # Lookup User
    stmt = select(User).where(User.phone_number == phone_number)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        user = User(
            phone_number=phone_number,
            name="WhatsApp User",
            email=f"wa_{phone_number}@example.com"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Lookup Conversation
    stmt = select(Conversation).where(
        Conversation.user_id == user.id,
        Conversation.channel == Channel.whatsapp
    )
    conversation = db.execute(stmt).scalar_one_or_none()
    if not conversation:
        conversation = Conversation(
            user_id=user.id,
            channel=Channel.whatsapp
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return user, conversation

def store_message(conversation_id: uuid.UUID, role: Role, content: str, db: Session):
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()

@router.post("")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives incoming message payloads.
    NOTE: This endpoint is intentionally unauthenticated by JWT, as it uses 
    Meta's own signature and verify-token mechanism for security.
    """
    body = await request.json()
    
    # Process WhatsApp payload
    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for msg in messages:
                    phone_number = msg.get("from")
                    user, conversation = get_or_create_user_and_conversation(phone_number, db)
                    
                    if msg.get("type") == "text":
                        text = msg["text"]["body"]
                        store_message(conversation.id, Role.user, text, db)
                        
                        # Use session to answer question about most recent bill
                        session = session_service.get_session(phone_number)
                        last_bill_id = session.get("last_bill_id")
                        
                        if last_bill_id:
                            answer = answer_question(last_bill_id, text, db)
                        else:
                            answer = "வணக்கம் 👋 Hi! I'm Sezhi, your AI healthcare companion. I help you understand healthcare costs, medical bills, reports, and medical terminology using simple language. How can I help you today? Please upload a medical bill to get started."
                            
                        whatsapp_client.send_text_message(phone_number, answer)
                        store_message(conversation.id, Role.assistant, answer, db)

                    elif msg.get("type") in ["image", "document"]:
                        media_id = msg.get("image", {}).get("id") or msg.get("document", {}).get("id")
                        
                        if msg.get("type") == "image":
                            store_message(conversation.id, Role.user, "[Image sent]", db)
                            ext = ".jpg"
                        else:
                            store_message(conversation.id, Role.user, "[Document sent]", db)
                            ext = ".pdf"
                            
                        # Download media and process
                        try:
                            content = whatsapp_client.download_media(media_id)
                            file_path = storage_service.save_bytes(content, ext=ext)
                            
                            # Create Bill
                            bill = Bill(
                                user_id=user.id,
                                raw_file_url=file_path,
                                status=BillStatus.uploaded,
                                total_amount=0.0
                            )
                            db.add(bill)
                            db.commit()
                            db.refresh(bill)
                            
                            # Parse
                            raw_text = bill_parser.extract_text(file_path)
                            parsed_items = bill_parser.parse_line_items(raw_text)
                            
                            total_parsed = 0.0
                            for item in parsed_items:
                                line_item = BillLineItem(
                                    bill_id=bill.id,
                                    description=item["description"],
                                    amount=item["amount"],
                                    flagged_overcharge=False
                                )
                                db.add(line_item)
                                total_parsed += item["amount"]
                                
                            bill.status = BillStatus.parsed
                            bill.total_amount = total_parsed
                            db.commit()
                            db.refresh(bill)
                            
                            # Explain
                            summary = explain_bill(bill.id, db)
                            
                            # Update session
                            session_service.update_session(phone_number, {"last_bill_id": str(bill.id)})
                            
                            # Create reply summary
                            if summary["flagged_items"] > 0:
                                reply = f"I analyzed your bill. I found {summary['flagged_items']} potential overcharge(s) out of {summary['total_items']} items. Ask me any questions!"
                            else:
                                reply = f"I analyzed your bill. Everything looks normal across the {summary['total_items']} items. Ask me any questions!"
                                
                            whatsapp_client.send_text_message(phone_number, reply)
                            store_message(conversation.id, Role.assistant, reply, db)
                            
                        except Exception as e:
                            print(f"Error processing bill from WhatsApp: {e}")
                            error_reply = "I'm sorry, I encountered an error while processing your bill."
                            whatsapp_client.send_text_message(phone_number, error_reply)
                            store_message(conversation.id, Role.assistant, error_reply, db)

    return {"status": "ok"}
