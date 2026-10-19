"""Public extension contracts exercised through real Flask requests and SQLite."""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy.orm import DeclarativeBase

from flarchitect import Architect, OperationContext


@pytest.fixture
def setup():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite://", API_CREATE_DOCS=True, API_ADD_RELATIONS=False)

    class Base(DeclarativeBase):
        pass

    db = SQLAlchemy(app, model_class=Base)

    class Order(db.Model):
        __tablename__ = "orders"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        approved = db.Column(db.Boolean, default=False)

        class Meta:
            tag = "Orders"

    app.config["API_BASE_MODEL"] = db.Model
    architect = Architect()
    with app.app_context():
        db.create_all()
        db.session.add_all([Order(name="visible"), Order(name="hidden")])
        db.session.commit()

    def start():
        with app.app_context():
            architect.init_app(app)
        return app.test_client()

    yield app, db, Order, architect, start
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_action_keeps_crud_and_documents_path(setup):
    app, db, Order, api, start = setup

    @api.action(Order, "approve")
    def approve(order, context):
        assert isinstance(context, OperationContext)
        order.approved = True
        return order

    client = start()
    response = client.post("/api/orders/1/approve")
    assert response.status_code == 200, response.json
    assert response.json["value"]["approved"] is True
    assert client.get("/api/orders/1").json["value"]["approved"] is True
    assert len(client.get("/api/orders").json["value"]) == 2
    spec = client.get("/docs/apispec.json").json
    assert "post" in spec["paths"]["/api/orders/{id}/approve"]


def test_action_validates_and_rolls_back_handler_failure(setup):
    app, db, Order, api, start = setup

    class Input(Schema):
        reason = fields.String(required=True)

    @api.action(Order, "approve", input_schema=Input)
    def approve(order, context):
        order.approved = True
        context.session.flush()
        raise ValueError("business failure")

    client = start()
    assert client.post("/api/orders/1/approve", json={}).status_code == 400
    assert client.post("/api/orders/1/approve", json={"reason": "ok"}).status_code == 500
    with app.app_context():
        assert db.session.get(Order, 1).approved is False


def test_action_scope_write_policy_and_explicit_permission(setup):
    app, db, Order, api, start = setup

    class Policy:
        def scope_query(self, query, **kwargs):
            return query.filter(Order.id == 1)

        def can_update(self, obj, **kwargs):
            return False

    app.config["API_ACCESS_POLICY"] = Policy
    called = []

    @api.action(Order, "approve", permission=lambda obj, context: True)
    def approve(order, context):
        called.append(order.id)
        return order

    client = start()
    assert client.post("/api/orders/2/approve").status_code == 404
    assert client.post("/api/orders/1/approve").status_code == 403
    assert called == []


def test_explicit_permission_denies_action(setup):
    app, db, Order, api, start = setup

    @api.action(Order, "approve", permission=lambda obj, context: False)
    def approve(order, context):
        pytest.fail("permission must run before handler")

    assert start().post("/api/orders/1/approve").status_code == 403


def test_override_create_preserves_validation_and_other_operations(setup):
    app, db, Order, api, start = setup

    @api.override(Order, "create")
    def create(data, context):
        return Order(name=data["name"].upper())

    client = start()
    assert client.post("/api/orders", json={}).status_code == 400
    response = client.post("/api/orders", json={"name": "custom"})
    assert response.status_code < 300, response.json
    assert response.json["value"]["name"] == "CUSTOM"
    identity = response.json["value"]["id"]
    assert identity is not None
    assert client.patch(f"/api/orders/{identity}", json={"name": "patched"}).status_code == 200
    assert client.get(f"/api/orders/{identity}").json["value"]["name"] == "patched"


def test_override_create_policy_denial(setup):
    app, db, Order, api, start = setup
    app.config["API_ACCESS_POLICY"] = {"can_create": lambda **kwargs: False}

    @api.override(Order, "create")
    def create(data, context):
        pytest.fail("policy must run first")

    assert start().post("/api/orders", json={"name": "custom"}).status_code == 403


@pytest.mark.parametrize("operation,method", [("update", "patch"), ("delete", "delete")])
def test_override_mutation_scoped_and_atomic(setup, operation, method):
    app, db, Order, api, start = setup
    app.config["API_ACCESS_POLICY"] = {"scope_query": lambda query, **kwargs: query.filter(Order.id == 1)}

    @api.override(Order, operation)
    def change(order, context):
        order.name = "changed"
        context.session.flush()
        raise ValueError("rollback")

    client = start()
    assert getattr(client, method)("/api/orders/2", json={"name": "x"}).status_code == 404
    assert getattr(client, method)("/api/orders/1", json={"name": "x"}).status_code == 500
    with app.app_context():
        assert db.session.get(Order, 1).name == "visible"


def test_list_override_retains_scope_count_and_pagination(setup):
    app, db, Order, api, start = setup
    app.config["API_ACCESS_POLICY"] = {"scope_query": lambda query, **kwargs: query.filter(Order.id == 1)}

    @api.override(Order, "list")
    def listing(query, context):
        # A fresh query must not remove the application's visibility restriction.
        return context.session.query(Order)

    response = start().get("/api/orders?limit=1")
    assert response.status_code == 200, response.json
    assert [item["name"] for item in response.json["value"]] == ["visible"]
    assert response.json["total_count"] == 1


def test_retrieve_override(setup):
    app, db, Order, api, start = setup

    @api.override(Order, "retrieve")
    def retrieve(order, context):
        return {"id": order.id, "name": order.name.upper(), "approved": order.approved}

    client = start()
    assert client.get("/api/orders/1").json["value"]["name"] == "VISIBLE"
    assert client.get("/api/orders/999").status_code == 404


def test_hooks_and_standalone_route(setup):
    app, db, Order, api, start = setup
    events = []

    @api.hook(Order, "before_create")
    def label(order, context):
        order.name += " first"
        events.append(context.operation)

    @api.hook(Order, "before_create")
    def label_again(order, context):
        order.name += " second"
        return order

    @api.hook(Order, "query")
    def visible(query, context):
        return query.filter(Order.name != "hidden")

    @api.route("/health", auth=False)
    def health():
        return {"healthy": True}

    client = start()
    result = client.post("/api/orders", json={"name": "new"})
    assert result.json["value"]["name"] == "new first second"
    assert events == ["create"]
    assert len(client.get("/api/orders").json["value"]) == 2
    assert client.get("/health").json["value"] == {"healthy": True}
    assert "/health" in client.get("/docs/apispec.json").json["paths"]


def test_registration_errors_are_explicit(setup):
    app, db, Order, api, start = setup
    with pytest.raises(ValueError, match="Unknown hook"):
        api.hook(Order, "typo")
    with pytest.raises(ValueError, match="Unknown operation"):
        api.override(Order, "typo")
    api.override(Order, "create")(lambda data, context: Order(**data))
    with pytest.raises(ValueError, match="already registered"):
        api.override(Order, "create")(lambda data, context: Order(**data))
    start()
    with pytest.raises(RuntimeError, match="before"):
        api.action(Order, "late")


def test_unused_override_and_route_collision(setup):
    app, db, Order, api, start = setup
    Order.Meta.register_canonical_routes = False
    api.override(Order, "create")(lambda data, context: Order(**data))
    with pytest.raises(ValueError, match="No generated route"):
        start()


def test_route_collision(setup):
    app, db, Order, api, start = setup
    api.route("/api/orders", methods=["GET"])(lambda: {})
    with pytest.raises(ValueError, match="already registered"):
        start()


def test_action_input_and_custom_output(setup):
    app, db, Order, api, start = setup

    class Input(Schema):
        name = fields.String(required=True)

    @api.action(Order, "rename", input_schema=Input, output_schema=None)
    def rename(order, context):
        order.name = context.data["name"]
        return {"renamed": order.name}

    client = start()
    assert client.post("/api/orders/1/rename", json={"name": "new"}).json["value"] == {"renamed": "new"}
    assert client.get("/api/orders/1").json["value"]["name"] == "new"


def test_action_inherits_auth_and_model_roles(setup):
    from types import SimpleNamespace
    from flask import request
    from flarchitect.authentication.user import set_current_user

    app, db, Order, api, start = setup
    app.config.update(SECRET_KEY="test", API_AUTHENTICATE_METHOD=["custom"])

    def authenticate():
        role = request.headers.get("X-Role")
        if role:
            set_current_user(SimpleNamespace(id=1, roles=[role]))
            return True
        return False

    app.config["API_CUSTOM_AUTH"] = authenticate
    Order.Meta.roles_required = ["manager"]

    @api.action(Order, "approve")
    def approve(order, context):
        order.approved = True
        return order

    client = start()
    assert client.post("/api/orders/1/approve").status_code == 401
    assert client.post("/api/orders/1/approve", headers={"X-Role": "reader"}).status_code == 403
    assert client.post("/api/orders/1/approve", headers={"X-Role": "manager"}).status_code == 200


def test_action_alternate_endpoint_and_prefix(setup):
    app, db, Order, api, start = setup
    app.config["API_PREFIX"] = "/api/v2"
    Order.Meta.register_canonical_routes = False
    Order.Meta.endpoint = ["records/orders", "other-orders"]

    @api.action(Order, "approve")
    def approve(order, context):
        order.approved = True
        return order

    client = start()
    assert client.post("/api/v2/orders/1/approve").status_code == 404
    for path in ["records/orders", "other-orders"]:
        assert client.post(f"/api/v2/{path}/1/approve").status_code == 200
        assert f"/api/v2/{path}/{{id}}/approve" in client.get("/docs/apispec.json").json["paths"]


def test_read_only_model_rejects_write_action(setup):
    app, db, Order, api, start = setup
    Order.Meta.read_only = True
    api.action(Order, "approve")(lambda order, context: order)
    with pytest.raises(ValueError, match="blocked"):
        start()


def test_get_action_never_persists_writes(setup):
    app, db, Order, api, start = setup

    @api.action(Order, "preview", methods=["GET"])
    def preview(order, context):
        order.approved = True
        return order

    client = start()
    assert client.get("/api/orders/1/preview").json["value"]["approved"] is True
    assert client.get("/api/orders/1").json["value"]["approved"] is False


def test_failed_response_rolls_back(setup):
    app, db, Order, api, start = setup

    @api.action(Order, "approve", output_schema=None)
    def approve(order, context):
        order.approved = True
        return {"problem": "not ready"}, 409

    client = start()
    assert client.post("/api/orders/1/approve").status_code == 409
    with app.app_context():
        assert db.session.get(Order, 1).approved is False


def test_serialization_failure_rolls_back(setup):
    app, db, Order, api, start = setup

    class BrokenOutput(Schema):
        value = fields.Method("explode")

        def explode(self, obj):
            raise ValueError("cannot serialize")

    @api.action(Order, "approve", output_schema=BrokenOutput)
    def approve(order, context):
        order.approved = True
        return order

    client = start()
    assert client.post("/api/orders/1/approve").status_code >= 400
    with app.app_context():
        assert db.session.get(Order, 1).approved is False


def test_successful_update_and_delete_overrides(setup):
    app, db, Order, api, start = setup

    @api.override(Order, "update")
    def update(order, context):
        order.name = context.data["name"].upper()
        return order

    @api.override(Order, "delete")
    def delete(order, context):
        context.session.delete(order)

    client = start()
    assert client.patch("/api/orders/1", json={"name": "changed"}).json["value"]["name"] == "CHANGED"
    assert client.get("/api/orders/1").json["value"]["name"] == "CHANGED"
    assert client.delete("/api/orders/1").status_code == 200
    assert client.get("/api/orders/1").status_code == 404


def test_before_update_and_delete_hooks_and_failure_rollback(setup):
    app, db, Order, api, start = setup

    @api.hook(Order, "before_update")
    def validate(order, context):
        context.session.flush()
        raise ValueError("invalid")

    @api.hook(Order, "before_delete")
    def protect(order, context):
        raise ValueError("keep it")

    client = start()
    assert client.patch("/api/orders/1", json={"name": "bad"}).status_code == 500
    assert client.delete("/api/orders/1").status_code == 500
    with app.app_context():
        assert db.session.get(Order, 1).name == "visible"


def test_managed_route_factory_without_auto_routes():
    api = Architect()

    @api.route("/echo/<int:number>", methods=["POST"], auth=False)
    def echo(number):
        return {"number": number}

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False)
    with app.app_context():
        api.init_app(app)
    assert app.test_client().post("/echo/5").json["value"] == {"number": 5}
    assert "/echo/{number}" in app.test_client().get("/docs/apispec.json").json["paths"]


def test_demo_runs_without_extra_setup():
    from demo.extensions.app import create_app

    client = create_app().test_client()
    created = client.post("/api/orders", json={"name": " sample "})
    assert created.json["value"]["name"] == "SAMPLE"
    identity = created.json["value"]["id"]
    assert client.post(f"/api/orders/{identity}/approve").json["value"]["approved"] is True
    assert client.get("/health").status_code == 200


def test_after_operation_receives_records_without_pagination_internals(setup):
    app, db, Order, api, start = setup
    seen = []

    @api.hook(Order, "after_operation")
    def change_response(value, context):
        if context.operation == "list":
            assert isinstance(value, list)
            seen.append(context.operation)
            return [{"id": obj.id, "name": obj.name.upper()} for obj in value]
        return value

    response = start().get("/api/orders?limit=1")
    assert response.json["value"][0]["name"] == "VISIBLE"
    assert response.json["total_count"] == 2
    assert seen == ["list"]


def test_zero_identity_action(setup):
    app, db, Order, api, start = setup
    with app.app_context():
        db.session.add(Order(id=0, name="zero"))
        db.session.commit()

    @api.action(Order, "approve")
    def approve(order, context):
        order.approved = True
        return order

    assert start().post("/api/orders/0/approve").json["value"]["approved"] is True


def test_action_duplicate_and_bad_method_registration(setup):
    app, db, Order, api, start = setup
    api.action(Order, "approve")(lambda order, context: order)
    with pytest.raises(ValueError, match="already registered"):
        api.action(Order, "approve")(lambda order, context: order)
    with pytest.raises(ValueError):
        api.action(Order, "bad/path")
    with pytest.raises(ValueError):
        api.action(Order, "empty", methods=[])
    with pytest.raises(ValueError):
        api.route("/empty", methods=[])


def test_managed_route_auth_errors_without_auto_routes():
    api = Architect()

    @api.route("/private", auth=True)
    def private():
        return {"private": True}

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False, SECRET_KEY="test", API_AUTHENTICATE_METHOD=["custom"], API_CUSTOM_AUTH=lambda: False)
    with app.app_context():
        api.init_app(app)
    assert app.test_client().get("/private").status_code == 401


def test_zero_identity_override(setup):
    app, db, Order, api, start = setup
    with app.app_context():
        db.session.add(Order(id=0, name="zero"))
        db.session.commit()

    @api.override(Order, "update")
    def update(order, context):
        order.name = context.data["name"]
        return order

    @api.override(Order, "retrieve")
    def retrieve(order, context):
        return order

    client = start()
    assert client.patch("/api/orders/0", json={"name": "new"}).status_code == 200
    assert client.get("/api/orders/0").json["value"]["name"] == "new"


def test_action_model_response_status_is_preserved_and_rolls_back(setup):
    app, db, Order, api, start = setup

    @api.action(Order, "approve")
    def approve(order, context):
        order.approved = True
        return order, 409

    client = start()
    response = client.post("/api/orders/1/approve")
    assert response.status_code == 409
    with app.app_context():
        assert db.session.get(Order, 1).approved is False


def test_extensions_support_named_string_primary_keys():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite://", API_CREATE_DOCS=False, API_ADD_RELATIONS=False)

    class Base(DeclarativeBase):
        pass

    db = SQLAlchemy(app, model_class=Base)

    class Product(db.Model):
        __tablename__ = "products"
        sku = db.Column(db.String, primary_key=True)
        name = db.Column(db.String, nullable=False)

        class Meta:
            tag = "Products"

    app.config["API_BASE_MODEL"] = db.Model
    api = Architect()

    @api.override(Product, "retrieve")
    def retrieve(product, context):
        return product

    @api.override(Product, "update")
    def update(product, context):
        product.name = context.data["name"]
        return product

    @api.action(Product, "rename")
    def rename(product, context):
        product.name = "action"
        return product

    with app.app_context():
        db.create_all()
        db.session.add(Product(sku="ABC", name="before"))
        db.session.commit()
        api.init_app(app)
    client = app.test_client()
    assert client.get("/api/products/ABC").json["value"]["name"] == "before"
    assert client.patch("/api/products/ABC", json={"name": "override"}).json["value"]["name"] == "override"
    assert client.post("/api/products/ABC/rename").json["value"]["name"] == "action"
    assert client.get("/api/products/ABC").json["value"]["name"] == "action"
