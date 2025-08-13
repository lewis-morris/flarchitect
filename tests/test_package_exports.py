import flarchitect.core as core
import flarchitect.database as database
import flarchitect.schemas as schemas
import flarchitect.specs as specs


def test_core_exports_and_docstring():
    assert core.__doc__
    assert core.Architect.__name__ == "Architect"
    assert "Architect" in core.__all__


def test_database_exports_and_docstring():
    assert database.__doc__
    assert database.CrudService.__name__ == "CrudService"
    assert "CrudService" in database.__all__


def test_schemas_exports_and_docstring():
    assert schemas.__doc__
    assert isinstance(schemas.AutoSchema, type)
    assert "AutoSchema" in schemas.__all__


def test_specs_exports_and_docstring():
    assert specs.__doc__
    assert specs.CustomSpec.__name__ == "CustomSpec"
    assert "CustomSpec" in specs.__all__
