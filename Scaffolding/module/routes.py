"""API routes for the scaffolding example."""

from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from .extensions import db
from .models import User

api_bp = Blueprint("api", __name__)


@api_bp.post("/register")
def register() -> tuple[dict[str, str], int]:
    """Register a new user."""

    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return {"message": "Missing fields"}, 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return {"message": "User created"}, 201


@api_bp.post("/login")
def login() -> tuple[dict[str, str], int]:
    """Authenticate a user and return a JWT."""

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        token = create_access_token(identity=str(user.id))
        return {"access_token": token}, 200

    return {"message": "Invalid credentials"}, 401


@api_bp.get("/protected")
@jwt_required()
def protected() -> tuple[dict[str, int], int]:
    """Return the current user's identity."""

    user_id = int(get_jwt_identity())
    return {"user_id": user_id}, 200
