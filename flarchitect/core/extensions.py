"""Small, explicit extension points for generated APIs.

Registrations belong to an Architect instance and must precede init_app.
Handlers receive a value and an OperationContext; they never own the commit.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from flask import current_app, g, has_app_context, request

from flarchitect.authentication.user import get_current_user
from flarchitect.core.utils import get_url_pk
from flarchitect.exceptions import CustomHTTPException
from flarchitect.schemas.utils import get_input_output_from_model_or_make
from flarchitect.utils.session import get_session

HOOKS = {"query", "before_create", "before_update", "before_delete", "after_operation"}
OPERATIONS = {"list", "retrieve", "create", "update", "delete"}


@dataclass
class OperationContext:
    """Request-local information shared by hooks, actions and overrides."""

    model: type
    session: Any
    operation: str
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def user(self):
        return get_current_user()

    @property
    def request(self):
        return request


def _registry():
    return current_app.extensions.get("flarchitect_extensions") if has_app_context() else None


def has_hooks(model, event: str) -> bool:
    registry = _registry()
    return bool(registry and registry._extension_hooks.get((model, event)))


def run_hooks(event: str, value: Any, context: OperationContext):
    """Run hooks in registration order; None preserves the current value."""
    registry = _registry()
    if registry:
        for handler in registry._extension_hooks.get((context.model, event), ()):
            replacement = current_app.ensure_sync(handler)(value, context)
            if replacement is not None:
                value = replacement
    return value


def scoped_record(service, identity, operation: str):
    """Resolve a record with the same visibility rules used by generated reads."""
    from flarchitect.database.utils import get_primary_key_filters

    policy = service._get_access_policy()
    query = service.session.query(service.model).filter_by(**get_primary_key_filters(service.model, identity))
    query = service._apply_policy_scope(query, policy=policy, action=operation, many=False, relation_name=None)
    query = service.apply_soft_delete_filter(query)
    obj = query.one_or_none()
    if obj is None:
        raise CustomHTTPException(404, "Resource not found.")
    service._ensure_can_read(obj, policy=policy, action=operation, many=False, relation_name=None)
    return obj


def execute_override(service, operation: str, handler: Callable, kwargs: dict):
    """Execute a replacement mutation after standard policy checks."""
    service = type(service)(service.model, g._flarchitect_extension_session)
    data = kwargs.get("data_dict") or {}
    context = OperationContext(service.model, service.session, operation, data)
    policy = service._get_access_policy()
    action = {"create": "POST", "update": "PATCH", "delete": "DELETE"}[operation]
    if operation == "create":
        service._ensure_can_create(data, policy=policy, action=action)
        value = data
    else:
        value = scoped_record(service, kwargs.get("lookup_val"), action)
        if operation == "update":
            service._ensure_can_update(value, data, policy=policy, action=action)
        else:
            service._ensure_can_delete(value, policy=policy, action=action)
    result = current_app.ensure_sync(handler)(value, context)
    if operation != "delete":
        if not isinstance(result, service.model):
            raise TypeError(f"{operation} override must return a {service.model.__name__} instance")
        result = run_hooks(f"before_{operation}", result, context)
        service.session.add(result)
    service.session.flush()
    return (None, 200) if operation == "delete" else result


def transactional(view, model, *, write=True):
    """Commit only after a successful serialised response; roll back all errors."""
    from flarchitect.utils.decorators import standardise_response

    @wraps(view)
    def wrapped(*args, **kwargs):
        with get_session(model) as session:
            previous = getattr(g, "_flarchitect_extension_session", None)
            g._flarchitect_extension_session = session
            try:
                response = view(*args, **kwargs)
                if response.status_code >= 400 or not write:
                    session.rollback()
                else:
                    session.commit()
                return response
            except Exception:
                session.rollback()
                raise
            finally:
                g._flarchitect_extension_session = previous

    return standardise_response(wrapped)


class ExtensionMixin:
    """Public registration API, shared by immediate and factory setup."""

    def _init_extensions(self):
        self._extension_hooks = {}
        self._extension_overrides = {}
        self._extension_actions = []
        self._extension_routes = []
        self._extensions_bound = False
        self._used_overrides = set()

    def _check_extension_setup(self):
        if self._extensions_bound:
            raise RuntimeError("Register extensions before Architect.init_app(app); use Architect() without an app first.")

    def hook(self, model, event: str):
        """Register query, before_create/update/delete, or after_operation."""
        self._check_extension_setup()
        if event not in HOOKS:
            raise ValueError(f"Unknown hook {event!r}; choose from {sorted(HOOKS)}")

        def decorate(handler):
            self._check_extension_setup()
            self._extension_hooks.setdefault((model, event), []).append(handler)
            return handler

        return decorate

    def override(self, model, operation: str):
        """Replace one generated operation, retaining its schemas and access checks."""
        self._check_extension_setup()
        if operation not in OPERATIONS:
            raise ValueError(f"Unknown operation {operation!r}; choose from {sorted(OPERATIONS)}")

        def decorate(handler):
            self._check_extension_setup()
            key = (model, operation)
            if key in self._extension_overrides:
                raise ValueError(f"An override for {model.__name__}.{operation} is already registered")
            self._extension_overrides[key] = handler
            return handler

        return decorate

    def action(self, model, name: str, *, methods=None, permission=None, **options):
        """Add a record action; POST by default. permission(record, context) may narrow access."""
        self._check_extension_setup()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
            raise ValueError("Action name must be a single path segment starting with a letter")
        methods = self._extension_methods(["POST"] if methods is None else methods)
        if any(method not in {"GET", "POST", "PATCH", "PUT", "DELETE"} for method in methods):
            raise ValueError("Actions support GET, POST, PATCH, PUT and DELETE")
        if "GET" in methods and len(methods) > 1:
            raise ValueError("Declare read and write actions separately")
        if permission is not None and not callable(permission):
            raise TypeError("permission must be callable")
        if options.get("auth") is False and options.get("roles"):
            raise ValueError("roles cannot be combined with auth=False")

        def decorate(handler):
            self._check_extension_setup()
            if any(item[0] is model and item[1] == name for item in self._extension_actions):
                raise ValueError(f"Action {model.__name__}.{name} is already registered")
            self._extension_actions.append((model, name, methods, permission, options, handler))
            return handler

        return decorate

    def route(self, rule: str, *, methods=None, endpoint=None, **options):
        """Register a full Flask path with schema_constructor in one decorator."""
        self._check_extension_setup()
        if not rule.startswith("/"):
            raise ValueError("Route must start with /")
        methods = self._extension_methods(["GET"] if methods is None else methods)

        def decorate(handler):
            self._check_extension_setup()
            self._extension_routes.append((rule, methods, endpoint, options, handler))
            return handler

        return decorate

    @staticmethod
    def _extension_methods(methods):
        if isinstance(methods, str) or not methods:
            raise ValueError("methods must be a nonempty sequence, e.g. ['POST']")
        return tuple(dict.fromkeys(method.upper() for method in methods))

    def _register_extension_route(self, path, methods, endpoint, view):
        # Reject ambiguous routing instead of silently shadowing another view.
        def shape(path):
            return re.sub(r"<(?:(.*?):)?[^:<>]+>", lambda match: "<" + (match[1] or "string") + ">", path)

        effective_methods = set(methods) | ({"HEAD"} if "GET" in methods else set())
        for rule in self.app.url_map.iter_rules():
            if shape(rule.rule) == shape(path) and effective_methods & (rule.methods or set()):
                raise ValueError(f"Route already registered: {path} {methods}")
        self.app.add_url_rule(path, endpoint=endpoint, view_func=view, methods=list(methods))

    def _register_extensions(self):
        unused = set(self._extension_overrides) - self._used_overrides
        if unused:
            names = ", ".join(f"{model.__name__}.{operation}" for model, operation in unused)
            raise ValueError(f"No generated route exists for override(s): {names}")
        from flarchitect.utils.decorators import standardise_response

        for index, (path, methods, endpoint, options, handler) in enumerate(self._extension_routes):
            view = self.schema_constructor(**options)(handler)
            endpoint = endpoint or f"architect_custom_{index}_{handler.__name__}"
            if "." in endpoint:
                raise ValueError("Managed route endpoint names must not contain dots")
            view.__name__ = endpoint
            self._register_extension_route(path, methods, endpoint, standardise_response(view))
        for index, definition in enumerate(self._extension_actions):
            self._register_action(index, *definition)

    def _register_action(self, index, model, name, methods, permission, options, handler):
        from flarchitect.database.operations import CrudService

        if self.api is None:
            raise ValueError("Model actions require automatic route generation (FULL_AUTO=True)")
        input_schema, output_schema = get_input_output_from_model_or_make(model)
        segments, _, _ = self.api._model_route_segments(model, input_schema, output_schema)
        if not segments:
            raise ValueError(f"Action {name!r} needs a canonical or alternate endpoint for {model.__name__}")
        policy = self.api._model_route_policy(model)
        if any(not self.api._model_route_method_allowed(method, policy) for method in methods):
            raise ValueError(f"Action {name!r} uses a method blocked by {model.__name__}'s route policy")
        from sqlalchemy import inspect

        pk_name = inspect(model).primary_key[0].key

        def invoke(**kwargs):
            session = g._flarchitect_extension_session
            service = CrudService(model, session)
            context = OperationContext(model, session, name, kwargs.get("deserialized_data") or {})
            obj = scoped_record(service, kwargs[pk_name], name)
            access_policy = service._get_access_policy()
            if request.method == "DELETE":
                service._ensure_can_delete(obj, policy=access_policy, action=name)
            elif request.method not in {"GET", "HEAD"}:
                service._ensure_can_update(obj, context.data, policy=access_policy, action=name)
            if permission is not None and not current_app.ensure_sync(permission)(obj, context):
                raise CustomHTTPException(403, "Forbidden")
            result = current_app.ensure_sync(handler)(obj, context)
            result = run_hooks("after_operation", result, context)
            if request.method not in {"GET", "HEAD"}:
                session.flush()
            return result

        prefix = self.get_config("API_PREFIX", "/api").rstrip("/")
        for segment in segments:
            for method in methods:
                route_options = dict(options)
                roles, any_of = self.api._resolve_roles_for_route(model=model, http_method=method, is_many=False, is_relation=False)
                route_options.setdefault("roles", roles or False)
                route_options.setdefault("roles_any_of", any_of)
                route_options.setdefault("output_schema", output_schema)
                route_options.setdefault("group_tag", model.__name__)
                route_options.setdefault("summary", handler.__doc__ or name.replace("_", " "))
                route_options.update(model=model, method=method)
                endpoint = f"architect_action_{index}_{method}_{segment.replace('/', '_')}"
                view = self.schema_constructor(**route_options)(invoke)
                # Give spec lookup an unambiguous function name per rule.
                view.__name__ = endpoint
                view = transactional(view, model, write=method != "GET")
                self._register_extension_route(f"{prefix}/{segment}/{get_url_pk(model)}/{name}", [method], endpoint, view)
