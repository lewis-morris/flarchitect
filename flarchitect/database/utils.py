from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, Date, Float, Integer, func, inspect, or_
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    RelationshipProperty,
    class_mapper,
)

from flarchitect.exceptions import CustomHTTPException
from flarchitect.logging import logger
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import (
    convert_camel_to_snake,
    convert_case,
    convert_kebab_to_snake,
)

OPERATORS: dict[str, Callable[[Any, Any], Any]] = {
    "lt": lambda f, a: f < a,
    "le": lambda f, a: f <= a,
    "gt": lambda f, a: f > a,
    "eq": lambda f, a: f == a,
    "neq": lambda f, a: f != a,
    "ge": lambda f, a: f >= a,
    "ne": lambda f, a: f != a,
    "in": lambda f, a: f.in_(a),
    "nin": lambda f, a: ~f.in_(a),
    "like": lambda f, a: f.like(a),
    "ilike": lambda f, a: f.ilike(a),  # case-insensitive LIKE operator
}
AGGREGATE_FUNCS = {
    "sum": func.sum,
    "count": func.count,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
}
OTHER_FUNCTIONS = ["groupby", "fields", "join", "orderby"]


def fetch_related_classes_and_attributes(model: object) -> list[tuple[str, str]]:
    """Collect relationship attributes and their related class names.

    Args:
        model (object): SQLAlchemy declarative model whose relationships are
            inspected.

    Returns:
        list[tuple[str, str]]: Pairs of the relationship attribute name on
        ``model`` and the related model's class name. Returns an empty list if
        ``model`` defines no relationships.
    """

    return [(relation.key, relation.mapper.class_.__name__) for relation in class_mapper(model).relationships]


def get_all_columns_and_hybrids(model: DeclarativeBase, join_models: dict[str, DeclarativeBase]) -> tuple[dict[str, dict[str, hybrid_property | InstrumentedAttribute]], list[DeclarativeBase]]:
    """Gather columns and hybrid properties for the base and join models.

    Args:
        model (DeclarativeBase): Base SQLAlchemy model.
        join_models (dict[str, DeclarativeBase]): Mapping of join model aliases
            to SQLAlchemy model classes. May be empty.

    Returns:
        tuple[dict[str, dict[str, hybrid_property | InstrumentedAttribute]], list[DeclarativeBase]]:
        A mapping of table names to their public columns/hybrid properties and a
        list of all models inspected.

    Notes:
        Attributes beginning with ``_`` are ignored when
        ``API_IGNORE_UNDERSCORE_ATTRIBUTES`` is set (default).
    """
    ignore_underscore = get_config_or_model_meta(key="API_IGNORE_UNDERSCORE_ATTRIBUTES", model=model, default=True)
    schema_case = get_config_or_model_meta(key="API_SCHEMA_CASE", model=model, default="camel")

    all_columns = {}
    all_models = [model] + list(join_models.values())

    for mdl in all_models:
        table_name = convert_case(mdl.__name__, schema_case)
        all_columns[table_name] = {
            attr: column for attr, column in mdl.__dict__.items() if isinstance(column, hybrid_property | InstrumentedAttribute) and (not ignore_underscore or not attr.startswith("_"))
        }

    return all_columns, all_models


def create_pagination_defaults() -> tuple[dict[str, int], dict[str, int]]:
    """Assemble default and maximum pagination limits and return both dictionaries.

    Returns:
        tuple[dict[str, int], dict[str, int]]: Default pagination values and
        their maximum allowable limits.
    """

    PAGINATION_DEFAULTS = {
        "page": 1,
        "limit": get_config_or_model_meta("API_PAGINATION_SIZE_DEFAULT", default=20),
    }
    PAGINATION_MAX = {
        "limit": get_config_or_model_meta("API_PAGINATION_SIZE_MAX", default=100),
    }

    return PAGINATION_DEFAULTS, PAGINATION_MAX


def extract_pagination_params(args_dict: dict[str, str]) -> tuple[int, int]:
    """Parse pagination information from request arguments.

    Args:
        args_dict (dict[str, str]): Query string arguments from the request.

    Returns:
        tuple[int, int]: The requested page number and page size.
    Raises:
        CustomHTTPException: If the requested ``limit`` exceeds the configured
        maximum.

    Notes:
        Defaults are used when ``page`` or ``limit`` are missing.
    """

    PAGINATION_DEFAULTS, PAGINATION_MAX = create_pagination_defaults()

    page = int(args_dict.get("page", PAGINATION_DEFAULTS["page"]))
    limit = int(args_dict.get("limit", PAGINATION_DEFAULTS["limit"]))

    if limit > PAGINATION_MAX["limit"]:
        raise CustomHTTPException(400, f"Limit exceeds maximum value of {PAGINATION_MAX['limit']}")

    return page, limit


def get_group_by_fields(
    args_dict: dict[str, str],
    all_columns: dict[str, dict[str, hybrid_property | InstrumentedAttribute]],
    base_model: DeclarativeBase,
) -> list[Callable]:
    """Derive ``GROUP BY`` SQLAlchemy columns from query parameters.

    Args:

        args_dict (dict[str, str]): Query string arguments containing an
            optional ``groupby`` entry.
        all_columns (dict[str, dict[str, hybrid_property | InstrumentedAttribute]]):
            Mapping of table names to their accessible columns/hybrid
            properties.
        base_model (DeclarativeBase): Base model used for resolving table
            names when not explicitly provided.

    Returns:
        list[Callable]: Columns to use in the ``GROUP BY`` clause. Returns an
        empty list when ``groupby`` is absent.
    """

    group_by_fields: list[Callable] = []
    if "groupby" in args_dict:
        fields = args_dict.get("groupby").split(",")
        for field in fields:
            table_name, column_name = get_table_and_column(field, base_model)
            model_column, _ = validate_table_and_column(table_name, column_name, all_columns)
            group_by_fields.append(model_column)

    return group_by_fields


def get_models_for_join(args_dict: dict[str, str], get_model_func: Callable[[str], DeclarativeBase]) -> dict[str, DeclarativeBase]:
    """Build a mapping of models to join from the ``join`` query parameter.

    Args:
        args_dict: Mapping of request arguments.
        get_model_func: Callback used to resolve a model name to a class.

    Returns:
        dict[str, DeclarativeBase]: Requested join names mapped to model classes.
        An empty dictionary is returned when no joins are requested.

    Raises:
        CustomHTTPException: If a requested join model cannot be resolved.

    """

    models: dict[str, DeclarativeBase] = {}
    join_value = args_dict.get("join") or args_dict.get("join_models")
    if join_value:
        for join in join_value.split(","):
            model = get_model_func(join)
            if not model:
                raise CustomHTTPException(400, f"Invalid join model: {join}")
            models[join] = model

    return models


def get_table_column(key: str, all_columns: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    """Resolve a request key to its table name, column, and operator.

    Args:
        key: Request argument key containing a column name and optional operator
            (e.g., ``"id__eq"`` or ``"users.id__eq"``).
        all_columns: Mapping of table names to their column attributes.

    Returns:
        tuple[str, str, str]: The table name, column name, and operator. The
        operator is an empty string if none is specified.

    Raises:
        CustomHTTPException: If ``key`` does not correspond to a known column.
    """
    keys_split = key.split("__")
    column_name = keys_split[0]
    operator = keys_split[1] if len(keys_split) > 1 else ""

    for table_name, columns in all_columns.items():
        if "." in column_name:
            table_name, column_name = column_name.split(".")

        if column_name in columns:
            return table_name, column_name, operator

    raise CustomHTTPException(400, f"Invalid column name: {column_name}")


def get_select_fields(
    args_dict: dict[str, str],
    base_model: DeclarativeBase,
    all_columns: dict[str, dict[str, Column]],
) -> list[Callable]:
    """Determine explicit column selection from query parameters.

    Args:
        args_dict (dict[str, str]): Query string arguments which may contain a
            comma-separated ``fields`` entry.
        base_model (DeclarativeBase): Base model used to infer table names when
            ``fields`` entries omit them.
        all_columns (dict[str, dict[str, Column]]): Mapping of table names to
            their available SQLAlchemy columns.

    Returns:
        list[Callable]: SQLAlchemy columns to include in the ``SELECT`` clause.
        Returns an empty list when ``fields`` is absent.
    """
    select_fields = []
    if "fields" in args_dict:
        fields = args_dict.get("fields").split(",")
        for field in fields:
            table_name, column_name = get_table_and_column(field, base_model)
            model_column, _ = validate_table_and_column(table_name, column_name, all_columns)
            select_fields.append(model_column)

    return select_fields


def parse_or_condition_keys_and_values(key: str, val: str) -> tuple[list[str], list[str]]:
    """
    Get the 'or' values and keys.

    Args:
        key (str): The key from request arguments, e.g. "or[id__eq".
        val (str): The value from request arguments, e.g. "2, id__eq=3]".

    Returns:
        Tuple[List[str], List[str]]: Lists of keys and corresponding values.
    """
    # Extract the initial key, remove 'or[' and strip any whitespace
    keys = []
    values = []
    for item in (key + "=" + val)[3:-1].split(","):
        key_part, value_part = item.split("=")
        keys.append(key_part.strip())
        values.append(value_part.strip())

    return keys, values


def generate_conditions_from_args(
    args_dict: dict[str, str],
    base_model: DeclarativeBase,
    all_columns: dict[str, dict[str, Column]],
    all_models: list[DeclarativeBase],
    join_models: dict[str, DeclarativeBase],
) -> list[Callable]:
    """
    Create filter conditions based on request arguments and model's columns.

    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.
        base_model (DeclarativeBase): The base SQLAlchemy model.
        all_columns (Dict[str, Dict[str, Any]]): Nested dictionary of table names and their columns.
        all_models (List[DeclarativeBase]): List of all models.
        join_models (Dict[str, DeclarativeBase]): Dictionary of join models.

    Returns:
        List[Callable]: List of conditions to apply in the query.

    Raises:
        CustomHTTPException: If an invalid or ambiguous column name is provided.
    """
    conditions = []
    or_conditions = []

    PAGINATION_DEFAULTS, PAGINATION_MAX = create_pagination_defaults()

    for key, _value in args_dict.items():
        if any(op in key for op in OPERATORS) and not any(func in key for func in [*PAGINATION_DEFAULTS, *OTHER_FUNCTIONS]):
            if key.startswith("or["):
                or_keys, or_vals = parse_or_condition_keys_and_values(key, _value)
                or_conditions.extend(
                    create_condition(
                        *get_table_column(or_key, all_columns),
                        or_val,
                        all_columns,
                        base_model,
                    )
                    for or_key, or_val in zip(or_keys, or_vals, strict=False)
                )
                continue

            table, column, operator = get_table_column(key, all_columns)
            if operator:
                condition = create_condition(table, column, operator, _value, all_columns, base_model)
                if condition is not None:
                    conditions.append(condition)

    if or_conditions:
        conditions.append(or_(*or_conditions))

    return conditions


def parse_key_and_label(key):
    """
        Get the key and label from the key

    Args:
        key (str): The key from request arguments, e.g. "id__eq".

    Returns:
        A tuple of key and label

    """

    key_list = key.split("|")
    if len(key_list) == 1:
        return key, None
    elif len(key_list) >= 2:
        # was getting an error where the label and operator were combined, now we split them and recombine with the key
        key, pre_label = key_list[0], key_list[1]
        if "__" in pre_label:
            label, operator = pre_label.split("__")
            key = f"{key}__{operator}"
        else:
            label = pre_label

        return key, label


def create_aggregate_conditions(
    args_dict: dict[str, str],
) -> dict[str, str | None] | None:
    """
    Creates aggregate conditions based on request arguments and the model's columns.

    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.

    Returns:
        Optional[Dict[str, Optional[str]]]: A dictionary of aggregate conditions.
    """
    aggregate_conditions = {}

    for key, _value in args_dict.items():
        for func_name in AGGREGATE_FUNCS:
            if f"__{func_name}" in key:
                key, label = parse_key_and_label(key)
                aggregate_conditions[key] = label

    return aggregate_conditions


def get_table_and_column(value: str, main_model: DeclarativeBase) -> tuple[str, str]:
    """
    Get the table and column name from the value.

    Args:
        value (str): The value from request arguments, e.g. "id__eq".
        main_model (DeclarativeBase): The base SQLAlchemy model.

    Returns:
        Tuple[str, str]: A tuple of table name and column name.
    """
    if "." in value:
        return value.split(".", 1)

    from flarchitect.utils.general import get_config_or_model_meta

    schema_case = get_config_or_model_meta("API_SCHEMA_CASE", model=main_model, default="camel")
    table_name = convert_case(main_model.__name__, schema_case)
    return table_name, value


def parse_column_table_and_operator(key: str, main_model: DeclarativeBase) -> tuple[str, str, str]:
    """
    Get the column and table name from the key.

    Args:
        key (str): The key from request arguments, e.g. "id__eq".
        main_model (DeclarativeBase): The base SQLAlchemy model.

    Returns:
        Tuple[str, str, str]: A tuple of column name, table name, and operator.
    """
    column_name, operator_str = key.split("__")
    table_name, column_name = get_table_and_column(column_name, main_model)
    return column_name, table_name, operator_str


def validate_table_and_column(table_name: str, column_name: str, all_columns: dict[str, dict[str, Column]]) -> tuple[Column, str]:
    """
    Get the column from the column dictionary.

    Args:
        table_name (str): The table name.
        column_name (str): The column name.
        all_columns (Dict[str, Dict[str, Column]]): Dictionary of columns in the base model.

    Returns:
        Tuple[Column, str]: The column and its name.
    """
    from flarchitect.utils.general import get_config_or_model_meta

    # Ensure default matches supported values in convert_case
    field_case = get_config_or_model_meta("API_FIELD_CASE", default="snake")
    column_name = convert_case(column_name, field_case)

    all_models_columns = all_columns.get(table_name)
    if not all_models_columns:
        # Fallback to case-insensitive lookup to avoid issues with mixed casing
        all_models_columns = all_columns.get(table_name.lower())
    if not all_models_columns:
        raise CustomHTTPException(400, f"Invalid table name: {table_name}")

    model_column = all_models_columns.get(column_name)
    if not model_column:
        raise CustomHTTPException(400, f"Invalid column name: {column_name}")

    return model_column, column_name


def create_condition(
    table_name: str,
    column_name: str,
    operator: str,
    value: str,
    all_columns: dict[str, dict[str, Column]],
    model: DeclarativeBase,
) -> Callable | None:
    """
    Converts a key-value pair from request arguments to a condition.

    Args:
        table_name (str): The table name.
        column_name (str): The column name.
        operator (str): The operator.
        value (str): The value associated with the key.
        all_columns (Dict[str, Column]): Dictionary of columns in the base model.
        model (DeclarativeBase): The model instance.

    Returns:
        Optional[Callable]: A condition function or None if invalid operator.
    """
    model_column, _ = validate_table_and_column(table_name, column_name, all_columns)

    column_type = get_type_hint_from_hybrid(model_column) if isinstance(model_column, hybrid_property) else model_column.type

    if "in" in operator:
        value = value.strip("()").split(",")

    if "like" in operator:
        value = f"%{value}%"

    with suppress(ValueError):
        value = convert_value_to_type(value, column_type)

    operator_func = OPERATORS.get(operator)
    if operator_func is None:
        return None

    try:
        if is_hybrid_property(model_column):
            return operator_func(getattr(model, column_name), value)
        return operator_func(model_column, value)
    except (Exception, StatementError):
        return None


def is_hybrid_property(prop: Any) -> bool:
    """
    Check if a property of a model is a hybrid_property.

    Args:
        prop (Any): The property to check.

    Returns:
        bool: True if the property is a hybrid_property, False otherwise.
    """
    return isinstance(prop, hybrid_property)


def get_type_hint_from_hybrid(func: Callable) -> type | None:
    """
    Converts a function (hybrid_property) into its returning type.

    Args:
        func (Callable): Function to convert to its output type.

    Returns:
        Optional[Type]: The type hint of the hybrid property.
    """
    return func.__annotations__.get("return")


def convert_value_to_type(value: str | list[str], column_type: Any, is_hybrid: bool = False) -> Any:
    """
    Convert the given string value or list of string values to its appropriate type based on the provided column_type.

    Args:
        value (Union[str, List[str]]): The value(s) to convert.
        column_type (Any): The type to convert the value(s) to.
        is_hybrid (bool): Whether the conversion is for a hybrid property.

    Returns:
        Any: The converted value(s).
    """

    def convert_to_boolean(val: str) -> bool:
        val = val.lower()
        if val in ["true", "1", "yes", "y"]:
            return True
        if val in ["false", "0", "no", "n"]:
            return False
        raise CustomHTTPException(400, f"Invalid boolean value: {val}")

    def convert_single_value(val: str, _type: Any) -> Any:
        if isinstance(_type, Integer):
            return int(val)
        if isinstance(_type, Float):
            return float(val)
        if isinstance(_type, Date):
            return datetime.strptime(val, "%Y-%m-%d").date()
        if isinstance(_type, Boolean):
            return convert_to_boolean(val)
        return val

    if isinstance(value, list | set | tuple):
        return [convert_single_value(str(v), column_type) for v in value]
    return convert_single_value(value, column_type)


def find_matching_relations(model1: Callable, model2: Callable) -> list[tuple[str, str]]:
    """Find matching relation fields between two SQLAlchemy models.

    Args:
        model1 (Callable): The first SQLAlchemy model class.
        model2 (Callable): The second SQLAlchemy model class.

    Returns:
        List[Tuple[str, str]]: A list of matching relation field names.
    """
    relationships1 = class_mapper(model1).relationships
    relationships2 = class_mapper(model2).relationships

    matching_relations = [
        (rel_name1, rel_name2)
        for rel_name1, rel_prop1 in relationships1.items()
        if rel_prop1.mapper.class_ == model2
        for rel_name2, rel_prop2 in relationships2.items()
        if rel_prop2.mapper.class_ == model1
    ]

    return matching_relations


def _get_relation_use_list_and_type(
    relationship_property: RelationshipProperty,
) -> tuple[bool, str]:
    """Get the use_list property and relationship type for a given relationship_property.

    Args:
        relationship_property (RelationshipProperty): The relationship property.

    Returns:
        Tuple[bool, str]: A tuple containing the use_list property and relationship type.
    """
    if hasattr(relationship_property, "property"):
        relationship_property = relationship_property.property

    direction = relationship_property.direction.name
    return not relationship_property.uselist, direction


def table_namer(model: type[DeclarativeBase] | None = None) -> str:
    """
    Get the table name from the model name by converting camelCase, PascalCase, or kebab-case to snake_case.

    Args:
        model (Optional[Type[DeclarativeBase]]): The model to get the table name for.

    Returns:
        str: The table name in snake_case.
    """
    if model is None:
        return ""

    snake_case_name = convert_kebab_to_snake(model.__name__)
    return convert_camel_to_snake(snake_case_name)


def get_models_relationships(model: type[DeclarativeBase]) -> list[dict[str, Any]]:
    """
    Get the relationships of the model, including the join key and columns.

    Args:
        model (Type[DeclarativeBase]): The model to check for relations.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing relationship details.
    """
    if not model:
        return []

    relationships = []
    mapper = inspect(model)

    for rel in mapper.relationships:
        relationship_info = extract_relationship_info(rel)
        if relationship_info:
            relationships.append(relationship_info)
            logger.debug(
                4,
                f"Added |{model.__name__}| relationship with |{relationship_info['model'].__name__}| via columns {relationship_info['left_column']} to {relationship_info['right_column']}.",
            )
    return relationships


def extract_relationship_info(rel: RelationshipProperty) -> dict[str, Any]:
    """
    Extract detailed information from a relationship property.

    Args:
        rel (RelationshipProperty): The relationship property to extract information from.

    Returns:
        Dict[str, Any]: A dictionary with relationship details.
    """
    try:
        # Use local_remote_pairs to get pairs of local and remote columns
        left_columns = [local.name for local, _ in rel.local_remote_pairs]
        right_columns = [remote.name for _, remote in rel.local_remote_pairs]

        if len(left_columns) > 0:
            left_columns = left_columns[0]
        if len(right_columns) > 0:
            right_columns = right_columns[0]

        return {
            "relationship": rel.key,
            "join_type": str(rel.direction),
            "left_column": left_columns,
            "right_column": right_columns,
            "model": rel.mapper.class_,
            "parent": rel.parent.class_,
        }
    except Exception as e:
        logger.error(f"Error extracting relationship info: {e}")
        return {}


def get_primary_keys(model: type[DeclarativeBase]) -> Column:
    """
    Get the primary key column for the model.

    Args:
        model (Type[DeclarativeBase]): The model to get the primary key from.

    Returns:
        Column: The primary key column.
    """
    return next(iter(inspect(model).primary_key))


def get_primary_key_filters(base_model, lookup_val):
    """Generate a dictionary for filtering based on the primary key(s).

    Args:
        base_model (DeclarativeBase): The SQLAlchemy model class.
        lookup_val (Union[int, str]): The value to filter by primary key.

    Returns:
        Dict[str, Any]: A dictionary with primary key column(s) and the provided lookup value.
    """
    mapper = inspect(base_model)
    pks = mapper.primary_key

    # If there's only one primary key column, return a simple dictionary
    if len(pks) == 1:
        return {pks[0].name: lookup_val}

    # If there are multiple primary key columns, split the lookup_val and map accordingly
    if isinstance(lookup_val, tuple | list):
        return {pk.name: val for pk, val in zip(pks, lookup_val, strict=False)}

    raise ValueError(f"Multiple primary keys found in {base_model.__name__}, but lookup_val is not a tuple or list.")


def list_model_columns(model: type[DeclarativeBase]) -> list[str]:
    """
    Get the list of columns for the model, including hybrid properties.

    Args:
        model (Type[DeclarativeBase]): The SQLAlchemy model class.

    Returns:
        List[str]: List of column names.
    """
    all_columns, _ = get_all_columns_and_hybrids(model, join_models={})
    return list(all_columns.values())[0].keys()


def _extract_model_attributes(model: type[DeclarativeBase]) -> tuple[set, set]:
    """
    Extracts column and property keys from the model.

    Args:
        model (Type[DeclarativeBase]): The SQLAlchemy model class.

    Returns:
        Tuple[set, set]: A tuple containing sets of column keys and property keys.
    """
    inspector = inspect(model)
    model_keys = {column.key for column in inspector.columns}
    model_properties = set(inspector.attrs.keys()).difference(model_keys)
    return model_keys, model_properties


def get_related_b_query(model_a, model_b, a_pk_value, session):
    """
    Return a SQLAlchemy query that retrieves all instances of model_b related to model_a.

    Args:
        model_a: The parent SQLAlchemy model class.
        model_b: The related SQLAlchemy model class.
        a_pk_value: The primary key value of model_a.
        session: The SQLAlchemy session instance.

    Returns:
        A SQLAlchemy query object that retrieves all related model_b instances.

    Raises:
        Exception: If no relationship is found between model_a and model_b.
    """
    # Get the mappers for both models
    mapper_a = inspect(model_a)
    mapper_b = inspect(model_b)

    # Get the primary key column and attribute of model_a
    pk_column_a = mapper_a.primary_key[0]
    pk_attr_name_a = pk_column_a.name
    pk_attr_a = getattr(model_a, pk_attr_name_a)

    # Try to find the relationship on model_a
    relationship_property = None
    relationship_name = None
    source_model = None
    for rel in mapper_a.relationships:
        if rel.mapper.class_ == model_b or rel.mapper.class_.__name__ == model_b.__name__:
            relationship_property = rel
            relationship_name = rel.key
            source_model = model_a
            break

    # If not found on model_a, check model_b
    if not relationship_property:
        for rel in mapper_b.relationships:
            if rel.mapper.class_ == model_a or rel.mapper.class_.__name__ == model_a.__name__:
                relationship_property = rel
                relationship_name = rel.key
                source_model = model_b
                break

    if not relationship_property:
        raise Exception(f"No relationship found between {model_a.__name__} and {model_b.__name__}")

    # Build the query
    if source_model == model_a:
        # Relationship is from model_a to model_b
        relationship_attr = getattr(model_a, relationship_name)
        query = session.query(model_b).join(relationship_attr).filter(pk_attr_a == a_pk_value)
    else:
        # Relationship is from model_b to model_a
        relationship_attr = getattr(model_b, relationship_name)
        query = session.query(model_b).join(relationship_attr).filter(pk_attr_a == a_pk_value)

    return query
