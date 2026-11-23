from datetime import datetime
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bible_study_ai.database import Base

if TYPE_CHECKING:
    from bible_study_ai.models.book import Book
    from bible_study_ai.models.verse import Verse


class Chapter(Base):
    __tablename__ = "chapters"

    __table_args__ = (
        UniqueConstraint(
            "book_id",
            "number",
            name="uq_chapters_book_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    book_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("books.id"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    structure: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    book: Mapped["Book"] = relationship(
        back_populates="chapters",
    )

    verses: Mapped[list["Verse"]] = relationship(
        back_populates="chapter",
    )