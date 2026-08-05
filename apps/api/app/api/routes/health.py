from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        db_ok = result == 1
    except Exception as e:
        db_ok = False
        raise HTTPException(status_code=503, detail="database unreachable")

    return {
        "status": "ok",
        "service": "sezhi-api",
        "db": "ok" if db_ok else "unreachable",
    }