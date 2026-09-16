from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.employee import Employee


class Role(Base):
    """Represent an employee role or department."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="role",
    )

    def __repr__(self) -> str:
        return f"Role(id={self.id!r}, name={self.name!r})"
