from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.contract import Contract
    from epic_events.models.employee import Employee


class Event(Base):
    """Represent an event organized by Epic Events."""

    __tablename__ = "events"

    __table_args__ = (
        CheckConstraint(
            "attendees > 0",
            name="ck_event_attendees_positive",
        ),
        CheckConstraint(
            "end_date > start_date",
            name="ck_event_end_after_start",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    attendees: Mapped[int] = mapped_column(
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    support_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    contract: Mapped["Contract"] = relationship(
        back_populates="event",
    )

    support_contact: Mapped["Employee | None"] = relationship(
        back_populates="supported_events",
        foreign_keys=[support_contact_id],
    )

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id!r}, "
            f"contract_id={self.contract_id!r}, "
            f"name={self.name!r}, "
            f"start_date={self.start_date!r}, "
            f"end_date={self.end_date!r})"
        )
