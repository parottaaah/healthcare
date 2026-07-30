import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, Numeric, Enum as SQLEnum
from app.models.base import Base, TimestampMixin

class BillStatus(str, enum.Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    reviewed = "reviewed"

class Bill(Base, TimestampMixin):
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("providers.id"), nullable=True)
    raw_file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric)
    currency: Mapped[str] = mapped_column(String, default="INR")
    status: Mapped[BillStatus] = mapped_column(SQLEnum(BillStatus))
