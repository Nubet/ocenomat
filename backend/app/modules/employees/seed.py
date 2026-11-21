import argparse
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
    PositionKind,
)
from app.modules.users.models import Role, User

UNIT_ID = uuid5(NAMESPACE_URL, "kompas:fictional:unit")
UNIT_NAME = "Biuro Dyrektora Generalnego / Zespół Koordynacji Procesów"
FICTIONAL_EMPLOYEES = (
    ("jan", "Jan Kowalski", "Starszy specjalista", PositionKind.OTHER),
    ("maria", "Maria Wiśniewska", "Radca", PositionKind.OTHER),
    ("alicja", "Alicja Zielińska", "Główny specjalista", PositionKind.OTHER),
    ("piotr", "Piotr Nowak", "Naczelnik wydziału", PositionKind.DIRECT_MANAGER),
)


def seed_fictional_employees(session: Session, manager_subject: UUID) -> None:
    with session.begin():
        session.execute(text("SELECT pg_advisory_xact_lock(741302003)"))
        manager = session.scalar(
            select(User).where(User.auth_subject == manager_subject)
        )
        if (
            manager is None
            or not manager.active
            or Role.MANAGER not in {role.role for role in manager.roles}
        ):
            raise ValueError("An active local MANAGER is required")
        unit = session.get(OrganizationalUnit, UNIT_ID)
        if unit is None:
            session.add(OrganizationalUnit(id=UNIT_ID, name=UNIT_NAME))
            session.flush()
        elif unit.name == "Jednostka testowa — dane fikcyjne":
            unit.name = UNIT_NAME
        for slug, name, position, kind in FICTIONAL_EMPLOYEES:
            employee_id = uuid5(NAMESPACE_URL, f"kompas:fictional:employee:{slug}")
            if session.get(Employee, employee_id) is None:
                session.add(
                    Employee(
                        id=employee_id,
                        name=name,
                        position=position,
                        position_kind=kind,
                        unit_id=UNIT_ID,
                    )
                )
                session.flush()
            # Leave Piotr unassigned to demonstrate access isolation.
            if (
                slug != "piotr"
                and session.get(ManagerEmployeeAssignment, (manager.id, employee_id))
                is None
            ):
                session.add(
                    ManagerEmployeeAssignment(
                        manager_id=manager.id, employee_id=employee_id
                    )
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed explicit fictional employees; never import browser demo state"
    )
    parser.add_argument("--manager-subject", type=UUID, required=True)
    args = parser.parse_args()
    engine = create_database_engine(Settings())
    try:
        with Session(engine) as session:
            try:
                seed_fictional_employees(session, args.manager_subject)
            except ValueError as error:
                parser.exit(1, str(error) + "\n")
        print(
            "Fictional employees seeded; three assigned to the manager, one unassigned"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
