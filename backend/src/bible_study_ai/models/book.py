import enum
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bible_study_ai.database import Base

if TYPE_CHECKING:
    from bible_study_ai.models.chapter import Chapter
    from bible_study_ai.models.translation import Translation


class Testament(str, enum.Enum):
    OLD = "old"
    NEW = "new"


class Book(Base):
    __tablename__ = "books"

    __table_args__ = (
        UniqueConstraint(
            "translation_id",
            "usfm_id",
            name="uq_books_translation_usfm_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    translation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("translations.id"),
        nullable=False,
    )
    usfm_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    osis_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    testament: Mapped[Testament] = mapped_column(
        Enum(
            Testament,
            name="testament",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    translation: Mapped["Translation"] = relationship(
        back_populates="books",
    )

    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="book",
    )