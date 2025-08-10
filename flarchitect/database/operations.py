import random
from collections.abc import Callable
from typing import Any

from flask import request
from sqlalchemy import Column, and_, inspect
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Query, Session, object_session
from sqlalchemy.orm.exc import UnmappedInstanceError

from flarchitect.core.utils import get_primary_key_info
from flarchitect.database.utils import (
    generate_conditions_from_args,
    get_all_columns_and_hybrids,
    get_models_for_join,
    get_primary_key_filters,
    get_related_b_query,
    get_select_fields,
    get_table_and_column,
)
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.decorators import add_dict_to_query, add_page_totals_and_urls


def get_model_relationships(
    model: DeclarativeBase, randomise: bool = True
) -> list[type[DeclarativeBase]]:
    """
    Extracts relationships from a SQLAlchemy model.

    Args:
        model (DeclarativeBase): The SQLAlchemy model.
        randomise (bool, optional): Whether to randomise the order of relationships.

    Returns:
        List[Type[DeclarativeBase]]: A list of related models.
    """
    relationships = [
        relationship.mapper.class_ for relationship in inspect(model).relationships
    ]
    if randomise:
        random.shuffle(relationships)
    return relationships


def get_model_columns(model: DeclarativeBase, randomise: bool = True) -> list[str]:
    """
    Extracts column names from a SQLAlchemy model.

    Args:
        model (DeclarativeBase): The SQLAlchemy model.
        randomise (bool, optional): Whether to randomize the order of columns.

    Returns:
        List[str]: A list of column names.
    """
    columns = [x.name for x in list(inspect(model).mapper.columns)]
    if randomise:
        random.shuffle(columns)
    return columns


def paginate_query(
    sql_query: Query, page: int = 0, items_per_page: int | None = None
) -> Query:
    """Applies pagination to a query.

    Args:
        sql_query (Query): SQLAlchemy query to paginate.
        page (int): Page number.
        items_per_page (int): Number of items per page.

    Returns:
        Query: Paginated query.
    """

    def validate_pagination_params(page: int, items_per_page: int):
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

    default_pagination_size = get_config_or_model_meta(
        "API_PAGINATION_SIZE_DEFAULT", default=20
    )

    if items_per_page is None:
        items_per_page = default_pagination_size

    validate_pagination_params(page, items_per_page)

    return (
        sql_query.paginate(
            page=int(page), per_page=int(items_per_page), error_out=False
        ),
        default_pagination_size,
    )


def apply_sorting_to_query(
    args_dict: dict[str, str | int], query: Query, base_model: Callable
) -> Query:
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
        """Initializes the CrudService instance.

        Args:
            model (Callable): SQLAlchemy model class for CRUD operations.
            session (Session): SQLAlchemy session.
        """
        self.model = model
        self.session = session

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
        related_model = relationships.get(field_name)

        if related_model is None:
            raise CustomHTTPException(
                401,
                f"Field {field_name} does not represent a relationship in model {self.model.__name__}",
            )

        return related_model.mapper.class_

    def filter_query_from_args(
        self, args_dict: dict[str, str | int], query=None
    ) -> Query:
        """Filters a query based on request arguments.

        Args:
            args_dict (Dict[str, Union[str, int]]): Dictionary containing filtering, sorting, pagination, and aggregation conditions.

        Returns:
            Query: The filtered query.
        """
        join_models = get_models_for_join(args_dict, self.fetch_related_model_by_name)
        all_columns, all_models = get_all_columns_and_hybrids(self.model, join_models)

        conditions = [
            condition
            for condition in generate_conditions_from_args(
                args_dict, self.model, all_columns, all_models, join_models
            )
            if condition is not None
        ]

        query = self.initialize_query(args_dict, all_columns, query)

        if conditions and get_config_or_model_meta(
            "API_ALLOW_FILTER", model=self.model, default=True
        ):
            query = query.filter(and_(*conditions))

        return query

    def order_query(self, args_dict: dict, query: Query) -> Query:
        """
        Order the query based on the request arguments.
        Args:
            args_dict (dict): Dictionary containing filtering, sorting, pagination, and aggregation conditions.
            query (Query): The query to order.

        Returns:

        """
        if get_config_or_model_meta(
            "API_ALLOW_ORDER_BY", model=self.model, default=True
        ):
            query = apply_sorting_to_query(args_dict, query, self.model)
        return query

    def initialize_query(
        self,
        args_dict: dict[str, str | int],
        all_columns: dict[str, Column],
        query=None,
    ) -> Query:
        """Helper function to initialize the query based on select fields.

        Args:
            args_dict (Dict[str, Union[str, int]]): Dictionary containing filtering, sorting, pagination, and aggregation conditions.
            all_columns (Dict[str, Column]): Dictionary of all columns and hybrids.

        Returns:
            Query: Initialized query.
        """
        allow_select = get_config_or_model_meta(
            "API_ALLOW_SELECT_FIELDS", model=self.model, default=True
        )
        select_fields = (
            get_select_fields(args_dict, self.model, all_columns)
            if allow_select
            else []
        )

        if select_fields:
            if query:
                return query.select_from(*select_fields)
            return self.session.query(*select_fields)

        if query:
            return query
        return self.session.query(self.model)

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
        deleted_attr = get_config_or_model_meta(
            "API_SOFT_DELETE_ATTRIBUTE", default=None
        )
        soft_delete_values = get_config_or_model_meta(
            "API_SOFT_DELETE_VALUES", default=False
        )

        if not show_deleted and deleted_attr:
            models = {
                getattr(inspect(desc["entity"]).mapper, "class_", None)
                for desc in query.column_descriptions
                if desc["entity"]
            }

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

        if not many and lookup_val:
            if kwargs.get("join_model"):
                query = self.session.query(base_model).join(kwargs.get("join_model"))

            else:
                query = self.session.query(base_model)
                callback = get_config_or_model_meta(
                    "API_FILTER_CALLBACK", model=base_model, default=None
                )
                if callback:
                    query = callback(query, self.model, args_dict)

            if alt_field:
                query = query.filter(getattr(base_model, alt_field) == lookup_val)
            else:
                query = query.filter_by(
                    **get_primary_key_filters(base_model, lookup_val)
                )

            result = query.one_or_none()

            if result is None:
                raise CustomHTTPException(404, "Resource not found.")

            return {"query": result}

        elif kwargs.get("join_model"):
            # used for relationship endpoints.

            lookup_val = kwargs.get(get_primary_key_info(kwargs.get("join_model"))[0])

            query = get_related_b_query(
                kwargs.get("join_model"), self.model, lookup_val, self.session
            )

            # relationships i.e /authors/1/books was returning a 200 when author is None. This fixes it.
            if query.count() == 0:
                raise CustomHTTPException(
                    404, f"{kwargs.get('join_model').__name__} not found."
                )

            query = self.filter_query_from_args(args_dict, query)
        else:
            query = self.filter_query_from_args(args_dict)

        callback = get_config_or_model_meta(
            "API_FILTER_CALLBACK", model=base_model, default=None
        )
        if callback:
            query = callback(query, self.model, args_dict)

        count = query.count()
        order_query = self.order_query(args_dict, query)

        paginated_query, default_pagination_size = paginate_query(
            order_query, args_dict.get("page", 1), args_dict.get("limit")
        )

        final_query = self.apply_soft_delete_filter(paginated_query)

        return {
            "query": (
                final_query.all()
                if hasattr(final_query, "all")
                else final_query.items
                if hasattr(final_query, "items")
                else final_query
            ),
            "limit": (
                int(args_dict.get("limit"))
                if args_dict.get("limit")
                else default_pagination_size
            ),
            "page": int(args_dict.get("page")) if args_dict.get("page") else 1,
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
            obj = self.model(**data_dict)

            callback = get_config_or_model_meta(
                "API_ADD_CALLBACK", model=self.model, default=None
            )
            if callback:
                obj = callback(obj, self.model)

            self.session.add(obj)
            self.session.commit()
            return obj
        except (IntegrityError, DataError) as e:
            self.session.rollback()
            raise CustomHTTPException(422, str(e.orig))

    def update_object(
        self, lookup_val: int | str, data_dict: dict[str, Any], *args, **kwargs
    ) -> Callable:
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
            obj = (
                self.session.query(self.model)
                .filter_by(**get_primary_key_filters(self.model, lookup_val))
                .one_or_none()
            )
            if obj is None:
                raise CustomHTTPException(404, f"{self.model.__name__} not found.")
            for key, value in data_dict.items():
                setattr(obj, key, value)

            callback = get_config_or_model_meta(
                "API_UPDATE_CALLBACK", model=self.model, default=None
            )
            if callback:
                obj = callback(obj, self.model)

            self.session.commit()
            return obj
        except (IntegrityError, DataError) as e:
            self.session.rollback()
            raise CustomHTTPException(422, str(e.orig))

    def delete_object(
        self, lookup_val: int | str, *args, **kwargs
    ) -> None:
        """
        Deletes an object from the database.

        Args:
            lookup_val (Union[int, str]): Value to lookup the object by primary key.

        Raises:
            CustomHTTPException: If the object is not found or conflicts with related/dependent data.
        """
        # Fetch cascade_delete flag from request args
        cascade_delete = int(request.args.get("cascade_delete", 0)) == 1

        obj = (
            self.session.query(self.model)
            .filter_by(**get_primary_key_filters(self.model, lookup_val))
            .one_or_none()
        )

        if obj is None:
            raise CustomHTTPException(404, f"{self.model.__name__} not found.")

        callback = get_config_or_model_meta(
            "API_REMOVE_CALLBACK", model=self.model, default=None
        )
        if callback:
            obj = callback(obj, self.model)

        with self.session.no_autoflush:
            self.session.delete(obj)
            try:
                if (
                    not get_config_or_model_meta(
                        "API_ALLOW_CASCADE_DELETE", model=self.model, default=True
                    )
                    or request.args.get("cascade_delete") != "1"
                ):
                    self.session.commit()
                    return None, 200

                # Perform recursive delete based on cascade_delete flag

                objects_touched = recursive_delete(obj, cascade_delete)
                self.session.commit()

            except SQLAlchemyError:
                self.session.rollback()
                if get_config_or_model_meta(
                    "API_ALLOW_CASCADE_DELETE", model=self.model, default=False
                ):
                    error_msg = "Error deleting object, use url parameter `cascade_delete=1` to attempt cascade delete"
                else:
                    error_msg = "Error deleting object"

                raise CustomHTTPException(409, error_msg)

        return None, 200


def recursive_delete(
    obj, cascade_delete=True, visited=None, objects_touched=None, parent=None
):
    """
    Recursively delete related objects based on foreign key constraints, optimized for performance.

    Args:
        obj: The SQLAlchemy model instance to delete.
        cascade_delete (bool): Whether to recursively delete related objects.
        visited (set): Set of visited objects (identified by their class and primary keys) to avoid redundant deletion.
        objects_touched (list): List of objects touched (deleted) during the recursive process.
        parent: The parent object of the current recursion step, used to prevent backward traversal in cyclic relationships.
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
    print(
        f"Processing deletion for object: {obj.__class__.__name__} with ID: {obj_identifier[1]}"
    )

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
                    recursive_delete(
                        related_obj, cascade_delete, visited, objects_touched, obj
                    )
        else:
            # It's a scalar relationship (one-to-one or many-to-one)
            related_obj = related_objects
            related_obj_id = get_obj_id(related_obj)
            if related_obj_id not in visited:
                # For many-to-one, we generally don't delete the parent object
                if relationship.direction.name == "MANYTOONE":
                    print(
                        f"Skipping deletion of parent object {related_obj.__class__.__name__}"
                    )
                    continue
                else:
                    recursive_delete(
                        related_obj, cascade_delete, visited, objects_touched, obj
                    )

    # Log the actual deletion of the source object
    print(f"Deleting object: {obj.__class__.__name__} with ID: {obj_identifier[1]}")
    session.delete(obj)

    return objects_touched
