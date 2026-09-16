from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.contract import Contract
    from epic_events.models.employee import Employee


def utc_now() -> datetime:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc)


class Client(Base):
    """Represent an Epic Events client."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sales_contact_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
    )

    sales_contact: Mapped["Employee"] = relationship(
        back_populates="clients",
        foreign_keys=[sales_contact_id],
    )

    contracts: Mapped[list["Contract"]] = relationship(
        back_populates="client",
    )

    def __repr__(self) -> str:
        return (
            f"Client(id={self.id!r}, "
            f"full_name={self.full_name!r}, "
            f"email={self.email!r}, "
            f"company_name={self.company_name!r})"
        )
