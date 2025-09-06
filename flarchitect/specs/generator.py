from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.common import make_schema_key, resolve_schema_instance
from flask import Blueprint, Flask, Response, current_app, redirect, request, session
from flask_login import current_user, login_user
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase

from flarchitect.core.routes import (
    create_params_from_rule,
    create_query_params_from_rule,
    find_rule_by_function,
)
from flarchitect.logging import logger
from flarchitect.specs.utils import (
    append_parameters,
    convert_path_to_openapi,
    handle_authorisation,
    initialise_spec_template,
    schema_name_resolver,
    scrape_extra_info_from_spec_data,
)
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.general import (
    AttributeInitialiserMixin,
    generate_readme_html,
    get_html_path,
    make_base_dict,
    manual_render_absolute_template,
    pretty_print_dict,
    search_all_keys,
)
from flarchitect.utils.response_helpers import create_response

if TYPE_CHECKING:  # pragma: no cover - imported only for type hints
    from flarchitect import Architect


class CustomSpec(APISpec, AttributeInitialiserMixin):
    """A subclass of APISpec for specifying tag groups with extended features."""

    app: Flask
    architect: Architect  # The architect object

    spec_groups: dict[str, list[dict[str, str | list[str]]]] | None = None
    api_title: str | None = ""
    api_version: str | None = ""
    api_description: str | None = None
    api_logo_url: str | None = None
    api_logo_background: str | None = None
    api_keywords: list[str] | None = None
    create_docs: bool | None = True
    documentation_url_prefix: str | None = None
    documentation_url: str | None = "/docs"

    def __init__(self, app: Flask, architect: Architect, *args, **kwargs):
        """Initialises the CustomSpec object.

        Args:
            app (Flask): The Flask application.
            architect (Architect): The Architect object.
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
        """
        self.app = app
        self.architect = architect
        # initialise per-instance containers to avoid shared mutable defaults
        self.spec_groups: dict[str, list[dict[str, str | list[str]]]] = {"x-tagGroups": []}
        self.api_keywords: list[str] = []
        super().__init__(*args, **self._prepare_api_spec_data(**kwargs))

        # Reset MarshmallowPlugin schema refs to avoid cross-app/test bleed.
        import contextlib
        with contextlib.suppress(Exception):
            plugin = next((p for p in self.plugins if isinstance(p, MarshmallowPlugin)), None)
            if plugin and getattr(getattr(plugin, "converter", None), "refs", None) is not None:
                plugin.converter.refs.clear()  # type: ignore[attr-defined]

        if self._should_create_docs():
            self.architect.api_spec = self
            self._create_specification_blueprint()
            register_routes_with_spec(self.architect, self.architect.route_spec)

    def to_dict(self) -> dict:
        """Converts the API specification to a dictionary.

        Returns:
            dict: The API specification as a dictionary.
        """
        # Notify plugins that spec build is starting/completing
        import contextlib
        with contextlib.suppress(Exception):
            self.architect.plugins.spec_build_started(self)
        spec_dict = super().to_dict()
        with contextlib.suppress(Exception):
            maybe = self.architect.plugins.spec_build_completed(spec_dict)
            if isinstance(maybe, dict):
                spec_dict = maybe
        if self.spec_groups:
            spec_dict.update(self.spec_groups)
        return spec_dict

    def _prepare_api_spec_data(self, **kwargs) -> dict:
        """Prepares the data required to initialise the API spec.

        Returns:
            dict: Data for initialising the API spec.
        """
        api_description = self._get_api_description()
        api_spec_data = {
            "openapi_version": "3.0.2",
            "plugins": [MarshmallowPlugin(schema_name_resolver=schema_name_resolver)],
            "title": self._get_config("API_TITLE", "My API"),
            "version": self._get_config("API_VERSION", "1.0.0"),
            "info": {
                "description": api_description,
                **self._get_contact_info(),
                **self._get_license_info(),
                **self._get_logo_info(),
            },
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                }
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
        contact_info = {k: self._get_config(f"API_CONTACT_{k.upper()}") for k in ["name", "email", "url"]}
        return {"contact": {k: v for k, v in contact_info.items() if v}} if any(contact_info.values()) else {}

    def _get_license_info(self) -> dict[str, dict[str, str | None]]:
        """Retrieves license information for the API spec.

        Returns:
            dict: A dictionary containing the license information.
        """
        license_info = {k: self._get_config(f"API_LICENCE_{k.upper()}") for k in ["name", "url"]}
        return {"license": {k: v for k, v in license_info.items() if v}} if any(license_info.values()) else {}

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
                    "backgroundColor": self._get_config("API_LOGO_BACKGROUND", "#ffffff"),
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
        """Validates the initialisation arguments for the API spec.

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
        if self.spec_groups is None:
            self.spec_groups = {"x-tagGroups": []}

        tag_groups = self.spec_groups.setdefault("x-tagGroups", [])

        for group in tag_groups:
            if group["name"] == group_name:
                if tag_name not in group["tags"]:
                    group["tags"].append(tag_name)
                return
        tag_groups.append({"name": group_name, "tags": [tag_name]})

    def _create_specification_blueprint(self) -> None:
        """Sets up the blueprint to serve the API specification and documentation.

        The HTML template directory is resolved dynamically using
        :func:`~flarchitect.utils.general.get_html_path` to avoid reliance on
        global state.
        """

        html_path = get_html_path()

        specification = Blueprint(
            "specification",
            __name__,
            static_folder=html_path,
            url_prefix=self.documentation_url_prefix or self._get_config("DOCUMENTATION_URL_PREFIX", "/"),
        )

        documentation_url = get_config_or_model_meta("API_DOCUMENTATION_URL", default="/docs")
        docs_password = get_config_or_model_meta("API_DOCUMENTATION_PASSWORD", default=None)
        docs_require_auth = get_config_or_model_meta("API_DOCUMENTATION_REQUIRE_AUTH", default=False)
        auth_method = get_config_or_model_meta("API_AUTHENTICATE_METHOD", default=None)
        user_model = get_config_or_model_meta("API_USER_MODEL", default=None)

        def _ensure_docs_access(
            json_only: bool = False,
        ) -> Response | tuple[str, int] | None:
            """Validate optional documentation authentication.

            Args:
                json_only (bool): When ``True`` return a JSON error response instead of HTML.

            Returns:
                Optional[Union[Response, tuple[str, int]]]: ``None`` if access is granted, otherwise a response prompting for login.
            """

            if not (docs_password or docs_require_auth):
                return None

            if session.get("docs_authenticated") or getattr(current_user, "is_authenticated", False):
                return None

            if request.method == "POST" and not json_only:
                username = request.form.get("username")
                password = request.form.get("password", "")

                if docs_password and password == docs_password:
                    session["docs_authenticated"] = True
                    return redirect(request.path)

                if auth_method and user_model and username and password:
                    lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD", model=user_model, default=None)
                    check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", model=user_model, default=None)
                    usr = user_model.query.filter(getattr(user_model, lookup_field) == username).first()
                    if usr and getattr(usr, check_method)(password):
                        session["docs_authenticated"] = True
                        login_user(usr)
                        return redirect(request.path)

                error = "Invalid credentials"
            else:
                error = None

            if json_only:
                return create_response(status=401, errors="Unauthorized")

            docs_style = get_config_or_model_meta("API_DOCS_STYLE", default="redoc").lower()
            allow_username = bool(auth_method and user_model)
            html = manual_render_absolute_template(
                os.path.join(self.architect.get_templates_path(), "docs_login.html"),
                config=self.app.config,
                docs_style=docs_style,
                allow_username=allow_username,
                error=error,
            )
            return html, 200

        # Determine the JSON spec route under the docs path
        docs_json_url = get_config_or_model_meta(
            "API_DOCS_SPEC_ROUTE",
            default=f"{(documentation_url or '/docs').rstrip('/')}/apispec.json",
        )

        @specification.route(docs_json_url)
        def get_swagger_spec() -> dict | Response | tuple[str, int]:
            """Serve the Swagger spec as JSON.

            Returns:
                Union[dict, Response, tuple[str, int]]: The Swagger spec or an authentication response.
            """

            unauthorized = _ensure_docs_access(json_only=True)
            if unauthorized:
                return unauthorized
            return self.architect.to_api_spec()

        # Backwards-compatibility: legacy endpoints still serve the same content
        @specification.route("apispec.json")
        def get_legacy_apispec() -> dict | Response | tuple[str, int]:  # pragma: no cover
            return get_swagger_spec()

        @specification.route("swagger.json")
        def get_legacy_swagger_spec() -> dict | Response | tuple[str, int]:
            """Serve the Swagger spec at legacy ``swagger.json`` endpoint."""

            return get_swagger_spec()

        get_swagger_spec._auth_disabled = True

        @specification.route(documentation_url, methods=["GET", "POST"])
        @specification.route(documentation_url + "/", methods=["GET", "POST"])
        def get_docs() -> str | Response | tuple[str, int]:
            """Serve the API documentation page.

            Returns:
                Union[str, Response, tuple[str, int]]: HTML documentation or an authentication response.
            """

            unauthorized = _ensure_docs_access()
            if unauthorized:
                return unauthorized

            custom_headers = get_config_or_model_meta("API_DOCUMENTATION_HEADERS", default="") or self._get_config("API_DOC_HTML_HEADERS", "")
            docs_style = get_config_or_model_meta("API_DOCS_STYLE", default="redoc").lower()

            template_name = "swagger.html" if docs_style == "swagger" else "apispec.html"
            return manual_render_absolute_template(
                os.path.join(self.architect.get_templates_path(), template_name),
                config=self.app.config,
                custom_headers=custom_headers,
            )

        get_docs._auth_disabled = True

        self.architect.app.register_blueprint(specification)

        prefix = self.documentation_url_prefix or self._get_config("DOCUMENTATION_URL_PREFIX", "/")
        docs_url = documentation_url if documentation_url.startswith("/") else f"/{documentation_url}"
        full_url = f"{prefix.rstrip('/')}{docs_url}"
        server_name = self.app.config.get("SERVER_NAME")
        if server_name:
            full_url = f"http://{server_name}{full_url}"
        logger.log(1, f"API documentation available at |{full_url}|")


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
    spec_template = initialise_spec_template(http_method, many, rate_limit, error_responses)

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
    handle_authorisation(f, spec_template)

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

    # ``MarshmallowPlugin`` keeps track of registered schemas. Inspect the
    # plugin to avoid adding the same schema class twice, which would trigger
    # warnings from ``apispec``.
    plugin = next((p for p in spec.plugins if isinstance(p, MarshmallowPlugin)), None)
    registered_refs = getattr(getattr(plugin, "converter", None), "refs", {}) if plugin else {}

    for schema in [input_schema, output_schema]:
        if schema:
            schema_instance = resolve_schema_instance(schema)
            schema_name = schema_name_resolver(schema_instance)

            schema_key = make_schema_key(schema_instance)
            existing_ref = registered_refs.get(schema_key)
            if existing_ref and not force_update:
                if existing_ref != schema_name:
                    spec.components.schemas[schema_name] = spec.components.schemas.pop(existing_ref)
                    registered_refs[schema_key] = schema_name
                continue

            existing_schema = spec.components.schemas.get(schema_name)
            if existing_schema and force_update:
                spec.components.schemas[schema_name] = schema_instance
            elif not existing_schema:
                spec.components.schema(schema_name, schema=schema_instance)

            registered_refs[schema_key] = schema_name


def register_routes_with_spec(architect: Architect, route_spec: list[dict[str, Any]] | None = None) -> None:
    """Register routes and schemas with the API spec.

    Args:
        architect: The :class:`~flarchitect.Architect` instance.
        route_spec: Optional list of routes and schemas to register with the
            apispec. Defaults to no action when ``None`` or empty.

    Returns:
        None
    """

    if not route_spec:
        return

    for route_info in route_spec:
        with architect.app.test_request_context():
            f = route_info["function"]
            rule = find_rule_by_function(architect, f)

            if rule:
                methods = rule.methods - {"OPTIONS", "HEAD"}
                for http_method in methods:
                    summary = route_info.get("summary")
                    route_info = scrape_extra_info_from_spec_data(route_info, method=http_method, summary=summary)
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
                    final_query_params = create_query_params_from_rule(rule, methods, output_schema, many, model, custom_query_params)

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
                    if not any(t.get("name") == tag for t in architect.api_spec._tags):
                        architect.api_spec.tag({"name": tag})

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
