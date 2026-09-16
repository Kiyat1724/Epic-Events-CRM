from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.client import Client
    from epic_events.models.event import Event
    from epic_events.models.role import Role


class Employee(Base):
    """Represent an Epic Events employee."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)

    employee_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    role: Mapped["Role"] = relationship(
        back_populates="employees",
    )

    clients: Mapped[list["Client"]] = relationship(
        back_populates="sales_contact",
        foreign_keys="Client.sales_contact_id",
    )

    supported_events: Mapped[list["Event"]] = relationship(
        back_populates="support_contact",
        foreign_keys="Event.support_contact_id",
    )

    def __repr__(self) -> str:
        return (
            f"Employee(id={self.id!r}, "
            f"employee_number={self.employee_number!r}, "
            f"full_name={self.full_name!r}, "
            f"email={self.email!r})"
        )
