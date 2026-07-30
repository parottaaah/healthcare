import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, Enum as SQLEnum, Text
from app.models.base import Base, CreatedAtMixin

class Role(str, enum.Enum):
    user = "user"
    assistant = "assistant"

class Message(Base, CreatedAtMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[Role] = mapped_column(SQLEnum(Role))
    content: Mapped[str] = mapped_column(Text)
