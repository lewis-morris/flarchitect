import base64
import binascii
import importlib
import os
import re
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast

from flask import Flask, Response, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase, Session

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from flask_caching import Cache

from flarchitect.authentication.jwt import get_user_from_token
from flarchitect.authentication.user import set_current_user
from flarchitect.core.routes import RouteCreator, find_rule_by_function
from flarchitect.exceptions import CustomHTTPException
from flarchitect.logging import logger
from flarchitect.specs.generator import CustomSpec
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.decorators import handle_many, handle_one
from flarchitect.utils.general import (
    AttributeInitializerMixin,
    check_rate_services,
    validate_flask_limiter_rate_limit_string,
)
from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.session import get_session

FLASK_APP_NAME = "flarchitect"

F = TypeVar("F", bound=Callable[..., Any])


def jwt_authentication(func: F) -> F:
    """Decorator enforcing JSON Web Token (JWT) authentication.

    Args:
        func (Callable[..., Any]): The view function to wrap.

    Returns:
        Callable[..., Any]: A wrapped function that validates the request's JWT
        before executing ``func``.

    Raises:
        CustomHTTPException: If the ``Authorization`` header is missing,
        malformed, or the provided token is invalid.
    """

    @wraps(func)
    def auth_wrapped(*args: Any, **kwargs: Any) -> Any:
        """Validate a request's JWT before executing ``func``.

        Args:
            *args: Positional arguments forwarded to ``func``.
            **kwargs: Keyword arguments forwarded to ``func``.

        Returns:
            Any: The result of ``func`` if authentication succeeds.

        Raises:
            CustomHTTPException: If the Authorization header or token is
                missing or invalid.
        """

        auth = request.headers.get("Authorization")
        if not auth:
            raise CustomHTTPException(
                status_code=401, reason="Authorization header missing"
            )
        parts = auth.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise CustomHTTPException(
                status_code=401, reason="Invalid Authorization header"
            )
        token = parts[1]
        usr = get_user_from_token(token, secret_key=None)
        if not usr:
            raise CustomHTTPException(status_code=401, reason="Invalid token")
        set_current_user(usr)
        return func(*args, **kwargs)

    return cast(F, auth_wrapped)


class Architect(AttributeInitializerMixin):
    """Main orchestrator for the Flask extension.

    The ``Architect`` centralizes initialisation, route creation, API
    specification generation, caching, CORS handling, and request
    authentication. It exposes helpers and configuration that allow an
    application to be wired up with minimal boilerplate.
    """

    app: Flask
    api_spec: CustomSpec | None = None
    api: Optional["RouteCreator"] = None
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    route_spec: list[dict[str, Any]] | None = None
    limiter: Limiter
    cache: "Cache | None" = None

    def __init__(self, app: Flask | None = None, *args, **kwargs):
        """Initialise the Architect extension.

        The Flask development server runs the application twice when the
        automatic reloader is enabled. To avoid duplicate initialisation and
        the noisy log output that comes with it, setup is skipped during the
        reloader's parent process and only performed for the serving process.

        Args:
            app: The Flask application instance.
            *args: Positional arguments forwarded to :meth:`init_app`.
            **kwargs: Keyword arguments forwarded to :meth:`init_app`.
        """
        self.route_spec: list[dict[str, Any]] = []

        if app is not None:
            if self._is_reloader_start():

                logger.debug(
                    4, "Skipping Architect initialisation in reloader parent process"
                )
            else:
                self.init_app(app, *args, **kwargs)
                logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)

    @staticmethod
    def _is_reloader_start() -> bool:
        """Return ``True`` when executing in the reloader's parent process.

        Flask's development reloader spawns a supervisory process that imports
        the application before starting a child process to serve requests. The
        parent process exposes a ``WERKZEUG_SERVER_FD`` environment variable
        while the child sets ``WERKZEUG_RUN_MAIN`` to ``"true"``. By combining
        these signals we can skip one-time setup during the parent's initial
        import without affecting production deployments where neither variable
        is present.

        Returns:
            bool: ``True`` if running as the reloader parent, otherwise ``False``.
        """

        run_main = os.environ.get("WERKZEUG_RUN_MAIN")
        server_fd = os.environ.get("WERKZEUG_SERVER_FD")
        return server_fd is not None and run_main != "true"

    def init_app(self, app: Flask, *args: Any, **kwargs: Any) -> None:
        """Initialise the extension for a given :class:`flask.Flask` app.

        The method wires core services into ``app``, enabling optional
        behaviours such as response caching, Cross-Origin Resource Sharing
        (CORS) headers and automatic OpenAPI documentation. Any additional
        ``kwargs`` are forwarded to :meth:`init_api` and
        :meth:`init_apispec`.

        Args:
            app: The Flask application to register with.
            *args: Positional arguments forwarded to
                :class:`~flarchitect.utils.general.AttributeInitializerMixin`.
            **kwargs: Optional keyword arguments affecting initialisation.
                Supported keys include:

                ``cache`` (dict | bool, optional): Configuration for caching
                responses. When truthy, ``API_CACHE_TYPE`` and
                ``API_CACHE_TIMEOUT`` are used to set up caching.

                ``enable_cors`` (bool, optional): Enable CORS handling when
                ``True``. The ``CORS_RESOURCES`` mapping defines allowed
                origins.

                ``create_docs`` (bool, optional): Generate ReDoc and OpenAPI
                documentation when ``True``.

        Examples:
            Basic initialisation::

                architect = Architect()
                architect.init_app(app)

            With optional features::

                architect = Architect()
                architect.init_app(
                    app,
                    cache={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300},
                    enable_cors=True,
                    create_docs=True,
                )

        """
        super().__init__(app, *args, **kwargs)
        self._register_app(app)
        logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)
        self.api_spec = None

        self.cache = None
        cache_type = self.get_config("API_CACHE_TYPE")
        if cache_type:
            cache_timeout = self.get_config("API_CACHE_TIMEOUT", 300)
            if importlib.util.find_spec("flask_caching") is not None:
                from flask_caching import Cache

                cache_config = {
                    "CACHE_TYPE": cache_type,
                    "CACHE_DEFAULT_TIMEOUT": cache_timeout,
                }
                self.cache = Cache(config=cache_config)
                self.cache.init_app(app)
            elif cache_type == "SimpleCache":
                from flarchitect.core.simple_cache import SimpleCache

                self.cache = SimpleCache(default_timeout=cache_timeout)
                self.cache.init_app(app)
            else:
                raise RuntimeError(
                    "flask-caching is required when API_CACHE_TYPE is set"
                )

        if self.get_config("API_ENABLE_CORS", False):
            if importlib.util.find_spec("flask_cors") is not None:
                from flask_cors import CORS

                CORS(app, resources=app.config.get("CORS_RESOURCES", {}))
            else:
                resources = app.config.get("CORS_RESOURCES", {})
                compiled = [
                    (re.compile(pattern), opts.get("origins", "*"))
                    for pattern, opts in resources.items()
                ]

                @app.after_request
                def apply_cors_headers(response: Response) -> Response:
                    """Apply CORS headers based on configured resource patterns.

                    Args:
                        response: The outgoing Flask response.

                    Returns:
                        Response: The modified response with any relevant CORS
                        headers added.
                    """

                    path = request.path
                    origin = request.headers.get("Origin")
                    for pattern, origins in compiled:
                        if pattern.match(path):
                            allowed = (
                                [origins] if isinstance(origins, str) else list(origins)
                            )
                            if "*" in allowed or (origin and origin in allowed):
                                response.headers["Access-Control-Allow-Origin"] = (
                                    "*" if "*" in allowed else origin
                                )
                            break
                    return response

        if self.get_config("FULL_AUTO", True):
            self.init_api(app=app, **kwargs)
        if get_config_or_model_meta("API_CREATE_DOCS", default=True):
            self.init_apispec(app=app, **kwargs)

        logger.log(2, "Creating rate limiter")
        storage_uri = check_rate_services()
        self.app.config["RATELIMIT_HEADERS_ENABLED"] = True
        self.app.config["RATELIMIT_SWALLOW_ERRORS"] = True
        self.app.config["RATELIMIT_IN_MEMORY_FALLBACK_ENABLED"] = True
        self.limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=storage_uri if storage_uri else None,
        )

        @app.before_request
        def _global_authentication() -> None:
            """Authenticate requests for routes without ``schema_constructor``.

            Routes decorated with :meth:`schema_constructor` handle
            authentication themselves. This hook covers any additional view
            functions so developers can rely on global configuration without
            manual decoration.
            """

            view = app.view_functions.get(request.endpoint)
            if (
                not view
                or getattr(view, "_auth_disabled", False)
                or getattr(view, "_has_schema_constructor", False)
            ):
                return
            try:
                self._handle_auth(
                    model=None, output_schema=None, input_schema=None, auth_flag=True
                )
            except (
                CustomHTTPException
            ) as exc:  # pragma: no cover - integration behaviour
                return create_response(status=exc.status_code, errors=exc.reason)

        @app.teardown_request
        def clear_current_user(exception: BaseException | None = None) -> None:
            """Remove the current user from the context after each request.

            Args:
                exception (BaseException | None): Exception raised during the
                    request lifecycle, if any.

            Returns:
                None: Flask ignores the return value of teardown callbacks.
            """

            set_current_user(None)

    def _register_app(self, app: Flask):
        """
        Registers the app with the extension, and saves it to self.

        Args:
            app (Flask): The flask app.
        """
        if FLASK_APP_NAME not in app.extensions:
            app.extensions[FLASK_APP_NAME] = self
        self.app = app

    def init_apispec(self, app: Flask, **kwargs):
        """Initialise the API specification and serve it via a route.

        Args:
            app (Flask): The Flask app.
            **kwargs (dict): Additional keyword arguments for ``CustomSpec``.
        """
        self.api_spec = CustomSpec(app=app, architect=self, **kwargs)

        if self.get_config("API_CREATE_DOCS", True):
            spec_route = self.get_config("API_SPEC_ROUTE", "/openapi.json")

            @app.get(spec_route)
            def openapi_spec() -> Response:
                """Return the generated OpenAPI specification as JSON."""
                assert self.api_spec is not None
                return jsonify(self.api_spec.to_dict())

    def init_api(self, **kwargs):
        """Initialises the api object, which handles Flask route creation for models.

        Args:
            **kwargs (dict): Dictionary of keyword arguments.
        """
        self.api = RouteCreator(architect=self, **kwargs)

    def init_graphql(
        self,
        schema: Any | None = None,
        *,
        models: list[type[DeclarativeBase]] | None = None,
        session: Session | None = None,
        url_path: str = "/graphql",
    ) -> None:
        """Register a GraphQL endpoint and document it in the OpenAPI spec.

        The generated schema supports custom type mappings, model
        relationships, filtering and pagination arguments, and CRUD mutations.

        Args:
            schema: Prebuilt Graphene schema. If ``None``, ``models`` and
                ``session`` must be provided to build one automatically.
            models: Models to expose via GraphQL when ``schema`` is ``None``.
            session: SQLAlchemy session for resolver functions.
            url_path: URL path where the GraphQL endpoint should live.

        Raises:
            ValueError: If a schema is not supplied and models or session are
                missing.
        """

        if schema is None:
            if not models or session is None:
                raise ValueError("Provide a schema or models and session")
            from flarchitect.graphql import create_schema_from_models

            schema = create_schema_from_models(models, session)

        @self.app.route(url_path, methods=["GET", "POST"])
        def graphql_endpoint() -> Response:
            """Handle GraphQL queries and mutations."""

            if request.method == "GET":
                return jsonify({"message": "Send a POST request with a GraphQL query."})

            payload = request.get_json(silent=True) or {}
            result = schema.execute(
                payload.get("query"),
                variable_values=payload.get("variables"),
            )
            response_data: dict[str, Any] = {}
            if result.errors:
                response_data["errors"] = [str(err) for err in result.errors]
            if result.data is not None:
                response_data["data"] = result.data
            return jsonify(response_data)

        route = {
            "function": graphql_endpoint,
            "summary": "GraphQL endpoint",
            "description": "Execute GraphQL queries and mutations.",
            "tag": "GraphQL",
        }
        self.set_route(route)
        if self.api_spec is not None:
            from flarchitect.specs.generator import register_routes_with_spec

            register_routes_with_spec(self, [route])

    def to_api_spec(self):
        """
        Returns the api spec object.

        Returns:
            APISpec: The api spec json object.
        """
        if self.api_spec:
            return self.api_spec.to_dict()

    def get_config(self, key, default: Optional = None):
        """
        Gets a config value from the app config.

        Args:
            key (str): The key of the config value.
            default (Optional): The default value to return if the key is not found.

        Returns:
            Any: The config value.
        """
        if self.app:
            return self.app.config.get(key, default)

    def _handle_auth(
        self,
        *,
        model: DeclarativeBase | None,
        output_schema: type[Schema] | None,
        input_schema: type[Schema] | None,
        auth_flag: bool | None,
    ) -> None:
        """Authenticate the current request based on configuration.

        Args:
            model: Database model associated with the endpoint.
            output_schema: Schema used to serialize responses.
            input_schema: Schema used to deserialize requests.
            auth_flag: Optional flag to disable authentication when ``False``.

        Raises:
            CustomHTTPException: If authentication is required but no method
                succeeds.
        """

        auth_method = get_config_or_model_meta(
            "API_AUTHENTICATE_METHOD",
            model=model,
            output_schema=output_schema,
            input_schema=input_schema,
            method=request.method,
            default=False,
        )

        if auth_method and auth_flag is not False:
            if not isinstance(auth_method, list):
                auth_method = [auth_method]

            for method_name in auth_method:
                auth_func = getattr(self, f"_authenticate_{method_name}", None)
                if callable(auth_func) and auth_func():
                    return

            raise CustomHTTPException(status_code=401)

    def _apply_schemas(
        self,
        func: Callable,
        output_schema: type[Schema] | None,
        input_schema: type[Schema] | None,
        many: bool,
    ) -> Callable:
        """Apply input and output schema decorators to a view function.

        Args:
            func: The view function to decorate.
            output_schema: Schema used to serialize responses.
            input_schema: Schema used to deserialize requests.
            many: ``True`` if the route returns multiple objects.

        Returns:
            Callable: The decorated function.
        """

        decorator = (
            handle_many(output_schema, input_schema)
            if many
            else handle_one(output_schema, input_schema)
        )
        return decorator(func)

    def _apply_rate_limit(
        self,
        func: Callable,
        *,
        model: DeclarativeBase | None,
        output_schema: type[Schema] | None,
        input_schema: type[Schema] | None,
    ) -> Callable:
        """Wrap a function with rate limiting if configured.

        Args:
            func: The function to wrap.
            model: Database model associated with the endpoint.
            output_schema: Schema used to serialize responses.
            input_schema: Schema used to deserialize requests.

        Returns:
            Callable: The rate-limited function or the original ``func`` if no
            rate limiting is applied.
        """

        rl = get_config_or_model_meta(
            "API_RATE_LIMIT",
            model=model,
            input_schema=input_schema,
            output_schema=output_schema,
            default=False,
        )
        if rl and isinstance(rl, str) and validate_flask_limiter_rate_limit_string(rl):
            return self.limiter.limit(rl)(func)
        if rl:
            rule = find_rule_by_function(self, func).rule
            logger.error(
                f"Rate limit definition not a string or not valid. Skipping for `{rule}` route."
            )
        return func

    def _authenticate_jwt(self) -> bool:
        """Authenticate the request using a JSON Web Token."""

        try:
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ")[1]
                usr = get_user_from_token(token, secret_key=None)
                if usr:
                    set_current_user(usr)
                    return True
        except CustomHTTPException:
            pass
        return False

    def _authenticate_basic(self) -> bool:
        """Authenticate the request using HTTP Basic auth."""

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Basic "):
            return False

        encoded_credentials = auth.split(" ", 1)[1]
        try:
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError):
            return False

        username, _, password = decoded.partition(":")
        if not username or not password:
            return False

        user_model = get_config_or_model_meta("API_USER_MODEL", default=None)
        lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD", default=None)
        check_method = get_config_or_model_meta(
            "API_CREDENTIAL_CHECK_METHOD", default=None
        )

        if not (user_model and lookup_field and check_method):
            return False

        try:
            user = user_model.query.filter(
                getattr(user_model, lookup_field) == username
            ).first()
        except Exception:  # pragma: no cover
            return False

        if user and getattr(user, check_method)(password):
            set_current_user(user)
            return True

        return False

    def _authenticate_api_key(self) -> bool:
        """Authenticate the request using an API key."""

        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "api-key" or not token:
            return False

        custom_method = get_config_or_model_meta(
            "API_KEY_AUTH_AND_RETURN_METHOD", default=None
        )
        if callable(custom_method):
            user = custom_method(token)
            if user:
                set_current_user(user)
                return True
            return False

        user_model = get_config_or_model_meta("API_USER_MODEL", default=None)
        hash_field = get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", default=None)
        check_method = get_config_or_model_meta(
            "API_CREDENTIAL_CHECK_METHOD", default=None
        )

        if not (user_model and hash_field and check_method):
            return False

        query = getattr(user_model, "query", None)
        if query is None:
            try:
                session = get_session(user_model)
            except Exception:
                return False
            query = session.query(user_model)

        for usr in query.all():
            stored = getattr(usr, hash_field, None)
            if stored and getattr(usr, check_method)(token):
                set_current_user(usr)
                return True

        return False

    def _authenticate_custom(self) -> bool:
        """Authenticate the request using a custom method."""

        custom_auth_func = get_config_or_model_meta("API_CUSTOM_AUTH")
        if callable(custom_auth_func):
            return custom_auth_func()
        return False

    def schema_constructor(
        self,
        output_schema: type[Schema] | None = None,
        input_schema: type[Schema] | None = None,
        model: DeclarativeBase | None = None,
        group_tag: str | None = None,
        many: bool | None = False,
        roles: bool | list[str] | tuple[str, ...] | None = False,
        **kwargs,
    ) -> Callable:
        """Decorate an endpoint with schema, role, and OpenAPI metadata.

        Args:
            output_schema: Output schema. Defaults to ``None``.
            input_schema: Input schema. Defaults to ``None``.
            model: Database model. Defaults to ``None``.
            group_tag: Group name. Defaults to ``None``.
            many: Indicates if multiple items are returned. Defaults to ``False``.
            roles: Roles required to access the endpoint. When truthy and
                authentication is enabled, the :func:`require_roles` decorator
                is applied. Defaults to ``False``.
            kwargs: Additional keyword arguments.

        Returns:
            Callable: The decorated function.
        """

        auth_flag = kwargs.get("auth")
        roles_tuple: tuple[str, ...] = ()
        if roles and roles is not True:
            roles_tuple = (
                tuple(roles) if isinstance(roles, list | tuple) else (str(roles),)
            )

        def decorator(f: Callable) -> Callable:
            local_roles_required = None
            if roles and auth_flag is not False:
                from flarchitect.authentication import (
                    require_roles as local_roles_required,
                )

            @wraps(f)
            def wrapped(*_args, **_kwargs):
                self._handle_auth(
                    model=model,
                    output_schema=output_schema,
                    input_schema=input_schema,
                    auth_flag=auth_flag,
                )

                f_decorated = self._apply_schemas(
                    f, output_schema, input_schema, bool(many)
                )
                f_decorated = self._apply_rate_limit(
                    f_decorated,
                    model=model,
                    output_schema=output_schema,
                    input_schema=input_schema,
                )

                if roles and auth_flag is not False and local_roles_required:
                    f_decorated = local_roles_required(*roles_tuple)(f_decorated)

                return f_decorated(*_args, **_kwargs)

            wrapped._has_schema_constructor = True
            if auth_flag is False:
                wrapped._auth_disabled = True

            if roles and auth_flag is not False:

                def _marker() -> None:
                    """Marker function for roles documentation."""

                _marker.__name__ = "require_roles"
                _marker._args = roles_tuple  # type: ignore[attr-defined]
                _marker._any_of = False  # type: ignore[attr-defined]
                wrapped._decorators = getattr(wrapped, "_decorators", [])
                wrapped._decorators.append(_marker)  # type: ignore[attr-defined]

            # Store route information for OpenAPI documentation
            route_info = {
                "function": wrapped,
                "output_schema": output_schema,
                "input_schema": input_schema,
                "model": model,
                "group_tag": group_tag,
                "tag": kwargs.get("tag"),
                "summary": kwargs.get("summary"),
                "error_responses": kwargs.get("error_responses"),
                "many_to_many_model": kwargs.get("many_to_many_model"),
                "multiple": many or kwargs.get("multiple"),
                "parent": kwargs.get("parent_model"),
            }

            self.set_route(route_info)
            return wrapped

        return decorator

    @classmethod
    def get_templates_path(
        cls, folder_name: str = "html", max_levels: int = 3
    ) -> str | None:
        """Recursively search for ``folder_name`` within ancestor directories.

        Args:
            folder_name: Name of the folder to search for. Defaults to "html".
            max_levels: Maximum number of levels to search upward. Defaults to 3.

        Returns:
            str | None: Path to the folder if found, otherwise ``None``.
        """
        spec = importlib.util.find_spec(cls.__module__)
        source_dir: Path = Path(os.path.split(spec.origin)[0])

        for _level in range(max_levels):
            potential_path: Path = source_dir / folder_name
            if potential_path.exists() and potential_path.is_dir():
                return str(potential_path)

            source_dir = source_dir.parent

        return None

    def set_route(self, route: dict):
        """
        Adds a route to the route spec list, which is used to generate the api spec.

        Args:
            route (dict): The route object.
        """
        if not hasattr(route["function"], "_decorators"):
            route["function"]._decorators = []

        route["function"]._decorators.append(self.schema_constructor)

        if self.route_spec is None:
            self.route_spec = []

        self.route_spec.append(route)
