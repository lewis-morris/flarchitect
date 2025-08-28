"""Helper utilities for SQLAlchemy models.

Provides functions for primary-key retrieval, URL formatting for Flask routes,
and foreign-key inspection between related models.
"""

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_TO_FLASK_CONVERTER = {
    int: "int",
    str: "string",
    bytes: "path",  # Flask uses 'path' for URLs that can contain slashes
    "UUID": "uuid",  # UUID type support
    float: "float",
}


def get_pk(model: type[DeclarativeBase]):
    """
    Utility function to get the primary key column from a SQLAlchemy model.
    """
    primary_keys = inspect(model).primary_key
    if len(primary_keys) != 1:
        raise ValueError("Model must have a single primary key.")
    return primary_keys[0]


def get_url_pk(model: type[DeclarativeBase]) -> str:
    """
    Get the primary key for the model in Flask URL format.

    Args:
        model (Type[DeclarativeBase]): The model to get the primary key for.

    Returns:
        str: The Flask primary key format for the model.
    """
    primary_key = get_pk(model)
    pk_type = primary_key.type.python_type

    # Use the type from the SQLALCHEMY_TO_FLASK_CONVERTER mapping if it exists
    flask_converter = SQLALCHEMY_TO_FLASK_CONVERTER.get(pk_type, "string")  # Default to 'string' if unknown

    return f"<{flask_converter}:{primary_key.key}>"


def get_foreign_key_to_parent(child_model: type[DeclarativeBase], parent_model: type[DeclarativeBase]) -> tuple[str, str] | None:
    """
    Get the foreign key columns in the association table that reference the child and parent models.

    Args:
        child_model: The child SQLAlchemy model class.
        parent_model: The parent SQLAlchemy model class.

    Returns:
        Optional[Tuple[str, str]]: A tuple containing the foreign key column names from the association table
                                   to the child and parent models, or None if not found.
    """
    child_mapper = inspect(child_model)
    parent_mapper = inspect(parent_model)

    # Initialise variables
    association_table = None
    child_fk_column = None
    parent_fk_column = None

    # Find the relationship involving the secondary table
    for rel in child_mapper.relationships:
        if rel.secondary is not None and rel.mapper.class_ == parent_model:
            association_table = rel.secondary
            break
    else:
        for rel in parent_mapper.relationships:
            if rel.secondary is not None and rel.mapper.class_ == child_model:
                association_table = rel.secondary
                break
        else:
            # No secondary relationship found
            return None

    # Extract foreign key columns from the association table
    for column in association_table.columns:
        for fk in column.foreign_keys:
            if fk.column.table == child_mapper.local_table:
                child_fk_column = column.name
            elif fk.column.table == parent_mapper.local_table:
                parent_fk_column = column.name

    if child_fk_column and parent_fk_column:
        return (child_fk_column, parent_fk_column)
    else:
        return None


def get_primary_key_info(model: type[DeclarativeBase]) -> tuple[str, str] | None:
    """
    Get the primary key column name and its Flask converter type for the given model.

    Args:
        model: The SQLAlchemy model class.

    Returns:
        Optional[Tuple[str, str]]: A tuple containing the primary key column name and its Flask converter type,
                                   or None if no primary key is found.
    """
    mapper = inspect(model)
    primary_keys = mapper.primary_key

    if not primary_keys:
        return None  # No primary key found

    # Assuming there is only one primary key column
    pk_column = primary_keys[0]
    pk_column_name = pk_column.name

    # Map SQLAlchemy column type to Flask converter type
    type_mapping = {
        "Integer": "int",
        "String": "string",
        "UUID": "uuid",
        "Date": "string",  # Flask does not have a Date converter
        "DateTime": "string",  # Handle DateTime as string or implement custom converter
        "Float": "float",
        "Boolean": "int",  # Represent booleans as 0 or 1
        # Add more mappings as needed
    }

    column_type_name = type(pk_column.type).__name__
    flask_converter = type_mapping.get(column_type_name, "string")

    return (pk_column_name, flask_converter)
