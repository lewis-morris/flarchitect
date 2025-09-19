from collections.abc import Callable
from typing import Any

from flask import request
from sqlalchemy import and_, inspect
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Query, Session, object_session
from sqlalchemy.orm.exc import UnmappedInstanceError

from flarchitect.core.utils import get_primary_key_info
from flarchitect.database.inspections import get_model_columns, get_model_relationships

# Import utility helpers with a graceful fallback for optional helpers such as
# ``_eager_options_for`` which may not be present when tests monkeypatch the
# ``flarchitect.database.utils`` module. The recursive delete fixture replaces
# the module with a lightweight stub, so we resolve attributes dynamically.
from flarchitect.database import utils as _db_utils


AGGREGATE_FUNCS = _db_utils.AGGREGATE_FUNCS
create_aggregate_conditions = _db_utils.create_aggregate_conditions
generate_conditions_from_args = _db_utils.generate_conditions_from_args
get_all_columns_and_hybrids = _db_utils.get_all_columns_and_hybrids
get_group_by_fields = _db_utils.get_group_by_fields
get_models_for_join = _db_utils.get_models_for_join
get_primary_key_filters = _db_utils.get_primary_key_filters
get_related_b_query = _db_utils.get_related_b_query
get_select_fields = _db_utils.get_select_fields
get_table_and_column = _db_utils.get_table_and_column
parse_column_table_and_operator = _db_utils.parse_column_table_and_operator
validate_table_and_column = _db_utils.validate_table_and_column
normalise_join_token = getattr(
    _db_utils,
    "normalise_join_token",
    lambda token: (token or "").strip().lower().replace("-", "_"),
)


def _fallback_table_namer(model: DeclarativeBase | None = None) -> str:
    """Gracefully derive a table name when the DB utils module is stubbed."""

    if model is None:
        return ""

    table_name = getattr(model, "__tablename__", None)
    if isinstance(table_name, str) and table_name:
        return table_name

    return getattr(model, "__name__", "").strip().lower()


table_namer = getattr(_db_utils, "table_namer", _fallback_table_namer)
_eager_options_for = getattr(_db_utils, "_eager_options_for", lambda *args, **kwargs: [])
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.decorators import add_dict_to_query, add_page_totals_and_urls
from flarchitect.utils.core_utils import convert_case

__all__ = [
    "paginate_query",
    "apply_sorting_to_query",
    "CrudService",
    "get_model_columns",
    "get_model_relationships",
]


def paginate_query(sql_query: Query, page: int = 0, items_per_page: int | None = None) -> tuple[Query, int]:
    """Applies pagination to a query.

    Args:
        sql_query (Query): SQLAlchemy query to paginate.
        page (int): Page number.
        items_per_page (int): Number of items per page.

    Returns:
        tuple[Query, int]:
            A tuple containing the paginated query and the default pagination size.
    """

    def validate_pagination_params(page: int, items_per_page: int) -> None:
        """Validate pagination parameters.

        Args:
            page (int): Page number.
            items_per_page (int): Number of items per page.

        Raises:
            CustomHTTPException: If the parameters are not valid integers.
        """
        if not str(page).isnumeric():
            raise CustomHTTPException(400, "Page number must be an integer.")
        if not str(items_per_page).isnumeric():
            raise CustomHTTPException(400, "Items per page must be an integer.")

    default_pagination_size = get_config_or_model_meta("API_PAGINATION_SIZE_DEFAULT", default=20)

    if items_per_page is None:
        items_per_page = default_pagination_size

    validate_pagination_params(page, items_per_page)

    return (
        sql_query.paginate(page=int(page), per_page=int(items_per_page), error_out=False),
        default_pagination_size,
    )


def apply_sorting_to_query(args_dict: dict[str, str | int], query: Query, base_model: Callable) -> Query:
    """Applies order_by conditions to a query.

    Args:
        args_dict (Dict[str, Union[str, int]]): Dictionary containing order_by conditions.
        query (Query): SQLAlchemy query to apply order_by to.
        base_model (Callable): Base model for the query.

    Returns:
        Query: Query with applied order_by conditions.
    """
    order_by = args_dict.get("order_by") or args_dict.get("orderby")
    if not order_by:
        return query

    if isinstance(order_by, str):
        order_by = order_by.split(",")

    sorts = []

    for order_key in order_by:
        descending = order_key.startswith("-")
        order_key = order_key.lstrip("-")
        table_name, column_name = get_table_and_column(order_key, base_model)
        column_attr = getattr(base_model, column_name, None)

        if column_attr:
            sorts.append(column_attr.desc() if descending else column_attr)

    if sorts:
        query = query.order_by(*sorts)

    return query


class CrudService:
    def __init__(self, model: Callable, session: Session):
        """Initialises the CrudService instance.

        Args:
            model (Callable): SQLAlchemy model class for CRUD operations.
            session (Session): SQLAlchemy session.
        """
        self.model = model
        self.session = session

    def _process_nested_relationships(self, model: DeclarativeBase, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively build related model instances from nested dictionaries.

        Args:
            model: SQLAlchemy model to inspect.
            data: Payload containing potential nested relationship data.

        Returns:
            dict[str, Any]: Payload with nested dictionaries replaced by model instances.
        """
        for relationship in inspect(model).relationships:
            key = relationship.key
            if key not in data or data[key] is None:
                continue

            related_model = relationship.mapper.class_
            value = data[key]

            if relationship.uselist and isinstance(value, list):
                data[key] = [related_model(**self._process_nested_relationships(related_model, item)) for item in value]
            elif not relationship.uselist and isinstance(value, dict):
                data[key] = related_model(**self._process_nested_relationships(related_model, value))

            for col in relationship.local_columns:
                data.pop(col.name, None)

        return data

    def fetch_related_model_by_name(self, field_name: str) -> Callable:
        """Gets a related model by field name.

        Args:
            field_name (str): Name of the field representing the relationship.

        Returns:
            Callable: Related model class.

        Raises:
            CustomHTTPException: If the field does not represent a relationship.
        """
        relationships = inspect(self.model).relationships
        # Try direct relationship key match first
        related = relationships.get(field_name)
        if related is not None:
            return related.mapper.class_

        # Be flexible: allow endpoint-style names or case variations
        target = (field_name or "").strip().lower()
        from flarchitect.specs.utils import endpoint_namer
        from flarchitect.utils.config_helpers import get_config_or_model_meta
        from flarchitect.utils.core_utils import convert_case

        endpoint_case = get_config_or_model_meta("API_ENDPOINT_CASE", default="kebab") or "kebab"

        for rel in relationships.values():
            model_cls = rel.mapper.class_
            # Endpoint-style plural name (e.g., "authors")
            endpoint_name = endpoint_namer(model_cls).lower()
            # Relationship key in endpoint case (often singular)
            rel_key_endpoint_case = convert_case(rel.key, endpoint_case).lower()
            # Raw relationship key
            rel_key_raw = rel.key.lower()

            if target in {endpoint_name, rel_key_endpoint_case, rel_key_raw}:
                return model_cls

        raise CustomHTTPException(
            401,
            f"Field {field_name} does not represent a relationship in model {self.model.__name__}",
        )

    def filter_query_from_args(self, args_dict: dict[str, Any], query=None) -> Query:
        """Build a query applying joins, filters, grouping and aggregation.

        Args:
            args_dict: Dictionary containing query parameters.
            query: Optional existing SQLAlchemy query to build upon.

        Returns:
            Query with all requested transformations applied.
        """

        # Flatten values to simple scalars for general processing while preserving
        # the full argument structure for join parsing.
        def _flatten_values(d: dict[str, Any]) -> dict[str, Any]:
            return {k: (v[0] if isinstance(v, (list, tuple)) else v) for k, v in d.items()}

        allow_join = get_config_or_model_meta("API_ALLOW_JOIN", model=self.model, default=False)
        join_models = get_models_for_join(args_dict, self.fetch_related_model_by_name) if allow_join else {}
        # Use flattened args for all non-join processing
        flat_args = _flatten_values(args_dict)

        all_columns, all_models = get_all_columns_and_hybrids(self.model, join_models)

        schema_case = get_config_or_model_meta("API_SCHEMA_CASE", model=self.model, default="camel")

        alias_to_model: dict[str, type[DeclarativeBase]] = {}

        def _register_alias(model_cls: type[DeclarativeBase], *names: str) -> None:
            for name in names:
                if not name:
                    continue
                alias_to_model.setdefault(name, model_cls)
                normalised = normalise_join_token(name)
                if normalised:
                    alias_to_model.setdefault(normalised, model_cls)

        base_alias = convert_case(self.model.__name__, schema_case)
        _register_alias(self.model, base_alias, table_namer(self.model))

        for token, mdl in join_models.items():
            canonical = convert_case(mdl.__name__, schema_case)
            _register_alias(mdl, token, canonical, table_namer(mdl))

        conditions = [condition for condition in generate_conditions_from_args(flat_args, self.model, all_columns, all_models, join_models) if condition is not None]

        allow_select = get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", model=self.model, default=True)
        select_fields = get_select_fields(flat_args, self.model, all_columns) if allow_select else []

        allow_group = get_config_or_model_meta("API_ALLOW_GROUPBY", model=self.model, default=False)
        group_by_fields = get_group_by_fields(flat_args, all_columns, self.model) if allow_group else []

        allow_agg = get_config_or_model_meta("API_ALLOW_AGGREGATION", model=self.model, default=False)
        aggregate_conditions = create_aggregate_conditions(flat_args) if allow_agg else {}
        agg_fields = []
        for key, label in aggregate_conditions.items():
            column_name, table_name, func_name = parse_column_table_and_operator(key, self.model)
            model_column, _ = validate_table_and_column(table_name, column_name, all_columns)
            agg_func = AGGREGATE_FUNCS.get(func_name)
            if agg_func:
                agg_label = label or f"{column_name}_{func_name}"
                owning_model = alias_to_model.get(table_name) or alias_to_model.get(normalise_join_token(table_name)) or self.model
                target_column = getattr(owning_model, column_name) if isinstance(model_column, hybrid_property) else model_column
                agg_fields.append(agg_func(target_column).label(agg_label))

        query = query or self.session.query(self.model)

        if allow_join and join_models:
            join_type = str(flat_args.get("join_type", "inner")).lower()
            if join_type not in {"inner", "left", "right", "outer"}:
                raise CustomHTTPException(400, f"Invalid join_type: {join_type}. Supported: inner,left,right,outer")

            for mdl in join_models.values():
                if join_type == "left" or join_type == "outer":
                    query = query.outerjoin(mdl)
                elif join_type == "right":
                    # SQLAlchemy ORM has no direct RIGHT JOIN; `isouter=True` behaves as LEFT OUTER in most dialects.
                    # Right join semantics require reversed join order; this is a best-effort fallback.
                    query = query.join(mdl, isouter=True)
                else:
                    query = query.join(mdl)

            # When joining one-to-many relationships, the base entity rows can
            # be duplicated which breaks pagination semantics (limit applies to
            # multiplied rows rather than distinct base rows). If the request
            # is not selecting custom fields, grouping, or aggregating, ensure
            # we paginate over distinct base rows.
            if not select_fields and not group_by_fields and not agg_fields:
                query = query.distinct()

        if agg_fields or group_by_fields:
            query = query.with_entities(*(group_by_fields + agg_fields))
        elif select_fields:
            query = query.with_entities(*select_fields)

        if conditions and get_config_or_model_meta("API_ALLOW_FILTERS", model=self.model, default=True):
            query = query.filter(and_(*conditions))

        if group_by_fields:
            query = query.group_by(*group_by_fields)

        return query

    def order_query(self, args_dict: dict, query: Query) -> Query:
        """
        Order the query based on the request arguments.
        Args:
            args_dict (dict): Dictionary containing filtering, sorting, pagination, and aggregation conditions.
            query (Query): The query to order.

        Returns:

        """
        if get_config_or_model_meta("API_ALLOW_ORDER_BY", model=self.model, default=True):
            query = apply_sorting_to_query(args_dict, query, self.model)
        return query

    def apply_soft_delete_filter(self, query: Query) -> Query:
        """Adds a soft delete filter to the query if applicable.

        Args:
            query (Query): The original query.

        Returns:
            Query: Query with soft delete filter applied.
        """
        if not get_config_or_model_meta("API_SOFT_DELETE", default=False):
            return query

        show_deleted = request.args.get("include_deleted", None)
        deleted_attr = get_config_or_model_meta("API_SOFT_DELETE_ATTRIBUTE", default=None)
        soft_delete_values = get_config_or_model_meta("API_SOFT_DELETE_VALUES", default=False)

        if not show_deleted and deleted_attr:
            models = {getattr(inspect(desc["entity"]).mapper, "class_", None) for desc in query.column_descriptions if desc["entity"]}

            for model in models:
                if hasattr(model, deleted_attr):
                    deleted_column = getattr(model, deleted_attr)
                    query = query.filter(deleted_column == soft_delete_values[0])

        return query

    @add_page_totals_and_urls
    @add_dict_to_query
    def get_query(
        self,
        args_dict: dict[str, str | int],
        lookup_val: int | str | None = None,
        alt_field: str | None = None,
        many: bool = True,
        other_model=None,
        **kwargs,
    ) -> dict[str, Any]:
        """Gets the query result after applying filtering, sorting, pagination, and aggregation.

        Args:
            args_dict (Dict[str, Union[str, int]]): Dictionary containing filtering, sorting, pagination, and aggregation conditions.
            lookup_val (Optional[Union[int, str]]): Value to lookup a single result by primary key or alternate field.
            alt_field (Optional[str]): Alternate field name to lookup a single result.
            many (bool): Whether to return multiple results.
            other_model (Callable): Other model for join operations.

        Returns:
            Dict[str, Any]: Dictionary with the query result and metadata.
        """
        base_model = self.model if other_model is None else other_model

        # Determine eager-loading preference based on configuration
        eager_depth = int(get_config_or_model_meta("API_SERIALIZATION_DEPTH", model=self.model, default=0) or 0)
        eager_enabled = bool(get_config_or_model_meta("API_ADD_RELATIONS", model=self.model, default=True)) and eager_depth > 0

        if not many and lookup_val:
            # When resolving singular relation endpoints (e.g., /parents/<id>/child),
            # prefer a relationship-aware join to avoid ambiguous FK joins.
            if kwargs.get("join_model") and kwargs.get("relation_name"):
                # Query the related B model via a relationship from A using the A PK lookup
                query = get_related_b_query(kwargs.get("join_model"), self.model, lookup_val, self.session)
            else:
                if kwargs.get("join_model"):
                    query = self.session.query(base_model).join(kwargs.get("join_model"))
                else:
                    query = self.session.query(base_model)
                    callback = get_config_or_model_meta("API_FILTER_CALLBACK", model=base_model, default=None)
                    if callback:
                        query = callback(query, self.model, args_dict)

                query = query.filter(getattr(base_model, alt_field) == lookup_val) if alt_field else query.filter_by(**get_primary_key_filters(base_model, lookup_val))

            # Apply eager-loader options for single-object fetches
            if eager_enabled:
                opts = _eager_options_for(base_model, eager_depth)
                if opts:
                    query = query.options(*opts)

            if get_config_or_model_meta("API_SOFT_DELETE", model=base_model, default=False):
                show_deleted = request.args.get("include_deleted", None)
                deleted_attr = get_config_or_model_meta("API_SOFT_DELETE_ATTRIBUTE", model=base_model, default=None)
                soft_delete_values = get_config_or_model_meta("API_SOFT_DELETE_VALUES", model=base_model, default=None)
                if not show_deleted and deleted_attr:
                    query = query.filter(getattr(base_model, deleted_attr) == soft_delete_values[0])

            result = query.one_or_none()

            if result is None:
                raise CustomHTTPException(404, "Resource not found.")

            return {"query": result}

        elif kwargs.get("join_model"):
            # used for relationship endpoints.

            lookup_val = kwargs.get(get_primary_key_info(kwargs.get("join_model"))[0])

            query = get_related_b_query(kwargs.get("join_model"), self.model, lookup_val, self.session)

            # Apply eager options for related collection endpoints
            if eager_enabled:
                opts = _eager_options_for(self.model if other_model is None else other_model, eager_depth)
                if opts:
                    query = query.options(*opts)

            # relationships i.e /authors/1/books should 404 when the parent is missing or has no children
            # Use a lightweight existence check to avoid complex join inference
            if query.first() is None:
                raise CustomHTTPException(404, f"{kwargs.get('join_model').__name__} not found.")

            query = self.filter_query_from_args(args_dict, query)
        else:
            query = self.filter_query_from_args(args_dict)

        # Apply eager options for general collection queries
        if eager_enabled and 'query' in locals() and hasattr(query, 'options'):
            opts = _eager_options_for(base_model, eager_depth)
            if opts:
                query = query.options(*opts)

        callback = get_config_or_model_meta("API_FILTER_CALLBACK", model=base_model, default=None)
        if callback:
            query = callback(query, self.model, args_dict)

        # Flatten args for order/pagination values
        flat_args = {k: (v[0] if isinstance(v, (list, tuple)) else v) for k, v in args_dict.items()}
        count = query.count()
        order_query = self.order_query(flat_args, query)

        # Apply soft delete filtering before pagination to avoid operating on
        # paginated objects, which lack SQLAlchemy query attributes such as
        # ``column_descriptions``.
        filtered_query = self.apply_soft_delete_filter(order_query)

        paginated_query, default_pagination_size = paginate_query(filtered_query, flat_args.get("page", 1), flat_args.get("limit"))

        return {
            "query": (paginated_query.all() if hasattr(paginated_query, "all") else (paginated_query.items if hasattr(paginated_query, "items") else paginated_query)),
            "limit": (int(flat_args.get("limit")) if flat_args.get("limit") else default_pagination_size),
            "page": int(flat_args.get("page")) if flat_args.get("page") else 1,
            "total_count": count,
        }

    def add_object(self, data_dict: dict[str, Any], *args, **kwargs) -> Callable:
        """Adds a new object to the database.

        Args:
            data_dict (Dict[str, Any]): Data to create the new object.

        Returns:
            Callable: The created object.

        Raises:
            IntegrityError: If there is a uniqueness constraint violation.
            DataError: If there is a data type error.
        """
        try:
            allow_nested = get_config_or_model_meta("ALLOW_NESTED_WRITES", model=self.model, default=False)
            payload = self._process_nested_relationships(self.model, data_dict.copy()) if allow_nested else data_dict
            obj = self.model(**payload)

            callback = get_config_or_model_meta("API_ADD_CALLBACK", model=self.model, default=None)
            if callback:
                obj = callback(obj, self.model)

            self.session.add(obj)
            self.session.commit()
            return obj
        except (IntegrityError, DataError) as e:
            self.session.rollback()
            raise CustomHTTPException(422, str(e.orig)) from e

    def update_object(self, lookup_val: int | str, data_dict: dict[str, Any], *args, **kwargs) -> Callable:
        """Updates an existing object in the database.

        Args:
            lookup_val (Union[int, str]): Value to lookup the object by primary key.
            update_dict (Dict[str, Any]): Data to update the object.

        Returns:
            Callable: The updated object.

        Raises:
            IntegrityError: If there is a uniqueness constraint violation.
            DataError: If there is a data type error.
        """
        try:
            obj = self.session.query(self.model).filter_by(**get_primary_key_filters(self.model, lookup_val)).one_or_none()
            if obj is None:
                raise CustomHTTPException(404, f"{self.model.__name__} not found.")

            payload = data_dict or {}
            allow_nested = get_config_or_model_meta("ALLOW_NESTED_WRITES", model=self.model, default=False)
            update_payload = self._process_nested_relationships(self.model, payload.copy()) if allow_nested else payload

            mapper = inspect(self.model)
            writable_keys = {column.key for column in mapper.columns}

            for key, value in update_payload.items():
                if key not in writable_keys:
                    continue
                setattr(obj, key, value)

            callback = get_config_or_model_meta("API_UPDATE_CALLBACK", model=self.model, default=None)
            if callback:
                obj = callback(obj, self.model)

            self.session.commit()
            return obj
        except (IntegrityError, DataError) as e:
            self.session.rollback()
            raise CustomHTTPException(422, str(e.orig)) from e

    def delete_object(self, lookup_val: int | str, *args, **kwargs) -> None:
        """
        Deletes an object from the database.

        Args:
            lookup_val (Union[int, str]): Value to lookup the object by primary key.

        Raises:
            CustomHTTPException: If the object is not found or conflicts with related/dependent data.
        """
        # Fetch cascade_delete flag from request args
        cascade_delete = int(request.args.get("cascade_delete", 0)) == 1

        obj = self.session.query(self.model).filter_by(**get_primary_key_filters(self.model, lookup_val)).one_or_none()

        if obj is None:
            raise CustomHTTPException(404, f"{self.model.__name__} not found.")

        callback = get_config_or_model_meta("API_REMOVE_CALLBACK", model=self.model, default=None)
        if callback:
            obj = callback(obj, self.model)

        # Handle soft deletes when configured.
        if get_config_or_model_meta("API_SOFT_DELETE", model=self.model, default=False) and not cascade_delete:
            deleted_attr = get_config_or_model_meta("API_SOFT_DELETE_ATTRIBUTE", model=self.model, default=None)
            soft_delete_values = get_config_or_model_meta("API_SOFT_DELETE_VALUES", model=self.model, default=None)

            if not deleted_attr or not soft_delete_values:
                raise CustomHTTPException(500, "Soft delete misconfigured")

            setattr(obj, deleted_attr, soft_delete_values[1])
            self.session.commit()
            return None, 200

        with self.session.no_autoflush:
            self.session.delete(obj)
            try:
                if not get_config_or_model_meta("API_ALLOW_CASCADE_DELETE", model=self.model, default=True) or request.args.get("cascade_delete") != "1":
                    self.session.commit()
                    return None, 200

                # Perform recursive delete based on cascade_delete flag

                recursive_delete(obj, cascade_delete)
                self.session.commit()

            except SQLAlchemyError as e:
                self.session.rollback()
                if get_config_or_model_meta("API_ALLOW_CASCADE_DELETE", model=self.model, default=False):
                    error_msg = "Error deleting object, use url parameter `cascade_delete=1` to attempt cascade delete"
                else:
                    error_msg = "Error deleting object"

                raise CustomHTTPException(409, error_msg) from e

        return None, 200


def recursive_delete(obj, cascade_delete=True, visited=None, objects_touched=None, parent=None):
    """Recursively delete related objects following foreign key constraints.

    Why/How:
        Traverses relationships to remove dependent records when permitted.
        Tracks visited instances to avoid cycles and redundant operations,
        reducing database round‑trips on complex graphs.

    Args:
        obj: The SQLAlchemy model instance to delete.
        cascade_delete (bool): Whether to recursively delete related objects.
        visited (set): Set of visited objects (by class and primary keys) to avoid redundant deletion.
        objects_touched (list): Objects deleted during the recursion (for diagnostics).
        parent: Parent object of the current step to prevent backward traversal in cyclic relationships.
    """

    def get_obj_id(obj):
        mapper = inspect(obj.__class__)
        return (
            obj.__class__,
            tuple(getattr(obj, col.name) for col in mapper.primary_key),
        )

    if visited is None:
        visited = set()
    if objects_touched is None:
        objects_touched = []

    try:
        session = object_session(obj)
    except UnmappedInstanceError:
        # The object is not mapped, possibly already deleted
        return

    mapper = inspect(obj.__class__)

    # Create a unique identifier for the object based on its class and primary key(s)
    obj_identifier = get_obj_id(obj)

    # Skip if the object has already been visited
    if obj_identifier in visited:
        return

    # Mark this object as visited
    visited.add(obj_identifier)

    # Log the source object when it's first called and add it to the touched list
    objects_touched.append((obj.__class__.__name__, obj_identifier[1]))
    print(f"Processing deletion for object: {obj.__class__.__name__} with ID: {obj_identifier[1]}")

    # Iterate through relationships of the object
    for relationship in mapper.relationships:
        # Avoid backtracking to the parent object
        if parent and relationship.mapper.class_ == parent.__class__:
            continue

        # Get related objects for the current relationship
        related_objects = getattr(obj, relationship.key)

        if related_objects is None:
            continue

        # Determine if the relationship is a collection (one-to-many or many-to-many)
        if relationship.uselist:
            # It's a collection
            for related_obj in related_objects:
                related_obj_id = get_obj_id(related_obj)
                if related_obj_id not in visited:
                    recursive_delete(related_obj, cascade_delete, visited, objects_touched, obj)
        else:
            # It's a scalar relationship (one-to-one or many-to-one)
            related_obj = related_objects
            related_obj_id = get_obj_id(related_obj)
            if related_obj_id not in visited:
                # For many-to-one, we generally don't delete the parent object
                if relationship.direction.name == "MANYTOONE":
                    print(f"Skipping deletion of parent object {related_obj.__class__.__name__}")
                    continue
                else:
                    recursive_delete(related_obj, cascade_delete, visited, objects_touched, obj)

    # Log the actual deletion of the source object
    print(f"Deleting object: {obj.__class__.__name__} with ID: {obj_identifier[1]}")
    session.delete(obj)

    return objects_touched
