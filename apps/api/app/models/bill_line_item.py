import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, Numeric, Boolean
from app.models.base import Base, CreatedAtMixin

class BillLineItem(Base, CreatedAtMixin):
    __tablename__ = "bill_line_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bills.id"))
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric)
    flagged_overcharge: Mapped[bool] = mapped_column(Boolean, default=False)
