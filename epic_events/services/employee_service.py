from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.auth_service import hash_password

VALID_ROLE_NAMES = frozenset({"management", "sales", "support"})


class EmployeeService:
    """Apply business rules related to employees."""

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        role_repository: RoleRepository,
    ) -> None:
        self.employee_repository = employee_repository
        self.role_repository = role_repository

    def create_employee(
        self,
        *,
        employee_number: str,
        full_name: str,
        email: str,
        password: str,
        role_name: str,
    ) -> Employee:
        normalized_employee_number = employee_number.strip()
        normalized_full_name = full_name.strip()
        normalized_email = email.strip().lower()
        normalized_role_name = role_name.strip().lower()

        self._validate_required_fields(
            employee_number=normalized_employee_number,
            full_name=normalized_full_name,
            email=normalized_email,
        )

        if normalized_role_name not in VALID_ROLE_NAMES:
            raise ValueError("Role must be management, sales, or support.")

        if self.employee_repository.get_by_email(normalized_email) is not None:
            raise ValueError("An employee with this email already exists.")

        if (
            self.employee_repository.get_by_employee_number(normalized_employee_number)
            is not None
        ):
            raise ValueError("An employee with this employee number already exists.")

        role = self.role_repository.get_by_name(normalized_role_name)
        if role is None:
            raise ValueError(
                "Role does not exist. Run the initial data seeding command."
            )

        employee = Employee(
            employee_number=normalized_employee_number,
            full_name=normalized_full_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
        )

        return self.employee_repository.add(employee)

    @staticmethod
    def _validate_required_fields(
        *,
        employee_number: str,
        full_name: str,
        email: str,
    ) -> None:
        if not employee_number:
            raise ValueError("Employee number is required.")

        if not full_name:
            raise ValueError("Full name is required.")

        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")
