from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("size BETWEEN 1 AND 10485760"),
        CheckConstraint("kind = 'attachment'"),
        CheckConstraint("length(filename) BETWEEN 1 AND 255"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20), default="attachment")
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column()
    sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(150), unique=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
