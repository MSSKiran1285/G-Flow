"""Core domain entities (spec §3), MVP slice: Module/ModuleAttribute (what a scanned
screen looks like) and TestCase/TestStep (a reusable, ordered sequence of actions against
those attributes, with data-driven bindings). SQLite for now, via SQLAlchemy so Postgres
is a connection-string change later, per spec.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Module(Base):
    """A scanned SAP screen: technical metadata + its attributes."""

    __tablename__ = "module"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    tcode: Mapped[str] = mapped_column(String(20))
    screen_number: Mapped[str] = mapped_column(String(10), default="")
    root_id: Mapped[str] = mapped_column(String(500))
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    attributes: Mapped[list["ModuleAttribute"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="ModuleAttribute.component_id"
    )


class ModuleAttribute(Base):
    """One control on a Module's screen: locator + what it's known to support."""

    __tablename__ = "module_attribute"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    module_id: Mapped[str] = mapped_column(ForeignKey("module.id"))
    semantic_name: Mapped[str] = mapped_column(String(200))
    component_id: Mapped[str] = mapped_column(String(500))
    sap_type: Mapped[str] = mapped_column(String(50))
    sap_sub_type: Mapped[str] = mapped_column(String(50), default="")
    label: Mapped[str] = mapped_column(String(300), default="")
    supported_action_modes: Mapped[str] = mapped_column(Text, default="")  # comma-separated

    module: Mapped[Module] = relationship(back_populates="attributes")


class TestCase(Base):
    """Ordered TestSteps composing a reusable, data-driven test."""

    __tablename__ = "test_case"
    __test__ = False  # tell pytest this isn't a test class despite the name

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    steps: Mapped[list["TestStep"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan", order_by="TestStep.sequence_order"
    )


class TestStep(Base):
    """One Module-attribute instance in a TestCase: an ActionMode + a binding.

    binding_type: "literal" (binding_value used as-is) | "column" (binding_value names
    a TestSheet column, resolved per data row at run time).
    """

    __tablename__ = "test_step"
    __test__ = False  # tell pytest this isn't a test class despite the name

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    test_case_id: Mapped[str] = mapped_column(ForeignKey("test_case.id"))
    sequence_order: Mapped[int] = mapped_column(Integer)
    module_name: Mapped[str] = mapped_column(String(200), default="")
    attribute_semantic_name: Mapped[str] = mapped_column(String(200), default="")
    # Escape hatch for elements that aren't part of any scanned Module — e.g. a
    # conditional completeness-check popup that only exists after Save is pressed.
    raw_component_id: Mapped[str] = mapped_column(String(500), default="")
    action_mode: Mapped[str] = mapped_column(String(30))  # matches ActionOp names, e.g. "SET", "PRESS"
    binding_type: Mapped[str] = mapped_column(String(10), default="literal")
    binding_value: Mapped[str] = mapped_column(String(300), default="")
    optional: Mapped[bool] = mapped_column(default=False)  # skip (don't fail) if the component isn't found

    test_case: Mapped[TestCase] = relationship(back_populates="steps")
