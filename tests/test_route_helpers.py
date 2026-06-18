import base64
from types import SimpleNamespace
from typing import ClassVar

import pytest
from flask import Flask
from werkzeug.routing import IntegerConverter

from flarchitect.core.routes import (
    RouteCreator,
    _global_pre_process,
    _post_process,
    _pre_process,
    _route_function_factory,
    _truthy_config_value,
    create_params_from_rule,
    create_query_params_from_rule,
    find_rule_by_function,
)


class _Service:
    class Model:
        pass

    model = Model


def test_global_pre_process_no_hook_returns_kwargs():
    service = _Service()
    assert _global_pre_process(service, None, test=1) == {"test": 1}


def test_truthy_config_value_handles_strings_and_native_values():
    assert _truthy_config_value("true") is True
    assert _truthy_config_value(" yes ") is True
    assert _truthy_config_value("0") is False
    assert _truthy_config_value("false") is False
    assert _truthy_config_value("no") is False
    assert _truthy_config_value(1) is True
    assert _truthy_config_value(0) is False


def test_pre_and_post_process_helpers():
    service = _Service()

    def pre_hook(*, model, **kwargs):
        kwargs["pre"] = True
        return kwargs

    def post_hook(*, model, output, **kwargs):
        return {"output": output + 1}

    processed = _pre_process(service, pre_hook, test=1)
    assert processed["pre"] is True
    assert _post_process(service, post_hook, 1, **processed) == 2


def test_route_function_factory_runs_hooks():
    service = _Service()

    def global_hook(*, model, **kwargs):
        kwargs["global"] = True
        return kwargs

    def pre_hook(*, model, **kwargs):
        kwargs["pre"] = True
        return kwargs

    def post_hook(*, model, output, **kwargs):
        return {"output": output + 1}

    def action(**action_kwargs):
        return action_kwargs["lookup_val"]

    route = _route_function_factory(
        service,
        action,
        many=False,
        global_pre_hook=global_hook,
        pre_hook=pre_hook,
        post_hook=post_hook,
        get_field=None,
        join_model=None,
        output_schema=None,
    )

    assert route(1) == 2


def test_route_function_factory_without_hooks_returns_action_output():
    service = _Service()

    def action(**action_kwargs):
        return {"id": action_kwargs["id"], "model": action_kwargs["model"]}

    route = _route_function_factory(
        service,
        action,
        many=True,
        global_pre_hook=None,
        pre_hook=None,
        post_hook=None,
        get_field="items",
        join_model=_Service.Model,
        output_schema=None,
    )

    assert route(7) == {"id": 7, "model": None}


def _route_creator(app: Flask) -> RouteCreator:
    return RouteCreator(SimpleNamespace(app=app), app, api_full_auto=False)


def test_find_rule_by_function_and_parameter_helpers():
    app = Flask(__name__)

    @app.get("/items/<int:item_id>")
    def item_detail():
        return "ok"

    class ItemSchema:
        pass

    class ItemModel:
        class Meta:
            name = "Inventory item"
            schema_case = "snake"

    architect = SimpleNamespace(app=app)
    rule = find_rule_by_function(architect, item_detail)

    assert rule is not None
    params = create_params_from_rule(ItemModel, rule, ItemSchema)
    assert params == [
        {
            "name": "item_id",
            "in": "path",
            "required": True,
            "description": "Identifier for the inventory_item instance.",
            "schema": {"type": "integer"},
        }
    ]
    assert find_rule_by_function(architect, lambda: None) is None


def test_create_query_params_from_rule_combines_generated_and_custom_params():
    class Rule:
        arguments = {"item_id"}
        _converters = {"item_id": IntegerConverter(map=None)}

    class Schema:
        class Meta:
            model = None

    class Model:
        class Meta:
            get_additional_query_params: ClassVar[list[dict[str, str]]] = [{"name": "extra"}]

    app = Flask(__name__)
    app.config.update(API_SOFT_DELETE=True, API_ALLOW_CASCADE_DELETE=True)

    with app.app_context():
        params = create_query_params_from_rule(
            Rule,
            {"GET", "DELETE"},
            Schema,
            many=True,
            model=Model,
            custom_query_params=[{"name": "custom"}],
        )
        post_params = create_query_params_from_rule(Rule, {"POST"}, Schema, many=False, model=Model)

    names = [param["name"] for param in params]
    assert names == ["cascade_delete", "include_deleted", "limit", "page", "extra", "custom"]
    assert post_params == []


def test_model_route_segments_use_alternate_endpoint_when_canonical_disabled():
    app = Flask(__name__)
    app.config.update(API_REGISTER_CANONICAL_ROUTES=False)

    class CustomEndpointModel:
        class Meta:
            endpoint: ClassVar[list[str]] = ["/custom-items", "archive/items", ""]

    with app.app_context():
        route_creator = _route_creator(app)
        segments, to_url_segment, canonical_segment = route_creator._model_route_segments(
            CustomEndpointModel,
            input_schema_class=None,
            output_schema_class=None,
        )

    assert segments == ["custom-items", "archive/items"]
    assert to_url_segment == "custom-items"
    assert canonical_segment == "custom-endpoint-models"


def test_model_route_method_policy_respects_read_only_config_and_model_overrides():
    app = Flask(__name__)

    class ReadOnlyModel:
        class Meta:
            read_only = True

    class ModelAllowedMethods:
        class Meta:
            allowed_methods: ClassVar[list[str]] = ["POST"]
            block_methods: ClassVar[list[str]] = ["POST", "PATCH"]

    class ModelAllowedOnly:
        class Meta:
            allowed_methods: ClassVar[list[str]] = ["POST"]

    with app.app_context():
        route_creator = _route_creator(app)

        read_only_policy = route_creator._model_route_policy(ReadOnlyModel)
        assert route_creator._model_route_method_allowed("GET", read_only_policy) is True
        assert route_creator._model_route_method_allowed("POST", read_only_policy) is False

        model_policy = route_creator._model_route_policy(ModelAllowedMethods)
        assert route_creator._model_route_method_allowed("POST", model_policy) is False
        assert route_creator._model_route_method_allowed("PATCH", model_policy) is False
        assert route_creator._model_route_method_allowed("GET", model_policy) is False

        allowed_only_policy = route_creator._model_route_policy(ModelAllowedOnly)
        assert route_creator._model_route_method_allowed("POST", allowed_only_policy) is True
        assert route_creator._model_route_method_allowed("GET", allowed_only_policy) is False


def test_model_route_method_policy_respects_global_allow_and_block_lists():
    app = Flask(__name__)
    app.config.update(API_ALLOWED_METHODS=["GET", "POST"], API_BLOCK_METHODS=["DELETE"])

    class PlainModel:
        pass

    with app.app_context():
        route_creator = _route_creator(app)
        policy = route_creator._model_route_policy(PlainModel)

    assert route_creator._model_route_method_allowed("GET", policy) is True
    assert route_creator._model_route_method_allowed("POST", policy) is True
    assert route_creator._model_route_method_allowed("PATCH", policy) is False
    assert route_creator._model_route_method_allowed("DELETE", policy) is False


def test_route_roles_resolve_relation_get_method_and_fallbacks():
    app = Flask(__name__)
    app.config.update(
        API_ROLE_MAP={
            "RELATION_GET_MANY": {"roles": "relation-reader", "any_of": True},
            "GET_ONE": ["single-reader"],
            "POST": "writer",
            "ALL": ["fallback"],
        }
    )

    with app.app_context():
        route_creator = _route_creator(app)

        assert route_creator._resolve_roles_for_route(
            model=None,
            http_method="GET",
            is_many=True,
            is_relation=True,
        ) == (["relation-reader"], True)
        assert route_creator._resolve_roles_for_route(
            model=None,
            http_method="GET",
            is_many=False,
        ) == (["single-reader"], False)
        assert route_creator._resolve_roles_for_route(
            model=None,
            http_method="POST",
        ) == (["writer"], False)
        assert route_creator._resolve_roles_for_route(
            model=None,
            http_method="DELETE",
        ) == (["fallback"], False)


def test_route_roles_model_meta_overrides_and_required_accepted_fallbacks():
    app = Flask(__name__)

    class ModelRoleMap:
        class Meta:
            role_map: ClassVar[dict[str, object]] = {
                "RELATION_GET_ONE": ["relation-single"],
                "*": {"roles": ["model-star"], "any_of": True},
            }

    class RequiredRoles:
        class Meta:
            roles_required: ClassVar[list[str]] = ["admin", "editor"]

    class AcceptedRoles:
        class Meta:
            roles_accepted: ClassVar[list[str]] = ["admin", "support"]

    class AuthOnly:
        class Meta:
            role_map = True

    class NoRoles:
        pass

    with app.app_context():
        route_creator = _route_creator(app)

        assert route_creator._resolve_roles_for_route(
            model=ModelRoleMap,
            http_method="GET",
            is_relation=True,
        ) == (["relation-single"], False)
        assert route_creator._resolve_roles_for_route(
            model=ModelRoleMap,
            http_method="PATCH",
        ) == (["model-star"], True)
        assert route_creator._resolve_roles_for_route(
            model=RequiredRoles,
            http_method="GET",
        ) == (["admin", "editor"], False)
        assert route_creator._resolve_roles_for_route(
            model=AcceptedRoles,
            http_method="GET",
        ) == (["admin", "support"], True)
        assert route_creator._resolve_roles_for_route(
            model=AuthOnly,
            http_method="GET",
        ) == (None, False)
        assert route_creator._resolve_roles_for_route(
            model=NoRoles,
            http_method="GET",
        ) == (None, False)


def test_route_normalize_roles_spec_handles_dicts_and_unknown_values():
    app = Flask(__name__)

    with app.app_context():
        route_creator = _route_creator(app)

    assert route_creator._normalize_roles_spec(None) == (None, False)
    assert route_creator._normalize_roles_spec(True, default_any_of=True) == (None, True)
    assert route_creator._normalize_roles_spec(("admin", "editor")) == (["admin", "editor"], False)
    assert route_creator._normalize_roles_spec({"roles": "admin"}) == (["admin"], False)
    assert route_creator._normalize_roles_spec({"roles": [], "any_of": True}) == (None, True)
    assert route_creator._normalize_roles_spec(object(), default_any_of=True) == (None, True)


def test_api_key_token_from_request_accepts_only_api_key_scheme():
    app = Flask(__name__)

    with app.app_context():
        route_creator = _route_creator(app)

    with app.test_request_context(headers={"Authorization": "Api-Key secret-token"}):
        assert route_creator._api_key_token_from_request() == "secret-token"

    with app.test_request_context(headers={"Authorization": "Bearer secret-token"}):
        assert route_creator._api_key_token_from_request() is None

    with app.test_request_context(headers={"Authorization": "Api-Key"}):
        assert route_creator._api_key_token_from_request() is None


def test_api_key_user_from_token_prefers_custom_method_and_falls_back_to_candidates():
    app = Flask(__name__)
    seen_tokens: list[str] = []

    class CustomUser:
        class Meta:
            key_auth_and_return_method = staticmethod(lambda token: seen_tokens.append(token) or "custom-user")

    class Candidate:
        def __init__(self, stored: str, valid: bool) -> None:
            self.api_hash = stored
            self.valid = valid

        def check_key(self, token: str) -> bool:
            return self.valid and token == "secret"

    class Query:
        @staticmethod
        def all():
            return [
                Candidate("", True),
                Candidate("stored", False),
                Candidate("stored", True),
            ]

    class QueryUser:
        query = Query()

        class Meta:
            credential_hash_field = "api_hash"
            credential_check_method = "check_key"

    with app.app_context():
        route_creator = _route_creator(app)
        assert route_creator._api_key_user_from_token(CustomUser, "custom-token") == "custom-user"
        assert seen_tokens == ["custom-token"]

        matched = route_creator._api_key_user_from_token(QueryUser, "secret")
        assert isinstance(matched, Candidate)
        assert matched.valid is True


def test_api_key_candidate_iteration_and_payload(monkeypatch):
    app = Flask(__name__)

    class User:
        id = 42
        email = "user@example.com"

    class QueryBackedUser:
        class Query:
            @staticmethod
            def all():
                return [User()]

        query = Query()

    class SessionBackedUser:
        pass

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        def query(user):
            class Result:
                @staticmethod
                def all():
                    return [User()]

            return Result()

    from flarchitect.core import routes as routes_module

    monkeypatch.setattr(routes_module, "get_session", lambda user: Session())
    monkeypatch.setattr(routes_module, "_get_pk_and_lookups", lambda: ("id", "email"))

    with app.app_context():
        route_creator = _route_creator(app)
        assert list(route_creator._iter_api_key_candidates(QueryBackedUser))[0].email == "user@example.com"
        assert list(route_creator._iter_api_key_candidates(SessionBackedUser))[0].id == 42
        assert route_creator._api_key_login_payload(User()) == {
            "user_pk": 42,
            "email": "user@example.com",
        }

    monkeypatch.setattr(routes_module, "_get_pk_and_lookups", lambda: ("id", None))
    with app.app_context():
        route_creator = _route_creator(app)
        assert route_creator._api_key_login_payload(User()) == {"user_pk": 42}


def test_api_key_candidate_iteration_swallows_session_lookup_errors(monkeypatch):
    from flarchitect.core import routes as routes_module

    app = Flask(__name__)

    class SessionBackedUser:
        pass

    monkeypatch.setattr(routes_module, "get_session", lambda user: (_ for _ in ()).throw(RuntimeError("no session")))

    with app.app_context():
        route_creator = _route_creator(app)
        assert list(route_creator._iter_api_key_candidates(SessionBackedUser)) == []


def test_route_validation_requires_secret_for_auth_methods():
    app = Flask(__name__)
    app.config["API_AUTHENTICATE_METHOD"] = "basic"

    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="SECRET_KEY must be set"):
            route_creator._validate_authentication_setup()


def test_route_validation_is_noop_when_full_auto_disabled():
    app = Flask(__name__)

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.validate()


def test_route_validation_full_auto_requires_base_model():
    app = Flask(__name__)

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.api_full_auto = True
        route_creator.api_base_model = None
        with pytest.raises(ValueError, match="API_BASE_MODEL"):
            route_creator.validate()


def test_route_validation_authenticate_requires_method_and_user_model():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="secret", API_AUTHENTICATE=True)

    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_AUTHENTICATE_METHOD"):
            route_creator._validate_authentication_setup()

    app.config.update(API_AUTHENTICATE_METHOD="basic", API_AUTHENTICATE=False)
    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_USER_MODEL"):
            route_creator._validate_authentication_setup()


def test_route_validation_jwt_api_key_and_custom_auth_requirements():
    class User:
        pass

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="secret",
        API_AUTHENTICATE=True,
        API_AUTHENTICATE_METHOD="jwt",
        API_USER_MODEL=User,
    )

    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="ACCESS_SECRET_KEY"):
            route_creator._validate_authentication_setup()

    app.config.update(
        API_AUTHENTICATE_METHOD="api_key",
        API_CREDENTIAL_HASH_FIELD=None,
        API_KEY_AUTH_AND_RETURN_METHOD=None,
    )
    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_CREDENTIAL_HASH_FIELD"):
            route_creator._validate_authentication_setup()

    app.config.update(
        API_AUTHENTICATE_METHOD="custom",
        API_CUSTOM_AUTH=False,
    )
    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_CUSTOM_AUTH must be set"):
            route_creator._validate_authentication_setup()

    app.config["API_CUSTOM_AUTH"] = "not-callable"
    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="must be a callable"):
            route_creator._validate_authentication_setup()

    app.config["API_CUSTOM_AUTH"] = lambda: True
    with app.app_context():
        route_creator = _route_creator(app)
        route_creator._validate_authentication_setup()


def test_api_key_validation_requires_user_model_before_credentials():
    app = Flask(__name__)

    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_USER_MODEL"):
            route_creator._validate_api_key_auth_setup(
                user=None,
                hash_field="api_hash",
                check_method="check_key",
            )


def test_route_validation_soft_delete_requires_attribute_and_state_values():
    app = Flask(__name__)
    app.config.update(API_SOFT_DELETE=True)

    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_SOFT_DELETE_ATTRIBUTE"):
            route_creator._validate_soft_delete_setup()

    app.config["API_SOFT_DELETE_ATTRIBUTE"] = "deleted"
    app.config["API_SOFT_DELETE_VALUES"] = ["active", "deleted"]
    with app.app_context():
        route_creator = _route_creator(app)
        with pytest.raises(ValueError, match="API_SOFT_DELETE_VALUES"):
            route_creator._validate_soft_delete_setup()

    app.config["API_SOFT_DELETE_VALUES"] = ("active", "deleted")
    with app.app_context():
        route_creator = _route_creator(app)
        route_creator._validate_soft_delete_setup()


def test_make_auth_routes_respects_auto_flag_and_missing_methods():
    app = Flask(__name__)
    app.config.update(API_AUTO_AUTH_ROUTES=False, API_AUTHENTICATE_METHOD="jwt")

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.make_auth_routes()

    assert len(app.url_map._rules) == 1  # static route only

    app = Flask(__name__)
    app.config.update(API_AUTO_AUTH_ROUTES=True, API_AUTHENTICATE_METHOD=None)
    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.make_auth_routes()

    assert len(app.url_map._rules) == 1


def test_make_auth_routes_dispatches_configured_method_and_registers_loader(monkeypatch):
    app = Flask(__name__)
    calls: list[tuple[str, object]] = []

    class User:
        @staticmethod
        def get(user_id):
            return {"id": user_id}

    app.config.update(
        API_AUTO_AUTH_ROUTES=True,
        API_AUTHENTICATE_METHOD=["jwt"],
        API_USER_MODEL=User,
        API_EXPOSE_ME=False,
    )

    monkeypatch.setattr(RouteCreator, "_make_jwt_auth_routes", lambda self, user: calls.append(("jwt", user)))
    monkeypatch.setattr(RouteCreator, "_make_basic_auth_routes", lambda self, user: calls.append(("basic", user)))
    monkeypatch.setattr(RouteCreator, "_make_api_key_auth_routes", lambda self, user: calls.append(("api_key", user)))

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.make_auth_routes()

    assert calls == [("jwt", User)]
    assert app.login_manager._user_callback("12") == {"id": "12"}

    for method, expected_call in [
        ("basic", ("basic", User)),
        ("api_key", ("api_key", User)),
    ]:
        app = Flask(__name__)
        app.config.update(
            API_AUTO_AUTH_ROUTES=True,
            API_AUTHENTICATE_METHOD=method,
            API_USER_MODEL=User,
            API_EXPOSE_ME=False,
        )
        calls.clear()
        with app.app_context():
            route_creator = _route_creator(app)
            route_creator.make_auth_routes()
        assert calls == [expected_call]


def test_make_auth_routes_registers_me_route_when_exposed(monkeypatch):
    app = Flask(__name__)
    calls: list[tuple[str, object]] = []

    class User:
        @staticmethod
        def get(user_id):
            return {"id": user_id}

    app.config.update(
        API_AUTO_AUTH_ROUTES=True,
        API_AUTHENTICATE_METHOD="custom",
        API_USER_MODEL=User,
        API_EXPOSE_ME=True,
    )

    monkeypatch.setattr(RouteCreator, "_make_jwt_auth_routes", lambda self, user: calls.append(("jwt", user)))
    monkeypatch.setattr(RouteCreator, "_make_basic_auth_routes", lambda self, user: calls.append(("basic", user)))
    monkeypatch.setattr(RouteCreator, "_make_api_key_auth_routes", lambda self, user: calls.append(("api_key", user)))
    monkeypatch.setattr(RouteCreator, "_create_me_route", lambda self, user: calls.append(("me", user)))

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator.make_auth_routes()

    assert calls == [("me", User)]
    assert app.login_manager._user_callback("34") == {"id": "34"}


def test_basic_auth_route_rejects_bad_credentials_and_returns_user(monkeypatch):
    from flarchitect.core import routes as routes_module

    app = Flask(__name__)

    class UserInstance:
        id = 5
        username = "alice"
        password_valid = False

        def check_password(self, password):
            return self.password_valid and password == "secret"

    user_instance = UserInstance()

    class Query:
        @staticmethod
        def filter(_expr):
            return Query()

        @staticmethod
        def first():
            return user_instance

    class User:
        username = "username-column"
        query = Query()

        class Meta:
            user_lookup_field = "username"
            credential_check_method = "check_password"

    monkeypatch.setattr(routes_module, "_get_pk_and_lookups", lambda: ("id", "username"))

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator._make_basic_auth_routes(User)

    client = app.test_client()
    assert client.post("/auth/login").status_code == 401
    assert client.post("/auth/login", headers={"Authorization": "Basic not-base64"}).status_code == 401

    bad_credentials = base64.b64encode(b"alice:wrong").decode()
    assert client.post("/auth/login", headers={"Authorization": f"Basic {bad_credentials}"}).status_code == 401

    user_instance.password_valid = True
    good_credentials = base64.b64encode(b"alice:secret").decode()
    response = client.post("/auth/login", headers={"Authorization": f"Basic {good_credentials}"})

    assert response.status_code == 200
    assert response.get_json()["value"] == {"user_pk": 5, "username": "alice"}


def test_api_key_auth_route_rejects_missing_or_invalid_token_and_returns_user(monkeypatch):
    from flarchitect.core import routes as routes_module

    app = Flask(__name__)

    class UserInstance:
        id = 6
        username = "bob"
        api_hash = "stored"
        key_valid = False

        def check_key(self, token):
            return self.key_valid and token == "secret"

    user_instance = UserInstance()

    class Query:
        @staticmethod
        def all():
            return [user_instance]

    class User:
        query = Query()

        class Meta:
            credential_hash_field = "api_hash"
            credential_check_method = "check_key"

    monkeypatch.setattr(routes_module, "_get_pk_and_lookups", lambda: ("id", "username"))

    with app.app_context():
        route_creator = _route_creator(app)
        route_creator._make_api_key_auth_routes(User)

    client = app.test_client()
    assert client.post("/auth/login").status_code == 401
    assert client.post("/auth/login", headers={"Authorization": "Api-Key secret"}).status_code == 401

    user_instance.key_valid = True
    response = client.post("/auth/login", headers={"Authorization": "Api-Key secret"})

    assert response.status_code == 200
    assert response.get_json()["value"] == {"user_pk": 6, "username": "bob"}
