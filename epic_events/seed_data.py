from sqlalchemy import select

from epic_events.database import session_scope
from epic_events.models import Role

ROLE_NAMES: tuple[str, ...] = (
    "management",
    "sales",
    "support",
)


def seed_roles() -> None:
    """Create the initial employee roles without creating duplicates."""
    with session_scope() as session:
        existing_roles = set(
            session.scalars(
                select(Role.name),
            ).all()
        )

        missing_roles = [
            role_name for role_name in ROLE_NAMES if role_name not in existing_roles
        ]

        if not missing_roles:
            print("Initial roles already exist.")
            return

        session.add_all(Role(name=role_name) for role_name in missing_roles)

        created_names = ", ".join(missing_roles)
        print(f"Initial roles created: {created_names}")


if __name__ == "__main__":
    seed_roles()
