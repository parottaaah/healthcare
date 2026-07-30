from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    db_ok = result.scalar() == 1

    return {
        "status": "ok" if db_ok else "database unreachable",
        "service": "decryptcare-api",
        "database_connected": db_ok,
    }