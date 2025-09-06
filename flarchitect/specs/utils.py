import copy
import os
import random
import re
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from marshmallow import Schema, fields
from marshmallow_sqlalchemy.fields import Nested, Related, RelatedList
from sqlalchemy.orm import DeclarativeBase
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.routing import IntegerConverter, UnicodeConverter

from flarchitect.database.inspections import get_model_columns, get_model_relationships
from flarchitect.database.utils import AGGREGATE_FUNCS
from flarchitect.logging import logger
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case
from flarchitect.utils.general import (
    DATE_FORMAT,
    DATETIME_FORMAT,
    get_html_path,
    manual_render_absolute_template,
    pluralize_last_word,
)
from flarchitect.utils.response_helpers import create_response


def schema_name_resolver(schema: Schema) -> str:
    """Resolve a schema name based on configuration.

    Args:
        schema (Schema): Schema instance or class whose name requires resolving.

    Returns:
        str: The schema name converted using ``API_SCHEMA_CASE``.
    """

    schema_cls = schema if isinstance(schema, type) else schema.__class__
    model = getattr(getattr(schema_cls, "Meta", None), "model", None)
    case = get_config_or_model_meta("API_SCHEMA_CASE", model=model, default="camel") or "camel"
    return convert_case(schema_cls.__name__.replace("Schema", ""), case)


def scrape_extra_info_from_spec_data(
    spec_data: dict[str, Any],
    method: str,
    multiple: bool = False,
    summary: bool = False,
) -> dict[str, Any]:
    """
    Scrapes extra information from the spec data for API documentation generation.

    Args:
        spec_data (Dict[str, Any]): The spec data.
        method (str): The HTTP method (e.g., 'get', 'post').
        multiple (bool, optional): Whether the operation involves multiple items.
        summary (bool, optional): Whether to generate a summary.

    Returns:
        Dict[str, Any]: Updated spec data with extra information.
    """
    model = spec_data.get("model")
    output_schema = spec_data.get("output_schema")
    input_schema = spec_data.get("input_schema")
    function = spec_data.get("function")

    if not all([model, output_schema or input_schema, method, function]):
        missing = []
        if not model:
            missing.append("model")
        if not (output_schema or input_schema):
            missing.append("schema")
        if not method:
            missing.append("method")
        if not function:
            missing.append("function")
        logger.log(1, f"Missing data for documentation generation: {', '.join(missing)}")

    if spec_data.get("tag") is None:
        new_tag = get_config_or_model_meta("tag", model, output_schema, input_schema, "Unknown")
        if new_tag:
            spec_data["tag"] = new_tag
    else:
        spec_data["tag"] = spec_data.get("tag")

    if not summary and get_config_or_model_meta("AUTO_NAME_ENDPOINTS", default=True):
        schema = spec_data.get("output_schema") or spec_data.get("input_schema")
        if schema:
            spec_data["summary"] = make_endpoint_description(schema, method, **spec_data)
    else:
        spec_data["summary"] = summary

    new_description = get_summary_description(function)
    if new_description:
        spec_data["description"] = new_description

    for description_type in ["summary", "description"]:
        if method.lower() == "get" and multiple:
            config_val = f"{method.lower()}_many" + description_type
        elif method.lower() == "get" and not multiple:
            config_val = f"{method.lower()}_single" + description_type
        else:
            config_val = f"{method.lower()}" + description_type

        new_desc = get_config_or_model_meta(config_val, model, output_schema, input_schema, None)
        if new_desc:
            spec_data[description_type] = new_desc

    return spec_data


def get_summary_description(f: Callable) -> str | None:
    """
    Retrieves and formats the summary description from a function's docstring.

    Args:
        f (Callable): The function to extract the description from.

    Returns:
        Optional[str]: The formatted description, or None if not available.
    """
    description = f.__doc__.strip() if f.__doc__ else None
    return description.replace("  ", " ") if description else None


def get_param_schema(converter) -> dict[str, str]:
    """Helper function to get the schema for a parameter based on its converter.

    Args:
        converter: The converter to determine the schema for.

    Returns:
        Dict[str, str]: The schema for the parameter.
    """
    if isinstance(converter, IntegerConverter):
        return {"type": "integer"}
    elif isinstance(converter, UnicodeConverter):
        return {"type": "string"}
    else:
        return {"type": "string"}


def generate_delete_query_params(schema: Schema, model: DeclarativeBase) -> list[dict[str, Any]]:
    """Helper function to generate query parameters for DELETE method.

    Args:
        schema (Schema): The schema associated with the model.
        model (DeclarativeBase): The SQLAlchemy model.

    Returns:
        List[Dict[str, Any]]: List of query parameters for DELETE method.
    """
    query_params = []

    if get_config_or_model_meta("API_ALLOW_CASCADE_DELETE", getattr(schema.Meta, "model", None), default=True):
        query_params.append(
            {
                "name": "cascade_delete",
                "in": "query",
                "schema": {"type": "boolean"},
                "description": "If true or 1, will delete all recursively dependent resources.",
            }
        )
    return query_params


def generate_get_query_params(schema: Schema, model: DeclarativeBase) -> list[dict[str, Any]]:
    """Helper function to generate query parameters for GET method.

    Args:
        schema (Schema): The schema associated with the model.
        model (DeclarativeBase): The SQLAlchemy model.

    Returns:
        List[Dict[str, Any]]: List of query parameters for GET method.
    """
    query_params = []
    page_max = get_config_or_model_meta("API_PAGINATION_SIZE_MAX", default=100)
    page_default = get_config_or_model_meta("API_PAGINATION_SIZE_DEFAULT", default=20)

    if get_config_or_model_meta("API_SOFT_DELETE", default=False):
        query_params.append(
            {
                "name": "include_deleted",
                "in": "query",
                "schema": {"type": "boolean"},
                "description": "If true, deleted items will be included in the response.",
            }
        )
    query_params.extend(
        [
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer", "example": 20},
                "description": f"The maximum number of items to return in the response. Default `{page_default}` Maximum `{page_max}`.",
            },
            {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "example": 1},
                "description": "The pagination page number. Default `1`.",
            },
        ]
    )
    return query_params


def generate_additional_query_params(methods: set, schema: Schema, model: DeclarativeBase) -> list[dict[str, Any]]:
    """Helper function to generate additional query parameters.

    Args:
        methods (set): Set of methods to generate query parameters for.
        schema (Schema): The schema associated with the model.
        model (DeclarativeBase): The SQLAlchemy model.

    Returns:
        List[Dict[str, Any]]: List of additional query parameters.
    """
    query_params = []
    for method in methods:
        additional_qs = get_config_or_model_meta(
            "API_ADDITIONAL_QUERY_PARAMS",
            model=model,
            method=method,
            input_schema=schema,
        )
        if additional_qs:
            query_params.extend(additional_qs)
    return query_params


def _add_request_body_to_spec_template(
    spec_template: dict[str, Any],
    _http_method: str,
    input_schema: Schema,
    _model: DeclarativeBase | None,
):
    """Helper function to add a request body to the spec template.

    Args:
        spec_template (Dict[str, Any]): The OpenAPI specification template to enhance.
        _http_method (str): The HTTP method (GET, POST, PUT, DELETE, PATCH).
        input_schema (Schema): The Marshmallow schema for request body validation.
        _model (Optional[DeclarativeBase]): The SQLAlchemy model for database interactions.

    Returns:
        None
    """
    name = schema_name_resolver(input_schema)

    spec_template["requestBody"] = {
        "description": f"`{name}` payload.",
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": f"#/components/schemas/{name}"},
            }
        },
    }


def _add_response_to_spec_template(spec_template: dict[str, Any], output_schema: Schema):
    """Helper function to add a response to the spec template.

    Args:
        spec_template (Dict[str, Any]): The OpenAPI specification template to enhance.
        output_schema (Schema): The Marshmallow schema for response data serialisation.

    Returns:
        None
    """
    model = output_schema.get_model() if hasattr(output_schema, "get_model") else None
    case = get_config_or_model_meta("API_SCHEMA_CASE", model=model, default="camel")
    name = convert_case(output_schema.__name__.replace("Schema", ""), case)

    spec_template.setdefault("responses", {}).setdefault("200", {}).update(
        {
            "description": HTTP_STATUS_CODES.get(200),
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{name}"},
                }
            },
        }
    )


def build_error_response(status_code: int, links: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a standardised error response for the OpenAPI specification.

    Args:
        status_code (int): HTTP status code representing the error.
        links (Optional[Dict[str, Any]]): Optional OpenAPI links related to the error.

    Returns:
        Dict[str, Any]: Response block including example payload.
    """
    example = create_response(status=status_code, errors={"error": HTTP_STATUS_CODES.get(status_code)}).get_json()

    response: dict[str, Any] = {
        "description": HTTP_STATUS_CODES.get(status_code),
        "content": {"application/json": {"example": example}},
    }

    if links:
        response["links"] = links

    return response


def _initialize_base_responses(
    method: str,
    many: bool,
    error_responses: list[int],
    links: dict[int, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Initialise base responses for a route.

    Args:
        method (str): The HTTP method.
        many (bool): Whether the endpoint returns multiple items.
        error_responses (List[int]): List of error response status codes.
        links (Optional[Dict[int, Dict[str, Any]]]): Links for specific error responses.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of base responses.
    """
    links = links or {}
    responses = {"200": {"description": "Successful operation"}}

    if 500 in error_responses or not error_responses:
        responses["500"] = build_error_response(500, links.get(500))

    if method != "POST" and not many and (404 in error_responses or not error_responses):
        responses["404"] = build_error_response(404, links.get(404))

    if method == "DELETE" and not many and (409 in error_responses or not error_responses):
        responses["409"] = build_error_response(409, links.get(409))

    return responses


def _initialize_auth_responses(
    error_responses: list[int],
    links: dict[int, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Initialise authentication error responses.

    Args:
        error_responses (List[int]): List of error response status codes.
        links (Optional[Dict[int, Dict[str, Any]]]): Links for specific error responses.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of authentication responses.
    """
    responses = {}
    links = links or {}
    auth_on = get_config_or_model_meta("API_AUTHENTICATE", default=False)

    # Include 401/403 when explicitly requested via error_responses OR when
    # authentication is globally enabled and no explicit list was provided.
    want_401 = (error_responses and 401 in error_responses) or (auth_on and not error_responses)
    want_403 = (error_responses and 403 in error_responses) or (auth_on and not error_responses)

    if want_403:
        responses["403"] = build_error_response(403, links.get(403))
    if want_401:
        responses["401"] = build_error_response(401, links.get(401))

    return responses


def _initialize_rate_limit_responses(rate_limit: bool) -> dict[str, dict[str, Any]]:
    """Helper function to initialise rate limit responses.

    Args:
        rate_limit (bool): Whether the endpoint has a rate limit.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of rate limit responses.
    """
    if not rate_limit:
        return {}

    rate_limit_headers = {
        "X-RateLimit-Limit": {
            "description": "The maximum number of requests allowed in a time window.",
            "schema": {"type": "integer", "format": "int32", "example": 100},
        },
        "X-RateLimit-Remaining": {
            "description": "The number of requests remaining in the current rate limit window.",
            "schema": {"type": "integer", "format": "int32", "example": 99},
        },
        "X-RateLimit-Reset": {
            "description": "The time at which the current rate limit window resets (in UTC epoch seconds).",
            "schema": {"type": "integer", "format": "int32", "example": 15830457},
        },
        "Retry-After": {
            "description": "The amount of time to wait before making another request (in seconds).",
            "schema": {"type": "integer", "format": "int32", "example": 20},
        },
    }

    return {
        "429": {
            "description": HTTP_STATUS_CODES.get(429),
            "headers": rate_limit_headers.copy(),
        },
        "200": {
            "headers": rate_limit_headers,
        },
    }


def get_template_data_for_model(schema: Schema) -> dict[str, Any] | None:
    """Generates model data for Jinja template and Redoc.

    Args:
        schema (Schema): Schema to generate model data for.

    Returns:
        Optional[Dict[str, Any]]: Model data for the template.
    """
    schema_case = get_config_or_model_meta("API_SCHEMA_CASE", default="camel")

    if hasattr(schema, "Meta") and hasattr(schema.Meta, "model"):
        base_model = schema.Meta.model
        base_resource = convert_case(base_model.__name__, schema_case)
        base_fields = get_model_columns(base_model)

        model_relationships = get_model_relationships(base_model)
        model_relationship_names = [convert_case(x.__name__, schema_case) for x in model_relationships]

        if model_relationships:
            relationship_fields = get_model_columns(model_relationships[0])
            relationship_resource = convert_case(model_relationships[0].__name__, schema_case)
        else:
            relationship_fields = []
            relationship_resource = None

        aggs = ", ".join([f"`{x}`" for x in AGGREGATE_FUNCS])

        return {
            "relationship_resource": relationship_resource,
            "relationship_fields": relationship_fields,
            "base_resource": base_resource,
            "base_fields": base_fields,
            "aggs": aggs,
            "model_relationship_names": model_relationship_names,
        }
    return None


def generate_example_values(now: datetime, yesterday: datetime, day_before_yesterday: datetime) -> dict[str, list[str]]:
    """Helper function to generate example values for filter examples.

    Args:
        now (datetime): Current datetime.
        yesterday (datetime): Datetime of yesterday.
        day_before_yesterday (datetime): Datetime of the day before yesterday.

    Returns:
        Dict[str, List[str]]: Dictionary with example values.
    """
    return {
        "Integer": ["1", "10", "100", "500", "1000"],
        "Float": ["1.25", "2.50", "3.75", "5.00"],
        "String": ["John", "Doe", "Jane"],
        "Boolean": ["true", "false"],
        "Date": [
            now.date().strftime(DATE_FORMAT),
            yesterday.date().strftime(DATE_FORMAT),
            day_before_yesterday.date().strftime(DATE_FORMAT),
        ],
        "DateTime": [
            now.strftime(DATETIME_FORMAT),
            yesterday.strftime(DATETIME_FORMAT),
            day_before_yesterday.strftime(DATETIME_FORMAT),
        ],
        "Time": ["12:00:00", "13:00:00", "14:00:00"],
    }


def generate_operators() -> dict[str, list[str]]:
    """Helper function to generate operators for different data types.

    Returns:
        Dict[str, List[str]]: Dictionary with operators for each data type.
    """
    return {
        "Integer": [
            "__eq",
            "__lt",
            "__le",
            "__gt",
            "__ge",
            "__ne",
            "__in",
            "__nin",
            "__like",
            "__ilike",
        ],
        "Float": [
            "__eq",
            "__lt",
            "__le",
            "__gt",
            "__ge",
            "__ne",
            "__in",
            "__nin",
            "__like",
            "__ilike",
        ],
        "String": ["__eq", "__ne", "__in", "__nin", "__like", "__ilike"],
        "Bool": ["__eq", "__ne", "__in", "__nin"],
        "Date": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
        "DateTime": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
        "Time": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
    }


def generate_operator_examples(
    schema: Schema,
    operators: dict[str, list[str]],
    example_values: dict[str, list[str]],
) -> list[str]:
    """Helper function to generate operator examples for filters.

    Args:
        schema (Schema): The schema to generate examples for.
        operators (Dict[str, List[str]]): Operators applicable to each data type.
        example_values (Dict[str, List[str]]): Example values for each data type.

    Returns:
        List[str]: List of generated filter examples.
    """
    examples = []

    # Assuming fields is a function that needs to be called
    try:
        fields = schema().dump_fields  # Accessing fields through an instance
    except TypeError:
        fields = schema.dump_fields

    # Generate column examples only for those fields that are not dump_only
    columns = [k for k, v in fields.items() if v and not v.dump_only]

    for column in columns:
        col_type = type(fields[column]).__name__
        if col_type in operators:
            chosen_operator = random.choice(operators[col_type])
            if chosen_operator in ["__in", "__nin"]:
                chosen_values = ", ".join(random.choices(example_values.get(col_type, ["value"]), k=3))
                examples.append(f"{column}{chosen_operator}=({chosen_values})")
            else:
                chosen_value = random.choice(example_values.get(col_type, ["value"]))
                examples.append(f"{column}{chosen_operator}={chosen_value}")

    return examples


def get_table_name(index: int, resource_name: str, fields: list[str], example_table: list[str]) -> str:
    """Helper function to generate table names for field examples.

    Args:
        index (int): The index to determine which example to generate.
        resource_name (str): The name of the resource.
        fields (List[str]): The list of fields.
        example_table (List[str]): The example table data.

    Returns:
        str: Generated table name.
    """
    temp_fields = copy.deepcopy([x[0] for x in fields])
    random.shuffle(temp_fields)
    if index == 0:
        current_fields = temp_fields[:3]
    elif index == 1:
        current_fields = [resource_name + "." + x for x in temp_fields[:3]]
    else:
        current_fields = []
        for _ in range(5):
            table_choice = random.choice([resource_name, "OtherTable"])
            field_choice = random.choice(temp_fields) if table_choice == resource_name else random.choice(example_table)
            current_fields.append(f"{table_choice}.{field_choice}")

    return "fields=" + ",".join(current_fields)


def _prepare_patch_schema(input_schema: Schema | None) -> Schema | None:
    """Prepare a patch schema with all fields optional.

    Args:
        input_schema (Optional[Schema]): The input schema to prepare the patch schema for.

    Returns:
        Optional[Schema]: The prepared patch schema with all fields set to optional.
    """
    if not input_schema:
        return None

    # Initialise a dictionary to hold the new class's fields
    class_fields = {}

    # Iterate over all fields in the input schema
    items = input_schema.fields.items() if hasattr(input_schema, "fields") else input_schema().fields.items()

    for field_name, field_obj in items:
        # Deepcopy the field to avoid mutating the original field
        new_field = deepcopy(field_obj)

        # Set the field to be optional
        new_field.required = False
        new_field.allow_none = True

        # Add the modified field to the class fields
        class_fields[field_name] = new_field

    # Preserve the Meta class if it exists
    Meta = getattr(input_schema.__class__, "Meta", None)
    if Meta:
        class_fields["Meta"] = Meta

    # Dynamically create a new schema class with the modified fields
    PatchSchemaClass = type(
        f"Patch{input_schema.__class__.__name__}",
        (Schema,),  # Inherit directly from Schema to avoid field conflicts
        class_fields,
    )

    # Instantiate the new schema class
    put_input_schema = PatchSchemaClass()

    return put_input_schema


def make_endpoint_description(schema: Schema, http_method: str, **kwargs) -> str:
    """Generates endpoint description from a schema for the API docs.

    Only applicable in FULL_AUTO mode or if AUTO_NAME_ENDPOINTS = True.

    Args:
        schema (Schema): Schema to generate endpoint description from.
        http_method (str): HTTP method.

    Returns:
        str: Endpoint description.
    """
    many = kwargs.get("multiple")
    model = getattr(schema, "get_model", lambda: None)()
    name = (kwargs.get("model") or model or schema).__name__.replace("Schema", "")
    name = convert_case(name, get_config_or_model_meta("API_SCHEMA_CASE", model=model, default="camel"))

    parent = kwargs.get("parent")
    parent_name = parent.__name__ if parent else ""
    if parent_name:
        parent_name = convert_case(
            parent_name,
            get_config_or_model_meta("API_SCHEMA_CASE", model=parent, default="camel"),
        )

    if http_method == "GET":
        if parent and many:
            return f"Returns a list of `{name}` for a specific `{parent_name}`"
        elif parent and not many:
            return f"Get a `{name}` by id for a specific `{parent_name}`."
        elif many:
            return f"Returns a list of `{name}`"
        else:
            return f"Get a `{name}` by id."
    elif http_method == "POST":
        return f"Create a new `{name}`."
    elif http_method in ["PUT", "PATCH"]:
        return f"Update an existing `{name}`."
    elif http_method == "DELETE":
        return f"Delete a `{name}` by id."
    else:
        return "Endpoint description not available"


def generate_fields_description(schema: Schema) -> str:
    """Generates fields description from a schema for the API docs.

    Args:
        schema (Schema): Schema to generate fields description from.

    Returns:
        str: Fields description.
    """

    if callable(schema):
        schema = schema()

    fields = [(k, v.metadata.get("description", "")) for k, v in schema.fields.items() if v and v.dump_only is False and not isinstance(v, RelatedList | Related)]

    if hasattr(schema, "Meta") and hasattr(schema.Meta, "model"):
        resource_name = schema.Meta.model.__name__
        example_table = [
            "OtherTable.name",
            "OtherTable.age",
            "OtherTable.id",
            "OtherTable.email",
        ]
        example_fields = [get_table_name(i, resource_name, fields, example_table) for i in range(3)]

        full_path = os.path.join(get_html_path(), "redoc_templates/fields.html")
        schema_name = endpoint_namer(schema.Meta.model)
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")

        return manual_render_absolute_template(
            full_path,
            schema_name=schema_name,
            api_prefix=api_prefix,
            fields=fields,
            example_fields=example_fields,
        )

    return "None"


def generate_x_description(template_data: dict, path: str = "") -> str:
    """Generates filter examples from a model.

    Args:
        template_data (dict): Template data to generate filter examples from.
        path (str): Path to the template.

    Returns:
        str: Filter examples.
    """
    if template_data:
        full_path = os.path.join(get_html_path(), path)
        return manual_render_absolute_template(full_path, **template_data)
    else:
        return "This endpoint does not have a database table (or is computed etc) and should not be filtered\n"


def generate_filter_examples(schema: Schema) -> str:
    """Generates filter examples from a model.

    Args:
        schema (Schema): Schema to generate filter examples from.

    Returns:
        str: Filter examples.
    """
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    day_before_yesterday = yesterday - timedelta(days=1)

    example_values = generate_example_values(now, yesterday, day_before_yesterday)
    operators = generate_operators()

    examples = generate_operator_examples(schema, operators, example_values)

    split_examples = len(examples) // 3
    example_one = "&".join(examples[:split_examples])
    example_two = "&".join(examples[-split_examples:])

    full_path = os.path.join(get_html_path(), "redoc_templates/filters.html")

    return manual_render_absolute_template(full_path, examples=[example_one, example_two])


def convert_path_to_openapi(path: str) -> str:
    """Converts a Flask path to an OpenAPI path.

    Args:
        path (str): Flask path to convert.

    Returns:
        str: OpenAPI path with Flask converters removed.
    """
    pattern = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")
    # Replace Flask path converters with OpenAPI-style parameters
    return pattern.sub(r"{\1}", path)


def initialize_spec_template(
    method: str,
    many: bool = False,
    rate_limit: bool = False,
    error_responses: list[int] | None = None,
    links: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Initialises the spec template with optional rate limiting headers for successful and rate-limited responses.

    Args:
        method (str): The HTTP method.
        many (bool): Whether the endpoint returns multiple items.
        rate_limit (bool): Whether the endpoint has a rate limit.
        error_responses (Optional[List[int]]): List of error response status codes.
        links (Optional[Dict[int, Dict[str, Any]]]): Links for specific error responses.

    Returns:
        Dict[str, Any]: Spec template.
    """
    if not error_responses:
        error_responses = []

    if links is None:
        raw_links = get_config_or_model_meta("links", default={}, method=method)
        links = {int(k): v for k, v in raw_links.items()} if raw_links else {}

    responses = _initialize_base_responses(method, many, error_responses, links)
    responses.update(_initialize_auth_responses(error_responses, links))
    responses.update(_initialize_rate_limit_responses(rate_limit))

    return {"responses": responses, "parameters": []}


def initialise_spec_template(
    method: str,
    many: bool = False,
    rate_limit: bool = False,
    error_responses: list[int] | None = None,
    links: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """UK spelling wrapper for ``initialize_spec_template``.

    Mirrors arguments and behaviour; provided for naming consistency.
    """
    return initialize_spec_template(
        method,
        many=many,
        rate_limit=rate_limit,
        error_responses=error_responses,
        links=links,
    )


def append_parameters(
    spec_template: dict[str, Any],
    query_params: list[dict[str, Any]],
    path_params: list[dict[str, Any]],
    http_method: str,
    input_schema: Schema | None = None,
    output_schema: Schema | None = None,
    model: DeclarativeBase | None = None,
    many: bool = False,
):
    """Enhances a spec template with parameters, request bodies, and responses for API documentation.

    Args:
        spec_template (Dict[str, Any]): The OpenAPI specification template to enhance.
        query_params (List[Dict[str, Any]]): A list of dictionaries defining query parameters.
        path_params (List[Dict[str, Any]]): A list of dictionaries defining path parameters.
        http_method (str): The HTTP method (GET, POST, PUT, DELETE, PATCH).
        input_schema (Optional[Schema]): The Marshmallow schema for request body validation.
        output_schema (Optional[Schema]): The Marshmallow schema for response data serialisation.
        model (Optional[DeclarativeBase]): The SQLAlchemy model for database interactions.
        many (bool): Whether the endpoint returns multiple items.

    Returns:
        None
    """

    spec_template.setdefault("parameters", []).extend(path_params + query_params)
    rate_limit = get_config_or_model_meta(
        "API_RATE_LIMIT",
        model=model,
        input_schema=input_schema,
        output_schema=output_schema,
        default=False,
    )

    if rate_limit:
        description = spec_template.get("description", "")
        spec_template["description"] = f"{description}\n**Rate Limited** - requests on this endpoint are limited to `{rate_limit}`."

    if input_schema:
        _add_request_body_to_spec_template(spec_template, http_method, input_schema, model)

    if output_schema:
        _add_response_to_spec_template(spec_template, output_schema)

    if http_method == "GET" and model and many and get_config_or_model_meta("API_ALLOW_FILTERS", model=model, default=True):
        spec_template["parameters"].append(
            {
                "name": "filters",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_filter_examples(output_schema),
            }
        )

        template_data = get_template_data_for_model(output_schema)
        spec_template["parameters"].extend(make_endpoint_params_description(output_schema, template_data))

    # Conditionally include common error responses:
    # - 400: input validation errors or invalid query/pagination/filter params
    # - 422: create/update integrity/type errors
    # These are added only when relevant features are in play.
    responses = spec_template.setdefault("responses", {})

    # 400 Bad Request
    should_include_400 = False
    # Include when request body validation exists
    if input_schema is not None:
        should_include_400 = True
    # Include for GET collection routes where filtering/ordering/join/grouping is enabled
    if http_method == "GET" and many and model is not None:
        if (
            get_config_or_model_meta("API_ALLOW_FILTERS", model=model, default=True)
            or get_config_or_model_meta("API_ALLOW_ORDER_BY", model=model, default=True)
            or get_config_or_model_meta("API_ALLOW_JOIN", model=model, default=False)
            or get_config_or_model_meta("API_ALLOW_GROUPBY", model=model, default=False)
            or get_config_or_model_meta("API_ALLOW_AGGREGATION", model=model, default=False)
        ):
            should_include_400 = True
        else:
            # Even without extra features, pagination param validation may raise 400
            should_include_400 = True
    if should_include_400 and "400" not in responses:
        responses["400"] = build_error_response(400)

    # 422 Unprocessable Entity for write operations using auto CRUD
    if model is not None and http_method in {"POST", "PUT", "PATCH"} and "422" not in responses:
        responses["422"] = build_error_response(422)

    add_auth_to_spec(model, spec_template)


def add_auth_to_spec(model: DeclarativeBase, spec_template: dict[str, Any]):
    """Adds authentication information to the spec template.

    Args:
        model (DeclarativeBase): The SQLAlchemy model.
        spec_template (Dict[str, Any]): The OpenAPI specification template to enhance.

    Returns:
        None
    """
    auth_on = get_config_or_model_meta("API_AUTHENTICATE", model=model, default=False)
    auth_type = get_config_or_model_meta("API_AUTHENTICATE_METHOD", model=model, default=None)

    if not auth_on:
        return

    spec_template.setdefault("security", [])
    spec_template.setdefault("components", {}).setdefault("securitySchemes", {})

    if auth_type == "basic":
        spec_template["security"].append({"basicAuth": []})
        spec_template["components"]["securitySchemes"]["basicAuth"] = {
            "type": "http",
            "scheme": "basic",
            "description": "Basic Authentication. Credentials must be provided as a Base64-encoded string in the format `username:password` in the `Authorization` header.",
        }
    elif auth_type == "jwt":
        spec_template["security"].append({"bearerAuth": []})
        spec_template["components"]["securitySchemes"]["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Authentication. A valid JWT must be sent in the `Authorization` header as `Bearer <token>`.",
        }
    elif auth_type == "api_key":
        api_key_location = "header"
        api_key_name = "X-API-KEY"
        spec_template["security"].append({"apiKeyAuth": []})
        spec_template["components"]["securitySchemes"]["apiKeyAuth"] = {
            "type": "apiKey",
            "in": api_key_location,
            "name": api_key_name,
            "description": f"API Key Authentication. An API key must be sent in the `{api_key_name}` {api_key_location}.",
        }


def make_endpoint_params_description(schema: Schema, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Generates endpoint parameters description from a schema for the API docs.

    Args:
        schema (Schema): Schema to generate endpoint parameters description from.
        data (Dict[str, Any]): Data to generate endpoint parameters description from.

    Returns:
        List[Dict[str, Any]]: Endpoint parameters description.
    """
    params = []

    if get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", getattr(schema.Meta, "model", None), default=True):
        params.append(
            {
                "name": "fields",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_fields_description(schema),
            }
        )

    if get_config_or_model_meta("API_ALLOW_ORDER_BY", getattr(schema.Meta, "model", None), default=True):
        params.append(
            {
                "name": "order by",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(data, "redoc_templates/order.html"),
            }
        )

    if get_config_or_model_meta("API_ALLOW_JOIN", getattr(schema.Meta, "model", None), default=False):
        params.append(
            {
                "name": "join",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(data, "redoc_templates/joins.html"),
            }
        )

    if get_config_or_model_meta("API_ALLOW_GROUPBY", getattr(schema.Meta, "model", None), default=False):
        params.append(
            {
                "name": "groupby",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(data, "redoc_templates/group.html"),
            }
        )

    if get_config_or_model_meta("API_ALLOW_AGGREGATION", getattr(schema.Meta, "model", None), default=False):
        params.append(
            {
                "name": "aggregation",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(data, "redoc_templates/aggregate.html"),
            }
        )

    return params


def handle_authorization(f: Callable, spec_template: dict[str, Any]):
    """Handles authorization in the documentation.

    Args:
        f (Callable): The function to handle authorization for.
        spec_template (Dict[str, Any]): The OpenAPI specification template to enhance.

    Returns:
        None
    """
    required_roles: tuple[str, ...] | None = None
    roles_label: str | None = None

    if hasattr(f, "_decorators"):
        for decorator in f._decorators:
            if decorator.__name__ in {
                "roles_required",
                "roles_accepted",
                "require_roles",
            }:
                required_roles = decorator._args
                any_of = getattr(decorator, "_any_of", decorator.__name__ == "roles_accepted")
                roles_label = "Roles accepted" if any_of else "Roles required"
                security = spec_template.setdefault("security", [])
                if not any("bearerAuth" in scheme for scheme in security):
                    security.append({"bearerAuth": []})
                break

    if required_roles and roles_label:
        roles_desc = ", ".join(required_roles)
        # Ensure a 401 response exists; some routes may not have auth_on enabled
        # but still declare role decorators for documentation. Initialise safely.
        responses = spec_template.setdefault("responses", {})
        if "401" not in responses:
            responses["401"] = build_error_response(401)
        responses["401"]["description"] = (
            (responses["401"].get("description") or "Unauthorized") + f" {roles_label}: {roles_desc}."
        )


def handle_authorisation(f: Callable, spec_template: dict[str, Any]):
    """UK spelling wrapper for ``handle_authorization``."""
    return handle_authorization(f, spec_template)


def get_openapi_meta_data(field_obj: fields.Field) -> dict[str, Any]:
    """Convert a Marshmallow field to an OpenAPI type.

    Args:
        field_obj (fields.Field): The Marshmallow field to convert.

    Returns:
        Dict[str, Any]: The OpenAPI metadata for the field.
    """
    openapi_type_info = {}
    field_type = type(field_obj)

    if hasattr(field_obj, "parent") and hasattr(field_obj.parent, "Meta") and hasattr(field_obj.parent.Meta, "model"):
        openapi_type_info = get_description_and_example_add(openapi_type_info, field_obj)

    openapi_type_info["type"] = type_mapping.get(field_type, "string")

    # Populate example with sensible defaults when none provided
    if "example" not in openapi_type_info and (example := _resolve_default_example(field_type)):
        openapi_type_info["example"] = example

    if field_type in [fields.DateTime, fields.Date, fields.Time]:
        openapi_type_info["format"] = "date-time" if field_type == fields.DateTime else field_type.__name__.lower()

    if field_type == fields.Decimal and (fmt := field_obj.metadata.get("format")):
        # Add optional format for Decimal fields if provided in metadata
        openapi_type_info["format"] = fmt

    if field_type == fields.Function:
        openapi_type_info["format"] = "uri"
        openapi_type_info["example"] = "/url/to/resource"

    if field_type == fields.List:
        openapi_type_info["items"] = get_openapi_meta_data(field_obj.inner)

    if field_type in [Nested, Related, RelatedList]:
        related_schema_name = get_related_schema_name(field_obj, field_type)
        if related_schema_name:
            openapi_type_info = handle_nested_related_fields(field_obj, field_type, related_schema_name, openapi_type_info)

    return openapi_type_info


def get_related_schema_name(field_obj: fields.Field, field_type: type) -> str | None:
    """Determine the schema name referenced by a nested or related field.

    Args:
        field_obj (fields.Field): Field instance whose schema is being resolved.
        field_type (type): Concrete class of ``field_obj`` such as ``Nested``,
            ``Related`` or ``RelatedList``.

    Returns:
        str | None: The related schema name converted using
        ``API_SCHEMA_CASE`` (default ``"camel"``). ``None`` is returned when

    """
    if field_type == Nested:
        schema_cls = field_obj.schema.__class__
        model = getattr(schema_cls.Meta, "model", None)
        name = schema_cls.__name__
    elif field_type in [Related, RelatedList]:
        parent_model = field_obj.parent.Meta.model
        related_model = getattr(parent_model, field_obj.name).property.mapper.class_
        model = related_model
        name = f"{related_model.__name__}Schema"
    else:
        return None

    case = get_config_or_model_meta("API_SCHEMA_CASE", model=model, default="camel") or "camel"
    return convert_case(name.replace("Schema", ""), case)


def handle_nested_related_fields(
    field_obj: fields.Field,
    field_type: type,
    related_schema_name: str,
    openapi_type_info: dict[str, Any],
) -> dict[str, Any]:
    """Populate OpenAPI metadata for nested and related fields.

    Args:
        field_obj (fields.Field): Field being processed.
        field_type (type): Class of ``field_obj``.
        related_schema_name (str): Name of the referenced schema.
        openapi_type_info (dict[str, Any]): Existing OpenAPI snippet to
            mutate.

    Returns:
        dict[str, Any]: Updated OpenAPI metadata. When the field represents a
        collection (``many=True`` or ``RelatedList``), ``type`` is set to
        ``"array"`` with ``items`` referencing the related schema. Otherwise a
        direct ``$ref`` is applied.
    """
    if field_obj.many or field_type == RelatedList:
        openapi_type_info["type"] = "array"
        openapi_type_info["items"] = {"$ref": f"#/components/schemas/{related_schema_name}"}
    else:
        openapi_type_info["$ref"] = f"#/components/schemas/{related_schema_name}"
    return openapi_type_info


def get_description_and_example_add(openapi_type_info: dict[str, Any], field_obj: fields.Field) -> dict[str, Any]:
    """Attach description and example metadata defined on a model field.

    Args:
        openapi_type_info (dict[str, Any]): OpenAPI fragment to enrich.
        field_obj (fields.Field): Marshmallow field whose underlying SQLAlchemy
            column may define ``info`` with ``description`` or ``example``
            entries.

    Returns:
        dict[str, Any]: The modified ``openapi_type_info``. If the model field
        lacks relevant metadata the input is returned unchanged.

    """
    model_field = getattr(field_obj.parent.Meta.model, field_obj.name, None)
    if model_field and hasattr(model_field, "info"):
        model_field_metadata = model_field.info
        if description := model_field_metadata.get("description"):
            openapi_type_info["description"] = description
        if example := model_field_metadata.get("example"):
            openapi_type_info["example"] = example
    return openapi_type_info


type_mapping = {
    fields.String: "string",
    fields.Integer: "integer",
    fields.Float: "number",
    fields.Decimal: "number",
    fields.Boolean: "boolean",
    fields.DateTime: "string",
    fields.Date: "string",
    fields.Time: "string",
    fields.UUID: "string",
    fields.URL: "string",
    fields.Function: "string",
    fields.Nested: "object",
    fields.Email: "string",
    fields.Dict: "object",
    fields.List: "array",
    Related: "object",
    RelatedList: "array",
}


example_fallbacks = {
    fields.Integer: 1,
    fields.Float: 1.23,
    fields.Decimal: 9.99,
    fields.Boolean: True,
}


def _resolve_default_example(field_type: type[fields.Field]) -> Any | None:
    """Return default example for a field type.

    Args:
        field_type: Marshmallow field class to resolve an example for.

    Returns:
        The configured example value, or ``None`` if no default exists.
    """

    defaults = example_fallbacks.copy()
    try:
        overrides = get_config_or_model_meta("OPENAPI_FIELD_EXAMPLE_DEFAULTS", default={})
    except RuntimeError:
        overrides = {}
    if isinstance(overrides, dict):
        for key, value in overrides.items():
            override_cls = getattr(fields, key, None)
            if isinstance(override_cls, type) and issubclass(override_cls, fields.Field):
                defaults[override_cls] = value
    return defaults.get(field_type)


def get_description(kwargs: dict[str, Any]) -> str:
    """Return a human-readable description for an endpoint.

    Args:
        kwargs (dict[str, Any]): Context options. Recognised keys include:
            ``model`` or ``child_model`` (type[DeclarativeBase]): Models used to
                derive the description.
            ``parent_model`` (type[DeclarativeBase], optional): Required when
                ``child_model`` is supplied.
            ``name`` (str): Resource name used in fallback text.
            ``method`` (str): HTTP method in uppercase.
            ``multiple`` (bool, optional): Whether the endpoint returns multiple
                resources. Defaults to ``False``.

    Returns:
        str: Description sourced from ``model.Meta.description`` or a default
        string based on ``method``. An empty string is returned when no
        description can be determined.
    """
    model = kwargs.get("model", kwargs.get("child_model"))
    name, method = kwargs["name"], kwargs["method"]

    if "child_model" in kwargs:
        parent = kwargs["parent_model"]
        return f"Get multiple `{name}` records from the database based on the parent {endpoint_namer(parent)} id"

    description = getattr(model.Meta, "description", {}).get(method) if hasattr(model, "Meta") else None
    if description:
        return description

    default_descriptions = {
        "DELETE": f"Delete a single `{name}` in the database by its id",
        "PATCH": f"Patch (update) a single `{name}` in the database.",
        "POST": f"Post (create) a single `{name}` in the database.",
        "GET": f"Get {'multiple' if kwargs.get('multiple', False) else 'a single'} `{name}` record(s) from the database",
    }
    return default_descriptions.get(method, "")


def get_tag_group(kwargs: dict[str, Any]) -> str | None:
    """Retrieve the ``x-tagGroup`` value for a route.

    Args:
        kwargs (dict[str, Any]): Keyword arguments containing ``model`` or
            ``child_model``.

    Returns:
        str | None: Value of ``Meta.tag_group`` if defined; otherwise ``None``.
    """
    model = kwargs.get("model", kwargs.get("child_model"))
    return getattr(model.Meta, "tag_group", None) if hasattr(model, "Meta") else None


def endpoint_namer(
    model: type[DeclarativeBase] | None = None,
    input_schema: type[Schema] | None = None,
    output_schema: type[Schema] | None = None,
) -> str:
    """Generate a pluralised endpoint name for a model.

    Args:
        model (type[DeclarativeBase] | None): Model used to derive the name.
            This parameter is required; the schema parameters are reserved for
            future use.
        input_schema (type[Schema] | None, optional): Unused placeholder to
            match a common function signature.
        output_schema (type[Schema] | None, optional): Unused placeholder to
            match a common function signature.

    Returns:
        str: Endpoint name converted using ``API_ENDPOINT_CASE`` (default
        ``"kebab"``) and pluralised.
    """
    model_obj = model
    if model_obj is None:
        schema = input_schema or output_schema
        model_obj = getattr(getattr(schema, "Meta", None), "model", None) if schema else None
    if model_obj is None:
        raise ValueError("A model or schema with a Meta.model attribute is required")

    # Read directly from Flask config to avoid cross-test bleed-through from
    # model metadata on plain classes. Defaults to kebab-case for endpoints.
    case = get_config_or_model_meta("API_ENDPOINT_CASE", default="kebab") or "kebab"
    converted_name = convert_case(model_obj.__name__, case)
    pluralized_name = pluralize_last_word(converted_name)
    return convert_case(pluralized_name, case)
