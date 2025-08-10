import os
from collections.abc import Callable
from typing import Any

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Blueprint, Flask, current_app
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase

from flarchitect.core.routes import (
    create_params_from_rule,
    create_query_params_from_rule,
    find_rule_by_function,
)
from flarchitect.specs.utils import (
    _prepare_patch_schema,
    append_parameters,
    convert_path_to_openapi,
    handle_authorization,
    initialize_spec_template,
    scrape_extra_info_from_spec_data,
)
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case
from flarchitect.utils.general import (
    AttributeInitializerMixin,
    find_child_from_parent_dir,
    generate_readme_html,
    make_base_dict,
    manual_render_absolute_template,
    pretty_print_dict,
    search_all_keys,
)


class CustomSpec(APISpec, AttributeInitializerMixin):
    """A subclass of APISpec for specifying tag groups with extended features."""

    app: Flask
    architect: "Architect"  # The architect object

    spec_groups: dict[str, list[dict[str, str | list[str]]]] = {"x-tagGroups": []}
    api_title: str | None = ""
    api_version: str | None = ""
    api_description: str | None = None
    api_logo_url: str | None = None
    api_logo_background: str | None = None
    api_keywords: list[str] | None = []
    create_docs: bool | None = True
    documentation_url_prefix: str | None = "/"
    documentation_url: str | None = "/docs"

    def __init__(self, app: Flask, architect: "Architect", *args, **kwargs):
        """Initializes the CustomSpec object.

        Args:
            app (Flask): The Flask application.
            architect (Architect): The Architect object.
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
        """
        self.app = app
        self.architect = architect
        super().__init__(*args, **self._prepare_api_spec_data(**kwargs))

        if self._should_create_docs():
            self.architect.api_spec = self
            self._create_specification_blueprint()
            register_routes_with_spec(self.architect, self.architect.route_spec)

    def to_dict(self) -> dict:
        """Converts the API specification to a dictionary.

        Returns:
            dict: The API specification as a dictionary.
        """
        spec_dict = super().to_dict()
        spec_dict.update(self.spec_groups)
        return spec_dict

    def _prepare_api_spec_data(self, **kwargs) -> dict:
        """Prepares the data required to initialize the API spec.

        Returns:
            dict: Data for initializing the API spec.
        """
        api_description = self._get_api_description()
        api_spec_data = {
            "openapi_version": "3.0.2",
            "plugins": [MarshmallowPlugin()],
            "title": self._get_config("API_TITLE", "My API"),
            "version": self._get_config("API_VERSION", "1.0.0"),
            "info": {
                "description": api_description,
                **self._get_contact_info(),
                **self._get_license_info(),
                **self._get_logo_info(),
            },
            **self._get_servers_info(),
        }
        return {**api_spec_data, **kwargs}

    def _get_api_description(self) -> str:
        """Generates API description in HTML format.

        Returns:
            str: The API description in HTML format.
        """
        desc_path = get_config_or_model_meta(
            "API_DESCRIPTION",
            default=os.path.join(self.architect.get_templates_path(), "base_readme.MD"),
        )
        if os.path.isfile(desc_path):
            base_model = get_config_or_model_meta("API_BASE_MODEL")
            return generate_readme_html(
                desc_path,
                config=self.architect.app.config,
                api_output_example=pretty_print_dict(make_base_dict()),
                has_rate_limiting=search_all_keys(base_model, "API_RATE_LIMIT"),
                has_auth=search_all_keys(base_model, "API_AUTHENTICATE_METHOD"),
            )
        return desc_path

    def _get_config(self, key: str, default: str | None = None) -> str | None:
        """Fetches configuration or model metadata.

        Args:
            key (str): The configuration key to retrieve.
            default (Optional[str]): Default value if key not found.

        Returns:
            Optional[str]: The value for the given configuration key.
        """
        return get_config_or_model_meta(key, default=default)

    def _get_contact_info(self) -> dict[str, dict[str, str | None]]:
        """Retrieves contact information for the API spec.

        Returns:
            dict: A dictionary containing the contact information.
        """
        contact_info = {
            k: self._get_config(f"API_CONTACT_{k.upper()}")
            for k in ["name", "email", "url"]
        }
        return (
            {"contact": {k: v for k, v in contact_info.items() if v}}
            if any(contact_info.values())
            else {}
        )

    def _get_license_info(self) -> dict[str, dict[str, str | None]]:
        """Retrieves license information for the API spec.

        Returns:
            dict: A dictionary containing the license information.
        """
        license_info = {
            k: self._get_config(f"API_LICENCE_{k.upper()}") for k in ["name", "url"]
        }
        return (
            {"license": {k: v for k, v in license_info.items() if v}}
            if any(license_info.values())
            else {}
        )

    def _get_servers_info(self) -> dict[str, list[str] | None]:
        """Retrieves server URLs for the API spec.

        Returns:
            dict: A dictionary containing server information.
        """
        servers = self._get_config("API_SERVER_URLS")
        return {"servers": servers} if servers else {}

    def _get_logo_info(self) -> dict[str, dict[str, str | None]]:
        """Retrieves logo information for the API spec.

        Returns:
            dict: A dictionary containing the logo information.
        """
        logo_url = self._get_config("API_LOGO_URL")
        if logo_url:
            return {
                "x-logo": {
                    "url": logo_url,
                    "backgroundColor": self._get_config(
                        "API_LOGO_BACKGROUND", "#ffffff"
                    ),
                    "altText": f"{self._get_config('API_TITLE', 'My API')} logo.",
                }
            }
        return {}

    def _should_create_docs(self) -> bool:
        """Determines whether to create API documentation.

        Returns:
            bool: True if documentation should be created, False otherwise.
        """
        return get_config_or_model_meta("API_CREATE_DOCS", default=True)

    def validate_init_apispec_args(self) -> None:
        """Validates the initialization arguments for the API spec.

        Raises:
            ValueError: If any required argument is invalid.
        """
        if not isinstance(self.api_title, str) or not self.api_title:
            raise ValueError("API title must be a non-empty string.")
        if not isinstance(self.api_version, str) or not self.api_version:
            raise ValueError("API version must be a non-empty string.")

    def set_xtags_group(self, tag_name: str, group_name: str) -> None:
        """Adds a tag to a tag-group, creating the group if it doesn't exist.

        Args:
            tag_name (str): The tag to add.
            group_name (str): The group to add the tag to.

        Example:
            >>> spec.set_xtags_group("Users", "Authentication")
        """
        for group in self.spec_groups["x-tagGroups"]:
            if group["name"] == group_name:
                if tag_name not in group["tags"]:
                    group["tags"].append(tag_name)
                return
        self.spec_groups["x-tagGroups"].append({"name": group_name, "tags": [tag_name]})

    def _create_specification_blueprint(self) -> None:
        """Sets up the blueprint to serve the API specification and documentation."""
        html_path = find_child_from_parent_dir(
            "src", "html", current_dir=os.path.dirname(os.path.abspath(__file__))
        )

        specification = Blueprint(
            "specification",
            __name__,
            static_folder=html_path,
            url_prefix=self.documentation_url_prefix
            or self._get_config("DOCUMENTATION_URL_PREFIX", "/"),
        )

        documentation_url = get_config_or_model_meta(
            "API_DOCUMENTATION_URL", default="/docs"
        )

        @specification.route("swagger.json")
        def get_swagger_spec() -> dict:
            """Serves the Swagger spec as JSON.

            Returns:
                dict: The Swagger spec.
            """
            return self.architect.to_api_spec()

        @specification.route(documentation_url)
        @specification.route(documentation_url + "/")
        def get_docs() -> str:
            """Serves the API documentation page.

            Returns:
                str: The HTML documentation page.
            """

            custom_headers = get_config_or_model_meta(
                "API_DOCUMENTATION_HEADERS", default=""
            ) or self._get_config("API_DOC_HTML_HEADERS", "")
            return manual_render_absolute_template(
                os.path.join(self.architect.get_templates_path(), "apispec.html"),
                config=self.app.config,
                custom_headers=custom_headers,
            )

        self.architect.app.register_blueprint(specification)


def generate_swagger_spec(
    http_method: str,
    f: Callable,
    input_schema: Schema | None = None,
    output_schema: Schema | None = None,
    model: DeclarativeBase | None = None,
    query_params: list[dict[str, Any]] | None = None,
    path_params: list[dict[str, Any]] | None = None,
    many: bool = False,
    error_responses: list[int] | None = None,
) -> dict[str, Any]:
    """Generates a Swagger spec for an endpoint.

    Args:
        http_method (str): The HTTP method.
        f (Callable): The function associated with the endpoint.
        input_schema (Optional[Schema]): The schema for the input data.
        output_schema (Optional[Schema]): The schema for the output data.
        model (Optional[DeclarativeBase]): The SQLAlchemy model.
        query_params (Optional[List[Dict[str, Any]]]): Query parameters.
        path_params (Optional[List[Dict[str, Any]]]): Path parameters.
        many (bool): Whether the endpoint returns multiple items.
        error_responses (Optional[List[int]]): List of error response status codes.

    Returns:
        Dict[str, Any]: The generated Swagger spec.
    """
    spec = current_app.extensions["flarchitect"].api_spec

    register_schemas(spec, input_schema, output_schema)
    rate_limit = get_config_or_model_meta(
        "API_RATE_LIMIT",
        model=model,
        input_schema=input_schema,
        output_schema=output_schema,
        default=False,
    )
    spec_template = initialize_spec_template(
        http_method, many, rate_limit, error_responses
    )

    append_parameters(
        spec_template,
        query_params or [],
        path_params or [],
        http_method,
        input_schema,
        output_schema,
        model,
        many,
    )
    handle_authorization(f, spec_template)

    return spec_template


def register_schemas(
    spec: APISpec,
    input_schema: Schema,
    output_schema: Schema | None = None,
    force_update: bool = False,
):
    """Registers schemas with the apispec object.

    Args:
        spec (APISpec): APISpec object to register schemas with.
        input_schema (Schema): Input schema to register.
        output_schema (Schema): Output schema to register.
        force_update (bool): If True, will update the schema even if it already exists.

    Returns:
        None
    """

    put_input_schema = _prepare_patch_schema(input_schema)

    for schema in [input_schema, output_schema, put_input_schema]:
        if schema:
            model = schema.get_model() if hasattr(schema, "get_model") else None

            schema_name = convert_case(
                schema.__name__.replace("Schema", "")
                if hasattr(schema, "__name__")
                else schema.__class__.__name__.replace("Schema", ""),
                get_config_or_model_meta(
                    "API_SCHEMA_CASE", model=model, default="camel"
                ),
            )
            schema.__name__ = schema_name

            existing_schema = spec.components.schemas.get(schema_name)
            if existing_schema and force_update:
                spec.components.schemas[schema_name] = schema
            elif not existing_schema:
                spec.components.schema(schema_name, schema=schema)


def register_routes_with_spec(architect: "Architect", route_spec: list[dict[str, Any]]):
    """Registers all flarchitect with the apispec object.

    Args:
        architect (Architect): The architect object.
        route_spec (List[Dict[str, Any]]): List of routes/schemas to register with the apispec.

    Returns:
        None
    """

    for route_info in route_spec:
        with architect.app.test_request_context():
            f = route_info["function"]
            rule = find_rule_by_function(architect, f)

            if rule:
                methods = rule.methods - {"OPTIONS", "HEAD"}
                for http_method in methods:
                    route_info = scrape_extra_info_from_spec_data(
                        route_info, method=http_method
                    )
                    path = rule.rule

                    output_schema = route_info.get("output_schema")
                    input_schema = route_info.get("input_schema")
                    model = route_info.get("model")
                    description = route_info.get("description")
                    summary = route_info.get("summary")
                    custom_query_params = route_info.get("query_params")
                    tag = route_info.get("tag")
                    many = route_info.get("multiple")
                    error_responses = route_info.get("error_responses")

                    path_params = create_params_from_rule(model, rule, output_schema)
                    final_query_params = create_query_params_from_rule(
                        rule, methods, output_schema, many, model, custom_query_params
                    )

                    endpoint_spec = generate_swagger_spec(
                        http_method,
                        f,
                        input_schema=input_schema,
                        output_schema=output_schema,
                        model=model,
                        query_params=final_query_params,
                        path_params=path_params,
                        many=many,
                        error_responses=error_responses,
                    )

                    endpoint_spec["tags"] = [tag]

                    if route_info.get("group_tag"):
                        architect.api_spec.set_xtags_group(tag, route_info["group_tag"])

                    if summary:
                        endpoint_spec["summary"] = summary
                    if description:
                        endpoint_spec["description"] = description

                    architect.api_spec.path(
                        path=convert_path_to_openapi(path),
                        operations={http_method.lower(): endpoint_spec},
                    )

    from flarchitect.schemas.bases import AutoSchema

    register_schemas(architect.api_spec, AutoSchema)
