import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, Enum as SQLEnum
from app.models.base import Base, CreatedAtMixin

class Channel(str, enum.Enum):
    whatsapp = "whatsapp"
    web = "web"

class Conversation(Base, CreatedAtMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[Channel] = mapped_column(SQLEnum(Channel))
