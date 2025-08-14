"""Tests for `recursive_delete` utility."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

# Import `recursive_delete` without triggering heavy package initialisation.
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "flarchitect"
flarch_pkg = types.ModuleType("flarchitect")
flarch_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("flarchitect", flarch_pkg)
database_pkg = types.ModuleType("flarchitect.database")
database_pkg.__path__ = [str(PACKAGE_ROOT / "database")]
sys.modules.setdefault("flarchitect.database", database_pkg)
core_pkg = types.ModuleType("flarchitect.core")
core_pkg.__path__ = [str(PACKAGE_ROOT / "core")]
sys.modules.setdefault("flarchitect.core", core_pkg)
db_utils_stub = types.ModuleType("flarchitect.database.utils")
for name in [
    "AGGREGATE_FUNCS",
    "create_aggregate_conditions",
    "generate_conditions_from_args",
    "get_all_columns_and_hybrids",
    "get_group_by_fields",
    "get_models_for_join",
    "get_primary_key_filters",
    "get_related_b_query",
    "get_select_fields",
    "get_table_and_column",
    "parse_column_table_and_operator",
    "validate_table_and_column",
]:
    setattr(db_utils_stub, name, lambda *args, **kwargs: None)
sys.modules.setdefault("flarchitect.database.utils", db_utils_stub)
exceptions_stub = types.ModuleType("flarchitect.exceptions")


class CustomHTTPException(Exception):
    pass


exceptions_stub.CustomHTTPException = CustomHTTPException
sys.modules.setdefault("flarchitect.exceptions", exceptions_stub)
config_stub = types.ModuleType("flarchitect.utils.config_helpers")


def get_config_or_model_meta(*args, **kwargs):
    return {}


config_stub.get_config_or_model_meta = get_config_or_model_meta
sys.modules.setdefault("flarchitect.utils.config_helpers", config_stub)
decorators_stub = types.ModuleType("flarchitect.utils.decorators")
decorators_stub.add_dict_to_query = lambda *args, **kwargs: None
decorators_stub.add_page_totals_and_urls = lambda *args, **kwargs: None
sys.modules.setdefault("flarchitect.utils.decorators", decorators_stub)
spec = importlib.util.spec_from_file_location(
    "flarchitect.database.operations", PACKAGE_ROOT / "database" / "operations.py"
)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
recursive_delete = ops.recursive_delete


class Base(DeclarativeBase):
    """Base class for declarative models."""


class Parent(Base):
    """Parent model with one-to-many relationship to children."""

    __tablename__ = "parent"

    id: Mapped[int] = mapped_column(primary_key=True)
    children: Mapped[list[Child]] = relationship(back_populates="parent")


class Child(Base):
    """Child model with many-to-one parent and one-to-many grandchildren."""

    __tablename__ = "child"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped[Parent] = relationship(back_populates="children")
    grandchildren: Mapped[list[Grandchild]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )


class Grandchild(Base):
    """Grandchild model linked back to the child."""

    __tablename__ = "grandchild"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("child.id"))
    child: Mapped[Child] = relationship(back_populates="grandchildren")


def _setup_data(session: Session) -> tuple[Parent, Child, Child, list[Grandchild]]:
    """Populate sample data for deletion tests."""

    parent = Parent()
    child1 = Child(parent=parent)
    child2 = Child(parent=parent)
    g1 = Grandchild(child=child1)
    g2 = Grandchild(child=child1)
    g3 = Grandchild(child=child2)
    session.add(parent)
    session.commit()
    return parent, child1, child2, [g1, g2, g3]


def test_recursive_delete_removes_descendants_and_preserves_parents() -> None:
    """Ensure recursive deletion removes descendants but keeps parents intact."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        parent, child1, child2, (g1, g2, g3) = _setup_data(session)

        objects_touched = recursive_delete(child1)
        session.commit()

        assert session.get(Child, child1.id) is None
        assert session.get(Grandchild, g1.id) is None
        assert session.get(Grandchild, g2.id) is None
        assert session.get(Parent, parent.id) is not None
        assert session.get(Child, child2.id) is not None
        assert session.get(Grandchild, g3.id) is not None

        expected = {
            ("Child", (child1.id,)),
            ("Grandchild", (g1.id,)),
            ("Grandchild", (g2.id,)),
        }
        assert set(objects_touched) == expected
        assert len(objects_touched) == len(expected)
