import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Any

from app.db import get_db
from app.models.bill import Bill, BillStatus
from app.models.bill_line_item import BillLineItem
from app.services.storage import storage_service
from app.services import bill_parser

router = APIRouter(prefix="/bills", tags=["bills"])

ALLOWED_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload")
def upload_bill(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="File type not allowed. Must be PDF, JPEG, or PNG."
        )

    # Validate size
    # We read the file content to get size, then seek back
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 10MB limit."
        )

    # 1. Save file via storage service
    file_path = storage_service.save(file)
    
    # 2. Create Bill row
    bill = Bill(
        user_id=user_id,
        raw_file_url=file_path,
        status=BillStatus.uploaded,
        total_amount=0.0  # Will update after parsing or keep as placeholder
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    # 3. Run parsing pipeline synchronously (TODO: move to background task later)
    try:
        raw_text = bill_parser.extract_text(file_path)
        parsed_items = bill_parser.parse_line_items(raw_text)
        
        # 4. Create BillLineItem rows
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
            
        # 5. Update bill status
        bill.status = BillStatus.parsed
        bill.total_amount = total_parsed
        db.commit()
        db.refresh(bill)
        
    except Exception as e:
        # In a real app we might mark it as 'failed' or log it
        print(f"Parsing failed: {e}")
        pass

    # Fetch line items for return
    stmt = select(BillLineItem).where(BillLineItem.bill_id == bill.id)
    line_items = db.execute(stmt).scalars().all()

    return {
        "id": bill.id,
        "user_id": bill.user_id,
        "status": bill.status,
        "total_amount": bill.total_amount,
        "raw_file_url": bill.raw_file_url,
        "line_items": [
            {
                "id": li.id,
                "description": li.description,
                "amount": li.amount,
                "flagged_overcharge": li.flagged_overcharge
            }
            for li in line_items
        ]
    }

@router.get("/{bill_id}")
def get_bill(bill_id: uuid.UUID, db: Session = Depends(get_db)):
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    stmt = select(BillLineItem).where(BillLineItem.bill_id == bill.id)
    line_items = db.execute(stmt).scalars().all()

    return {
        "id": bill.id,
        "user_id": bill.user_id,
        "status": bill.status,
        "total_amount": bill.total_amount,
        "raw_file_url": bill.raw_file_url,
        "line_items": [
            {
                "id": li.id,
                "description": li.description,
                "amount": li.amount,
                "flagged_overcharge": li.flagged_overcharge
            }
            for li in line_items
        ]
    }

@router.get("")
def list_bills(user_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(Bill).where(Bill.user_id == user_id)
    bills = db.execute(stmt).scalars().all()
    
    return [
        {
            "id": b.id,
            "status": b.status,
            "total_amount": b.total_amount
        }
        for b in bills
    ]
