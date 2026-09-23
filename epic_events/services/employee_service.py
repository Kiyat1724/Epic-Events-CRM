from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.auth_service import hash_password
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import require_management

VALID_ROLE_NAMES = frozenset(
    {
        "management",
        "sales",
        "support",
    }
)


class EmployeeNotFoundError(Exception):
    """Raised when an employee cannot be found."""


class CurrentEmployeeDeletionError(Exception):
    """Raised when a manager tries to delete their own account."""


class EmployeeService:
    """Apply business rules related to employees."""

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        role_repository: RoleRepository,
    ) -> None:
        self.employee_repository = employee_repository
        self.role_repository = role_repository

    def list_employees(
        self,
        identity: TokenPayload,
    ) -> list[Employee]:
        """Return every employee to an authenticated manager."""

        require_management(identity)
        return self.employee_repository.list_all()

    def get_employee(
        self,
        identity: TokenPayload,
        *,
        employee_id: int,
    ) -> Employee:
        """Return one employee to an authenticated manager."""

        require_management(identity)

        employee = self.employee_repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} was not found.")

        return employee

    def create_employee(
        self,
        *,
        employee_number: str,
        full_name: str,
        email: str,
        password: str,
        role_name: str,
    ) -> Employee:
        """Create and persist an employee."""

        normalized_employee_number = employee_number.strip()
        normalized_full_name = full_name.strip()
        normalized_email = email.strip().lower()
        normalized_role_name = role_name.strip().lower()

        self._validate_required_fields(
            employee_number=normalized_employee_number,
            full_name=normalized_full_name,
            email=normalized_email,
        )
        self._validate_role_name(normalized_role_name)
        self._check_unique_employee_data(
            employee_number=normalized_employee_number,
            email=normalized_email,
        )

        role = self._get_role(normalized_role_name)

        employee = Employee(
            employee_number=normalized_employee_number,
            full_name=normalized_full_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
        )

        return self.employee_repository.add(employee)

    def update_employee(
        self,
        identity: TokenPayload,
        *,
        employee_id: int,
        employee_number: str,
        full_name: str,
        email: str,
        role_name: str,
        password: str | None = None,
    ) -> Employee:
        """Update an employee as an authenticated manager."""

        require_management(identity)

        employee = self.employee_repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} was not found.")

        normalized_employee_number = employee_number.strip()
        normalized_full_name = full_name.strip()
        normalized_email = email.strip().lower()
        normalized_role_name = role_name.strip().lower()

        self._validate_required_fields(
            employee_number=normalized_employee_number,
            full_name=normalized_full_name,
            email=normalized_email,
        )
        self._validate_role_name(normalized_role_name)
        self._check_unique_employee_data(
            employee_number=normalized_employee_number,
            email=normalized_email,
            ignored_employee_id=employee.id,
        )

        role = self._get_role(normalized_role_name)

        employee.employee_number = normalized_employee_number
        employee.full_name = normalized_full_name
        employee.email = normalized_email
        employee.role = role

        if password:
            employee.password_hash = hash_password(password)

        return self.employee_repository.save(employee)

    def delete_employee(
        self,
        identity: TokenPayload,
        *,
        employee_id: int,
    ) -> None:
        """Delete an employee as an authenticated manager."""

        require_management(identity)

        if identity.employee_id == employee_id:
            raise CurrentEmployeeDeletionError(
                "You cannot delete your own employee account."
            )

        employee = self.employee_repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} was not found.")

        self.employee_repository.delete(employee)

    def _check_unique_employee_data(
        self,
        *,
        employee_number: str,
        email: str,
        ignored_employee_id: int | None = None,
    ) -> None:
        """Reject an email or employee number already in use."""

        employee_with_email = self.employee_repository.get_by_email(email)

        if (
            employee_with_email is not None
            and employee_with_email.id != ignored_employee_id
        ):
            raise ValueError("An employee with this email already exists.")

        employee_with_number = self.employee_repository.get_by_employee_number(
            employee_number
        )

        if (
            employee_with_number is not None
            and employee_with_number.id != ignored_employee_id
        ):
            raise ValueError("An employee with this employee number already exists.")

    def _get_role(self, role_name: str):
        """Return an existing role or raise a clear error."""

        role = self.role_repository.get_by_name(role_name)

        if role is None:
            raise ValueError(
                "Role does not exist. " "Run the initial data seeding command."
            )

        return role

    @staticmethod
    def _validate_role_name(role_name: str) -> None:
        """Validate an Epic Events role name."""

        if role_name not in VALID_ROLE_NAMES:
            raise ValueError("Role must be management, sales, or support.")

    @staticmethod
    def _validate_required_fields(
        *,
        employee_number: str,
        full_name: str,
        email: str,
    ) -> None:
        """Validate the required employee values."""

        if not employee_number:
            raise ValueError("Employee number is required.")

        if not full_name:
            raise ValueError("Full name is required.")

        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")
