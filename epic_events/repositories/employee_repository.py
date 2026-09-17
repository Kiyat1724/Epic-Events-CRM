from sqlalchemy import select
from sqlalchemy.orm import Session

from epic_events.models import Employee


class EmployeeRepository:
    """Manage employee persistence in the database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> Employee | None:
        statement = select(Employee).where(Employee.email == email)
        return self.session.scalar(statement)

    def get_by_employee_number(
        self,
        employee_number: str,
    ) -> Employee | None:
        statement = select(Employee).where(Employee.employee_number == employee_number)
        return self.session.scalar(statement)

    def exists_by_role_name(self, role_name: str) -> bool:
        statement = (
            select(Employee.id).where(Employee.role.has(name=role_name)).limit(1)
        )
        return self.session.scalar(statement) is not None

    def add(self, employee: Employee) -> Employee:
        self.session.add(employee)
        self.session.flush()
        self.session.refresh(employee)
        return employee
