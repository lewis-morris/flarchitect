import importlib
import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Optional

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase

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

FLASK_APP_NAME = "flarchitect"


def jwt_authentication(func):
    @wraps(func)
    def auth_wrapped(*args, **kwargs):
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

    return auth_wrapped


class Architect(AttributeInitializerMixin):
    app: Flask
    api_spec: CustomSpec | None = None
    api: Optional["RouteCreator"] = None
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    route_spec: list = []
    limiter: Limiter

    def __init__(self, app: Flask | None = None, *args, **kwargs):
        """
        Initializes the Architect object.

        Args:
            app (Flask): The flask app.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.
        """
        if app is not None:
            self.init_app(app, *args, **kwargs)
            logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)

    def init_app(self, app: Flask, *args, **kwargs):
        """
        Initializes the Architect object.

        Args:
            app (Flask): The flask app.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.
        """
        super().__init__(app=app, *args, **kwargs)
        self._register_app(app)
        logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)
        self.api_spec = None

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

        @app.teardown_request
        def clear_current_user(exception=None):
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
        """
        Initializes the api spec object.

        Args:
            app (Flask): The flask app.
            **kwargs (dict): Dictionary of keyword arguments.
        """
        self.api_spec = CustomSpec(app=app, architect=self, **kwargs)

    def init_api(self, **kwargs):
        """
        Initializes the api object, which handles flask route creation for models.

        Args:
            **kwargs (dict): Dictionary of keyword arguments.
        """
        self.api = RouteCreator(architect=self, **kwargs)

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

    def schema_constructor(
        self,
        output_schema: type[Schema] | None = None,
        input_schema: type[Schema] | None = None,
        model: DeclarativeBase | None = None,
        group_tag: str | None = None,
        many: bool | None = False,
        **kwargs,
    ) -> Callable:
        """
        Decorator to specify OpenAPI metadata for an endpoint, along with schema information for the input and output.

        Args:
            output_schema (Optional[Type[Schema]], optional): Output schema. Defaults to None.
            input_schema (Optional[Type[Schema]], optional): Input schema. Defaults to None.
            model (Optional[DeclarativeBase], optional): Database model. Defaults to None.
            group_tag (Optional[str], optional): Group name. Defaults to None.
            many (Optional[Bool], optional): Is many or one? Defaults to False
            kwargs (dict): Dictionary of keyword arguments.

        Returns:
            Callable: The decorated function.
        """

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*_args, **_kwargs):
                # Fetch the authentication methods
                auth_method = get_config_or_model_meta(
                    "API_AUTHENTICATE_METHOD",
                    model=model,
                    output_schema=output_schema,
                    input_schema=input_schema,
                    method=request.method,
                    default=False,
                )

                # Ensure auth_method is a list
                if auth_method and kwargs.get("auth") is not False:
                    if not isinstance(auth_method, list):
                        auth_method = [auth_method]

                    auth_succeeded = False  # Flag to check if any auth method succeeded

                    # Iterate over the authentication methods
                    for method in auth_method:
                        if method == "jwt":
                            if authenticate_jwt():
                                auth_succeeded = True
                                break
                        elif method == "basic":
                            if authenticate_basic():
                                auth_succeeded = True
                                break
                        elif method == "api_key":
                            if authenticate_api_key():
                                auth_succeeded = True
                                break
                        elif method == "custom":
                            if authenticate_custom():
                                auth_succeeded = True
                                break

                    # If all authentication methods failed
                    if not auth_succeeded:
                        raise CustomHTTPException(status_code=401)

                # Apply the input/output schema handlers
                f_decorated = (
                    handle_many(output_schema, input_schema)(f)
                    if many
                    else handle_one(output_schema, input_schema)(f)
                )

                # Apply rate limiting if configured
                rl = get_config_or_model_meta(
                    "API_RATE_LIMIT",
                    model=model,
                    input_schema=input_schema,
                    output_schema=output_schema,
                    default=False,
                )
                if (
                    rl
                    and isinstance(rl, str)
                    and validate_flask_limiter_rate_limit_string(rl)
                ):
                    f_decorated = self.limiter.limit(rl)(f_decorated)
                elif rl:
                    rule = find_rule_by_function(self, f).rule
                    logger.error(
                        f"Rate limit definition not a string or not valid. Skipping for `{rule}` route."
                    )

                # Call the decorated function
                result = f_decorated(*_args, **_kwargs)
                return result

            # Authentication functions
            def authenticate_jwt() -> bool:
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

            def authenticate_basic() -> bool:
                # Implement basic authentication logic here
                # Example:
                auth = request.headers.get("Authorization")
                if auth and auth.startswith("Basic "):
                    encoded_credentials = auth.split(" ")[1]
                    # Decode and verify credentials
                    return True  # Return True if authenticated
                return False

            def authenticate_api_key() -> bool:

                header = request.headers.get("Authorization", "")
                scheme, _, token = header.partition(" ")
                if scheme.lower() != "api-key" or not token:
                    return False

                user_model = get_config_or_model_meta("API_USER_MODEL", default=None)
                hash_field = get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", default=None)
                check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", default=None)



                user = User.from_api_key(token)
                if not user:
                    abort(401)

                g.current_user = user
                return view(*args, **kwargs)

            def authenticate_custom() -> bool:
                custom_auth_func = get_config_or_model_meta("API_CUSTOM_AUTH")
                if callable(custom_auth_func):
                    return custom_auth_func()
                return False

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
    def get_templates_path(cls, folder_name="html", max_levels=3):
        """
        Recursively searches for the folder_name in the source directory
        or its parent directories up to max_levels levels.

        Args:
            folder_name (str): The name of the folder to search for. Default is "html".
            max_levels (int): Maximum number of levels to search upwards. Default is 3.

        Returns:
            str: The path to the folder if found, else None.
        """
        # Find the source directory of the class/module
        spec = importlib.util.find_spec(cls.__module__)
        source_dir = Path(os.path.split(spec.origin)[0])

        # Traverse up to max_levels levels
        for level in range(max_levels):
            # Search for the folder in the current directory
            potential_path = source_dir / folder_name
            if potential_path.exists() and potential_path.is_dir():
                return str(potential_path)

            # Move to the parent directory for the next level search
            source_dir = source_dir.parent

        # Return None if the folder is not found
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
        self.route_spec.append(route)
