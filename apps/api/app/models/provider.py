import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid
from app.models.base import Base, CreatedAtMixin

class Provider(Base, CreatedAtMixin):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
