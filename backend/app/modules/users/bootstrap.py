import argparse
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.modules.users.models import Role, User, UserRole


def bootstrap_admin(session: Session, subject: UUID, display_name: str) -> User:
    display_name = display_name.strip()
    if not 1 <= len(display_name) <= 200:
        raise ValueError("Display name must contain 1–200 characters")
    with session.begin():
        # Serialize first-admin creation across concurrent operator commands.
        session.execute(text("SELECT pg_advisory_xact_lock(741302001)"))
        if session.scalar(select(UserRole).where(UserRole.role == Role.ADMIN)):
            raise ValueError("An administrator already exists; bootstrap refused")
        if session.scalar(select(User).where(User.auth_subject == subject)):
            raise ValueError("Subject already exists; bootstrap refused")
        user = User(
            auth_subject=subject,
            display_name=display_name,
            roles=[UserRole(role=Role.ADMIN)],
        )
        session.add(user)
        session.flush()
    return user


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap the first local administrator"
    )
    parser.add_argument("--subject", type=UUID, required=True)
    parser.add_argument("--display-name", required=True)
    args = parser.parse_args()
    engine = create_database_engine(Settings())
    try:
        with Session(engine) as session:
            try:
                bootstrap_admin(session, args.subject, args.display_name)
            except ValueError as error:
                parser.exit(1, str(error) + "\n")
        print("First administrator created")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
