import base64
import binascii
import importlib
import importlib.resources
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
from flarchitect.plugins import PluginManager
from flarchitect.specs.generator import CustomSpec
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.decorators import handle_many, handle_one
from flarchitect.utils.general import (
    AttributeInitialiserMixin,
    check_rate_services,
    validate_flask_limiter_rate_limit_string,
)
from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.session import get_session

FLASK_APP_NAME = "flarchitect"

F = TypeVar("F", bound=Callable[..., Any])

DEFAULT_GRAPHIQL_HTML = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>GraphiQL</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/graphiql/graphiql.min.css"
    />
  </head>
  <body style="margin: 0;">
    <div id="graphiql" style="height: 100vh;"></div>
    <script
      crossorigin
      src="https://unpkg.com/react@17/umd/react.production.min.js"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"
    ></script>
    <script src="https://unpkg.com/graphiql/graphiql.min.js"></script>
    <script>
      const graphQLFetcher = (params) =>
        fetch('/graphql', {
          method: 'post',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        }).then((response) => response.json());
      ReactDOM.render(
        React.createElement(GraphiQL, { fetcher: graphQLFetcher }),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
"""


def jwt_authentication(func: F) -> F:
    """Enforce JSON Web Token (JWT) authentication for manual routes.

    Why/How:
        Use this decorator on hand‑written Flask views to apply the same
        request authentication used by automatically generated endpoints. The
        wrapper validates the ``Authorization: Bearer <token>`` header,
        resolves the current user and stores it in context for downstream
        logic. This keeps bespoke routes consistent with the rest of the API
        without duplicating authentication code.

    Args:
        func: The view function to be wrapped.

    Returns:
        The wrapped function that validates the request's JWT before invoking
        ``func``.

    Raises:
        CustomHTTPException: If the ``Authorization`` header is missing or
            malformed, or if the provided token is invalid.
    """

    @wraps(func)
    def auth_wrapped(*args: Any, **kwargs: Any) -> Any:
        """Validate a request's JWT then forward to ``func``.

        Args:
            *args: Positional arguments forwarded to ``func``.
            **kwargs: Keyword arguments forwarded to ``func``.

        Returns:
            The result of ``func`` when authentication succeeds.

        Raises:
            CustomHTTPException: When the authorisation header is absent or
                invalid, or the token fails verification.
        """

        auth = request.headers.get("Authorization")
        if not auth:
            raise CustomHTTPException(status_code=401, reason="Authorization header missing")
        parts = auth.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise CustomHTTPException(status_code=401, reason="Invalid Authorization header")
        token = parts[1]
        usr = get_user_from_token(token, secret_key=None)
        if not usr:
            raise CustomHTTPException(status_code=401, reason="Invalid token")
        set_current_user(usr)
        return func(*args, **kwargs)

    return cast(F, auth_wrapped)


class Architect(AttributeInitialiserMixin):
    """Orchestrate flarchitect services for a Flask app.

    Why/How:
        This class ties together route generation, OpenAPI specification
        creation, caching, CORS handling, rate limiting and request
        authentication. Instantiate with a Flask application (or call
        :meth:`init_app`) to register all required hooks and endpoints with
        minimal boilerplate while keeping behaviour configurable per app/model.
    """

    app: Flask
    api_spec: CustomSpec | None = None
    api: Optional["RouteCreator"] = None
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    route_spec: list[dict[str, Any]] | None = None
    limiter: Limiter
    cache: "Cache | None" = None
    plugins: PluginManager

    def __init__(self, app: Flask | None = None, *args, **kwargs):
        """Initialise the extension and optionally bind to a Flask app.

        Why/How:
            Accepts an optional ``app`` so you can either construct and bind in
            one step or configure the instance first and later call
            :meth:`init_app`. In development the Flask reloader imports the app
            twice; to prevent duplicate set‑up we detect the parent process and
            skip initialisation there.

        Args:
            app: Optional Flask application instance to register with.
            *args: Positional arguments forwarded to :meth:`init_app`.
            **kwargs: Keyword arguments forwarded to :meth:`init_app`.
        """
        self.route_spec: list[dict[str, Any]] = []

        if app is not None:
            if self._is_reloader_start():
                logger.debug(4, "Skipping Architect initialisation in reloader parent process")
            else:
                self.init_app(app, *args, **kwargs)

    @staticmethod
    def _is_reloader_start() -> bool:
        """Detect the Flask reloader's parent process.

        Why/How:
            The development reloader spawns a supervisor that imports the app
            before creating a child process to serve requests. We check
            environment variables set by Werkzeug to avoid running one‑time
            initialisation twice.

        Returns:
            True if running as the reloader parent, otherwise False.
        """

        run_main = os.environ.get("WERKZEUG_RUN_MAIN")
        server_fd = os.environ.get("WERKZEUG_SERVER_FD")
        return server_fd is not None and run_main != "true"

    def init_app(self, app: Flask, *args: Any, **kwargs: Any) -> None:
        """Register services and hooks on the Flask app.

        Why/How:
            Wires core services into ``app``: caching, CORS, automatic OpenAPI
            documentation, rate limiting and global authentication. Extra
            ``kwargs`` are forwarded to :meth:`init_api` and
            :meth:`init_apispec` for route/spec creation.

        Args:
            app: The Flask application to register with.
            *args: Positional arguments forwarded to
                :class:`~flarchitect.utils.general.AttributeInitializerMixin`.
            **kwargs: Optional keyword arguments affecting initialisation.
                Recognised keys include ``cache``, ``enable_cors`` and
                ``create_docs``.

        Returns:
            None. The Flask app is modified in place.
        """
        super().__init__(app, *args, **kwargs)
        self._register_app(app)
        logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)
        # Enable structured JSON logs if configured
        try:
            logger.json_mode = bool(self.get_config("API_JSON_LOGS", False))
        except Exception:
            logger.json_mode = False
        self.api_spec = None
        # Load plugins
        try:
            self.plugins = PluginManager.from_config(self.get_config("API_PLUGINS", []))
        except Exception:
            self.plugins = PluginManager()

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
                raise RuntimeError("flask-caching is required when API_CACHE_TYPE is set")

        if self.get_config("API_ENABLE_CORS", False):
            if importlib.util.find_spec("flask_cors") is not None:
                from flask_cors import CORS

                CORS(app, resources=app.config.get("CORS_RESOURCES", {}))
            else:
                resources = app.config.get("CORS_RESOURCES", {})
                compiled = [(re.compile(pattern), opts.get("origins", "*")) for pattern, opts in resources.items()]

                @app.after_request
                def apply_cors_headers(response: Response) -> Response:
                    """Apply CORS headers based on configured resource patterns.

                    Args:
                        response: The outgoing Flask response.

                    Returns:
                        The response with any relevant CORS headers added.
                    """

                    path = request.path
                    origin = request.headers.get("Origin")
                    for pattern, origins in compiled:
                        if pattern.match(path):
                            allowed = [origins] if isinstance(origins, str) else list(origins)
                            if "*" in allowed or (origin and origin in allowed):
                                response.headers["Access-Control-Allow-Origin"] = "*" if "*" in allowed else origin
                            break
                    return response

        if self.get_config("FULL_AUTO", True):
            self.init_api(app=app, **kwargs)
        if get_config_or_model_meta("API_CREATE_DOCS", default=True):
            self.init_apispec(app=app, **kwargs)

        # Optional: enable built-in lightweight WebSocket endpoint if configured
        if self.get_config("API_ENABLE_WEBSOCKETS", False):
            try:
                from flarchitect.core.websockets import init_websockets

                path = self.get_config("API_WEBSOCKET_PATH", "/ws")
                init_websockets(self, path=path)
            except Exception:
                # best-effort; do not fail app init if WS cannot be set up
                pass

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

        # Correlation IDs and request timing
        @app.before_request
        def _assign_request_id_and_timer() -> None:  # pragma: no cover - Flask integration
            import contextlib
            with contextlib.suppress(Exception):
                import time as _t

                rid = request.headers.get("X-Request-ID")
                if not rid:
                    import uuid as _uuid

                    rid = _uuid.uuid4().hex
                from flask import g as _g

                _g.request_id = rid
                _g._flarch_req_start = _t.perf_counter()
            with contextlib.suppress(Exception):
                self.plugins.request_started(request)

        @app.after_request
        def _attach_request_id_and_log(response: Response) -> Response:  # pragma: no cover - Flask integration
            import contextlib
            with contextlib.suppress(Exception):
                from flask import g as _g

                rid = getattr(_g, "request_id", None)
                if rid:
                    response.headers["X-Request-ID"] = rid

                if get_config_or_model_meta("API_LOG_REQUESTS", default=True):
                    # Single-line request log with context provided by logger
                    logger.log(
                        1,
                        f"Completed {request.method} {request.path} -> {response.status_code}",
                    )
            # Allow plugins to modify/replace the response
            with contextlib.suppress(Exception):
                new_resp = self.plugins.request_finished(request, response)
                return new_resp or response
            return response

        @app.before_request
        def _global_authentication() -> None:
            """Authenticate requests for routes without ``schema_constructor``.

            Why/How:
                Routes decorated with :meth:`schema_constructor` perform their
                own authentication. This hook applies global auth to any other
                view functions so developers do not need to decorate every
                manual route individually.
            """

            view = app.view_functions.get(request.endpoint)
            if not view or getattr(view, "_auth_disabled", False) or getattr(view, "_has_schema_constructor", False):
                return
            import contextlib
            try:
                ctx = {"model": None, "method": request.method}
                self.plugins.before_authenticate(ctx)
                self._handle_auth(model=None, output_schema=None, input_schema=None, auth_flag=True)
                self.plugins.after_authenticate(ctx, success=True, user=None)
            except CustomHTTPException as exc:  # pragma: no cover - integration behaviour
                with contextlib.suppress(Exception):
                    self.plugins.after_authenticate({"model": None, "method": request.method}, success=False, user=None)
                return create_response(status=exc.status_code, errors=exc.reason)

        @app.teardown_request
        def clear_current_user(exception: BaseException | None = None) -> None:
            """Remove the current user from context after each request.

            Args:
                exception: Exception raised during the request lifecycle, if any.

            Returns:
                None. Flask ignores the return value of teardown callbacks.
            """

            set_current_user(None)

    def _register_app(self, app: Flask):
        """Attach this extension instance to the Flask app registry.

        Why/How:
            Stores the instance under a well‑known key in ``app.extensions`` so
            other components can retrieve it later and to prevent duplicate
            registration.

        Args:
            app: The Flask application.
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
            """Serve GraphiQL or execute GraphQL operations.

            A ``GET`` request returns the GraphiQL interface. ``POST`` requests
            execute GraphQL queries and mutations and return a JSON response.

            Returns:
                Response: HTML for GraphiQL or JSON GraphQL results.
            """

            if request.method == "GET":
                try:
                    template = importlib.resources.read_text("graphene", "graphiql.html")
                except (FileNotFoundError, ModuleNotFoundError):
                    template = DEFAULT_GRAPHIQL_HTML
                return Response(template, mimetype="text/html")

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
            output_schema: Schema used to serialise responses.
            input_schema: Schema used to deserialise requests.
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

            context = {
                "model": model,
                "output_schema": output_schema,
                "input_schema": input_schema,
                "method": request.method,
            }
            import contextlib
            with contextlib.suppress(Exception):
                self.plugins.before_authenticate(context)

            for method_name in auth_method:
                auth_func = getattr(self, f"_authenticate_{method_name}", None)
                if callable(auth_func) and auth_func():
                    with contextlib.suppress(Exception):
                        self.plugins.after_authenticate(context, success=True, user=None)
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
            output_schema: Schema used to serialise responses.
            input_schema: Schema used to deserialise requests.
            many: ``True`` if the route returns multiple objects.

        Returns:
            Callable: The decorated function.
        """

        decorator = handle_many(output_schema, input_schema) if many else handle_one(output_schema, input_schema)
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
            output_schema: Schema used to serialise responses.
            input_schema: Schema used to deserialise requests.

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
            logger.error(f"Rate limit definition not a string or not valid. Skipping for `{rule}` route.")
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
        check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", default=None)

        if not (user_model and lookup_field and check_method):
            return False

        try:
            user = user_model.query.filter(getattr(user_model, lookup_field) == username).first()
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

        custom_method = get_config_or_model_meta("API_KEY_AUTH_AND_RETURN_METHOD", default=None)
        if callable(custom_method):
            user = custom_method(token)
            if user:
                set_current_user(user)
                return True
            return False

        user_model = get_config_or_model_meta("API_USER_MODEL", default=None)
        hash_field = get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", default=None)
        check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", default=None)

        if not (user_model and hash_field and check_method):
            return False

        query = getattr(user_model, "query", None)
        if query is None:
            try:
                with get_session(user_model) as session:
                    for usr in session.query(user_model).all():
                        stored = getattr(usr, hash_field, None)
                        if stored and getattr(usr, check_method)(token):
                            set_current_user(usr)
                            return True
            except Exception:
                return False
            return False

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
        roles: bool | list[str] | tuple[str, ...] | dict | None = False,
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
        # Support roles provided as list/tuple/str or dict({"roles": [...], "any_of": bool})
        roles_tuple: tuple[str, ...] = ()
        roles_any_of_flag: bool = bool(kwargs.get("roles_any_of", False))
        if roles and isinstance(roles, dict):
            declared = roles.get("roles", [])
            roles_tuple = tuple(declared) if isinstance(declared, list | tuple) else (str(declared),) if declared else ()
            roles_any_of_flag = bool(roles.get("any_of", roles_any_of_flag))
        elif roles and roles is not True:
            roles_tuple = tuple(roles) if isinstance(roles, list | tuple) else (str(roles),)

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

                f_decorated = self._apply_schemas(f, output_schema, input_schema, bool(many))
                f_decorated = self._apply_rate_limit(
                    f_decorated,
                    model=model,
                    output_schema=output_schema,
                    input_schema=input_schema,
                )

                if roles and auth_flag is not False and local_roles_required:
                    f_decorated = local_roles_required(*roles_tuple, any_of=roles_any_of_flag)(f_decorated)

                return f_decorated(*_args, **_kwargs)

            wrapped._has_schema_constructor = True
            if auth_flag is False:
                wrapped._auth_disabled = True

            if roles and auth_flag is not False:

                def _marker() -> None:
                    """Marker function for roles documentation."""

                _marker.__name__ = "require_roles"
                _marker._args = roles_tuple  # type: ignore[attr-defined]
                _marker._any_of = roles_any_of_flag  # type: ignore[attr-defined]
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
    def get_templates_path(cls, folder_name: str = "html", max_levels: int = 3) -> str | None:
        """Find a templates folder relative to this module.

        Why/How:
            Walks up parent directories to locate a named folder bundled with
            the package (useful for serving GraphiQL/Redoc assets when packaged
            as a module).

        Args:
            folder_name: Folder to search for, default "html".
            max_levels: Maximum directory levels to ascend.

        Returns:
            Path to the folder if found, otherwise ``None``.
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
        """Record a route definition for OpenAPI generation.

        Why/How:
            ``schema_constructor`` and auto‑generated endpoints call this to
            collect the metadata used by the spec generator. The function also
            annotates the wrapped view with a marker so downstream tooling can
            identify it as managed by flarchitect.

        Args:
            route: Route metadata dictionary.
        """
        if not hasattr(route["function"], "_decorators"):
            route["function"]._decorators = []

        route["function"]._decorators.append(self.schema_constructor)

        if self.route_spec is None:
            self.route_spec = []

        self.route_spec.append(route)
