"""Tests for `recursive_delete` utility."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from flarchitect.utils.config_helpers import get_config_or_model_meta

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def recursive_delete(monkeypatch: pytest.MonkeyPatch):
    """Provide the ``recursive_delete`` operation with minimal stubs.

    The function patches ``sys.modules`` so the operation can be imported
    without pulling in heavy dependencies. Modules are restored
    automatically after the test thanks to ``monkeypatch``.
    """

    flarchitect_pkg = types.ModuleType("flarchitect")
    core_pkg = types.ModuleType("flarchitect.core")
    database_pkg = types.ModuleType("flarchitect.database")
    monkeypatch.setitem(sys.modules, "flarchitect", flarchitect_pkg)
    monkeypatch.setitem(sys.modules, "flarchitect.core", core_pkg)
    monkeypatch.setitem(sys.modules, "flarchitect.database", database_pkg)

    utils_spec = importlib.util.spec_from_file_location("flarchitect.core.utils", REPO_ROOT / "flarchitect/core/utils.py")
    utils_module = importlib.util.module_from_spec(utils_spec)
    assert utils_spec.loader is not None
    utils_spec.loader.exec_module(utils_module)
    monkeypatch.setitem(sys.modules, "flarchitect.core.utils", utils_module)

    inspections_spec = importlib.util.spec_from_file_location(
        "flarchitect.database.inspections",
        REPO_ROOT / "flarchitect/database/inspections.py",
    )
    inspections_module = importlib.util.module_from_spec(inspections_spec)
    assert inspections_spec.loader is not None
    inspections_spec.loader.exec_module(inspections_module)
    monkeypatch.setitem(sys.modules, "flarchitect.database.inspections", inspections_module)

    utils_stub = types.ModuleType("flarchitect.database.utils")
    utils_stub.AGGREGATE_FUNCS = {}

    def _stub(*args: Any, **kwargs: Any) -> None:  # pragma: no cover - simple stub
        return None

    # Populate stub with the required callables
    utils_stub.create_aggregate_conditions = _stub
    utils_stub.generate_conditions_from_args = _stub
    utils_stub.get_all_columns_and_hybrids = _stub
    utils_stub.get_group_by_fields = _stub
    utils_stub.get_models_for_join = _stub
    utils_stub.get_primary_key_filters = _stub
    utils_stub.get_related_b_query = _stub
    utils_stub.get_select_fields = _stub
    utils_stub.get_table_and_column = _stub
    utils_stub.parse_column_table_and_operator = _stub
    utils_stub.validate_table_and_column = _stub
    monkeypatch.setitem(sys.modules, "flarchitect.database.utils", utils_stub)

    exceptions_stub = types.ModuleType("flarchitect.exceptions")

    class CustomHTTPException(Exception):
        """Lightweight stand-in for the real exception."""

    exceptions_stub.CustomHTTPException = CustomHTTPException
    monkeypatch.setitem(sys.modules, "flarchitect.exceptions", exceptions_stub)

    config_stub = types.ModuleType("flarchitect.utils.config_helpers")
    config_stub.get_config_or_model_meta = get_config_or_model_meta
    monkeypatch.setitem(sys.modules, "flarchitect.utils.config_helpers", config_stub)

    decorators_stub = types.ModuleType("flarchitect.utils.decorators")

    def add_dict_to_query(query: Any, *args: Any, **kwargs: Any) -> Any:
        return query

    def add_page_totals_and_urls(query: Any, *args: Any, **kwargs: Any) -> Any:
        return query

    decorators_stub.add_dict_to_query = add_dict_to_query
    decorators_stub.add_page_totals_and_urls = add_page_totals_and_urls
    monkeypatch.setitem(sys.modules, "flarchitect.utils.decorators", decorators_stub)

    operations_spec = importlib.util.spec_from_file_location(
        "flarchitect.database.operations",
        REPO_ROOT / "flarchitect/database/operations.py",
    )
    operations_module = importlib.util.module_from_spec(operations_spec)
    assert operations_spec.loader is not None
    operations_spec.loader.exec_module(operations_module)

    return operations_module.recursive_delete


class Base(DeclarativeBase):
    """Base declarative class."""


class Parent(Base):
    """Parent model owning children."""

    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    children: Mapped[list[Child]] = relationship("Child", back_populates="parent")


class Child(Base):
    """Child model with link to parent and grandchildren."""

    __tablename__ = "children"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id"))
    parent: Mapped[Parent] = relationship("Parent", back_populates="children")
    grandchildren: Mapped[list[Grandchild]] = relationship("Grandchild", back_populates="child")


class Grandchild(Base):
    """Grandchild model linked to child."""

    __tablename__ = "grandchildren"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"))
    child: Mapped[Child] = relationship("Child", back_populates="grandchildren")


def make_session() -> Session:
    """Create an in-memory database session."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_recursive_delete_removes_descendants_and_skips_parents(
    recursive_delete: Any,
) -> None:
    """Deleting a child removes descendants while preserving ancestors."""

    session: Session = make_session()

    parent: Parent = Parent(name="parent")
    child1: Child = Child(name="child1")
    child2: Child = Child(name="child2")
    g1: Grandchild = Grandchild(name="g1")
    g2: Grandchild = Grandchild(name="g2")
    g3: Grandchild = Grandchild(name="g3")

    child1.grandchildren.extend([g1, g2])
    child2.grandchildren.append(g3)
    parent.children.extend([child1, child2])

    session.add(parent)
    session.commit()

    objects_touched = recursive_delete(child1)
    session.commit()

    assert session.get(Parent, parent.id) is not None
    assert session.get(Child, child1.id) is None
    assert session.get(Grandchild, g1.id) is None
    assert session.get(Grandchild, g2.id) is None
    assert session.get(Child, child2.id) is not None
    assert session.get(Grandchild, g3.id) is not None

    expected = {
        ("Child", (child1.id,)),
        ("Grandchild", (g1.id,)),
        ("Grandchild", (g2.id,)),
    }
    assert set(objects_touched) == expected
    assert len(objects_touched) == len(expected)

    session.close()
