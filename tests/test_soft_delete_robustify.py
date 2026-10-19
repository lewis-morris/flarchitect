"""Regression coverage for collection soft-delete settings and pagination."""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flarchitect import Architect


@pytest.fixture()
def soft_collection():
    apps = []

    def make_client(mode="global", rows=None):
        app = Flask(__name__)
        app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            API_CREATE_DOCS=False,
        )
        db = SQLAlchemy(app)

        class Record(db.Model):
            __tablename__ = "records"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            deleted = db.Column(db.Boolean, nullable=False, default=False)

            class Meta:
                pass

        if mode == "meta":
            Record.Meta.soft_delete = True
            Record.Meta.soft_delete_attribute = "deleted"
            Record.Meta.soft_delete_values = (False, True)
        else:
            app.config.update(
                API_SOFT_DELETE=True,
                API_SOFT_DELETE_ATTRIBUTE="deleted",
                API_SOFT_DELETE_VALUES=(False, True),
            )
            if mode == "disabled":
                Record.Meta.soft_delete = False
        app.config["API_BASE_MODEL"] = db.Model
        with app.app_context():
            db.create_all()
            for ident, name, deleted in rows or [(1, "keep", False), (2, "keep", True), (3, "keep", False), (4, "other", False)]:
                db.session.add(Record(id=ident, name=name, deleted=deleted))
            db.session.commit()
            Architect(app=app)
        apps.append((app, db))
        return app.test_client()

    yield make_client
    for app, db in apps:
        with app.app_context():
            db.session.remove()
            db.drop_all()


def test_all_deleted_collection_has_zero_total(soft_collection):
    client = soft_collection(rows=[(1, "gone", True)])
    response = client.get("/api/records")
    assert response.status_code == 200
    assert response.json["value"] == []
    assert response.json["total_count"] == 0
    assert response.json["next_url"] is None


def test_mixed_collection_totals_and_navigation_use_visible_filtered_rows(soft_collection):
    client = soft_collection()
    first = client.get("/api/records?name__eq=keep&orderby=id&limit=1&page=1")
    assert first.status_code == 200
    assert [row["id"] for row in first.json["value"]] == [1]
    assert first.json["total_count"] == 2
    assert first.json["next_url"] is not None
    second = client.get(first.json["next_url"])
    assert second.status_code == 200
    assert [row["id"] for row in second.json["value"]] == [3]
    assert second.json["total_count"] == 2
    assert second.json["next_url"] is None
    assert second.json["previous_url"] is not None


@pytest.mark.parametrize("mode,expected_ids", [("meta", [1, 3, 4]), ("global", [1, 3, 4]), ("disabled", [1, 2, 3, 4])])
def test_collection_honors_model_metadata_and_global_fallback(soft_collection, mode, expected_ids):
    client = soft_collection(mode)
    response = client.get("/api/records?orderby=id")
    assert response.status_code == 200
    assert [row["id"] for row in response.json["value"]] == expected_ids
    assert response.json["total_count"] == len(expected_ids)


@pytest.mark.parametrize("value", ["1", "0"])
def test_include_deleted_preserves_existing_truthy_string_semantics(soft_collection, value):
    client = soft_collection()
    response = client.get(f"/api/records?include_deleted={value}&orderby=id")
    assert response.status_code == 200
    assert [row["id"] for row in response.json["value"]] == [1, 2, 3, 4]
    assert response.json["total_count"] == 4


def test_include_deleted_can_be_combined_with_field_filter(soft_collection):
    client = soft_collection("meta")
    response = client.get("/api/records?include_deleted=1&name__eq=keep&orderby=id")
    assert response.status_code == 200
    assert [row["id"] for row in response.json["value"]] == [1, 2, 3]
    assert response.json["total_count"] == 3
