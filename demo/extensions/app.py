"""Run with python -m demo.extensions.app; SQLite data lasts for this process."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from flarchitect import Architect


def create_app():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite://", API_ADD_RELATIONS=False)

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

    @architect.hook(Order, "before_create")
    def tidy_name(order, context):
        order.name = order.name.strip()
        return order

    @architect.override(Order, "create")
    def create_order(data, context):
        return Order(name=data["name"].upper())

    @architect.action(Order, "approve")
    def approve_order(order, context):
        """Approve an order."""
        order.approved = True
        return order

    @architect.route("/health", auth=False)
    def health():
        return {"healthy": True}

    with app.app_context():
        db.create_all()
        architect.init_app(app)
    return app


if __name__ == "__main__":
    create_app().run()
