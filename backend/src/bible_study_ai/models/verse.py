from datetime import datetime
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bible_study_ai.database import Base

if TYPE_CHECKING:
    from bible_study_ai.models.chapter import Chapter


class Verse(Base):
    __tablename__ = "verses"

    __table_args__ = (
        UniqueConstraint(
            "chapter_id",
            "number",
            name="uq_verses_chapter_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    chapter_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("chapters.id"),
        nullable=False,
    )
    number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    chapter: Mapped["Chapter"] = relationship(
        back_populates="verses",
    )