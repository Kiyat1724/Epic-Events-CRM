from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Role


class RoleRepository:
    """Manage role queries in the database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)
        return self.session.scalar(statement)
