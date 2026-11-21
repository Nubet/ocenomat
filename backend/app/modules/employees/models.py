from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PositionKind(StrEnum):
    OFFICE_HEAD = "OFFICE_HEAD"
    DIRECT_MANAGER = "DIRECT_MANAGER"
    OTHER = "OTHER"


class OrganizationalUnit(Base):
    __tablename__ = "organizational_units"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0"),
        CheckConstraint("length(trim(position)) > 0"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    position: Mapped[str] = mapped_column(String(200))
    position_kind: Mapped[PositionKind] = mapped_column(
        Enum(PositionKind, native_enum=False, create_constraint=True)
    )
    unit_id: Mapped[UUID] = mapped_column(ForeignKey("organizational_units.id"))
    unit: Mapped[OrganizationalUnit] = relationship(lazy="joined")


class ManagerEmployeeAssignment(Base):
    __tablename__ = "manager_employee_assignments"

    manager_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True, index=True
    )
