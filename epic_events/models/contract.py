from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.client import Client
    from epic_events.models.event import Event


def utc_now() -> datetime:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc)


class Contract(Base):
    """Represent a contract between Epic Events and a client."""

    __tablename__ = "contracts"

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_contract_total_amount_non_negative",
        ),
        CheckConstraint(
            "remaining_amount >= 0",
            name="ck_contract_remaining_amount_non_negative",
        ),
        CheckConstraint(
            "remaining_amount <= total_amount",
            name="ck_contract_remaining_not_above_total",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    signed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    client: Mapped["Client"] = relationship(
        back_populates="contracts",
    )

    event: Mapped["Event | None"] = relationship(
        back_populates="contract",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"Contract(id={self.id!r}, "
            f"client_id={self.client_id!r}, "
            f"total_amount={self.total_amount!r}, "
            f"remaining_amount={self.remaining_amount!r}, "
            f"signed={self.signed!r})"
        )
