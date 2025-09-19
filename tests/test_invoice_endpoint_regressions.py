from __future__ import annotations

from datetime import datetime

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Declarative base for invoice regression fixtures."""


db = SQLAlchemy(model_class=BaseModel)


class Customer(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")


class Payment(db.Model):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")


class Invoice(db.Model):
    __tablename__ = "invoices"

    class Meta:
        tag_group = "Billing"
        tag = "Invoice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    customer: Mapped[Customer] = relationship(Customer, back_populates="invoices")
    payments: Mapped[list[Payment]] = relationship(Payment, back_populates="invoice", cascade="all, delete-orphan")
    lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

    @hybrid_property
    def total_outstanding(self) -> int:
        paid_total = sum(payment.amount_cents for payment in self.payments)
        return self.total_cents - paid_total

    @total_outstanding.expression
    def total_outstanding(cls):
        payment_sum = (
            select(func.coalesce(func.sum(Payment.amount_cents), 0))
            .where(Payment.invoice_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )
        return cls.total_cents - payment_sum


class InvoiceLine(db.Model):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    invoice: Mapped[Invoice] = relationship(Invoice, back_populates="lines")


@pytest.fixture()
def app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Invoices API",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_ALLOW_JOIN=True,
        API_ALLOW_GROUPBY=True,
        API_ALLOW_AGGREGATION=True,
        API_ALLOW_ORDER_BY=True,
        API_SERIALIZATION_TYPE="json",
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()

        acme = Customer(name="Acme Corp")
        globex = Customer(name="Globex")

        invoice_early = Invoice(
            customer=acme,
            date=datetime(2024, 1, 15),
            paid=False,
            total_cents=12_000,
            lines=[InvoiceLine(amount_cents=7_000), InvoiceLine(amount_cents=5_000)],
            payments=[Payment(amount_cents=2_000, paid_at=datetime(2024, 1, 20))],
        )
        invoice_mid = Invoice(
            customer=acme,
            date=datetime(2024, 2, 10),
            paid=True,
            total_cents=5_000,
            lines=[InvoiceLine(amount_cents=5_000)],
            payments=[Payment(amount_cents=5_000, paid_at=datetime(2024, 2, 15))],
        )
        invoice_latest = Invoice(
            customer=globex,
            date=datetime(2024, 3, 5),
            paid=True,
            total_cents=8_000,
            lines=[InvoiceLine(amount_cents=8_000)],
            payments=[Payment(amount_cents=3_000, paid_at=datetime(2024, 3, 7))],
        )

        db.session.add_all([acme, globex, invoice_early, invoice_mid, invoice_latest])
        db.session.commit()

        Architect(app)

    yield app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_hybrid_aggregate_uses_expression(client) -> None:
    response = client.get("/api/invoices?groupby=paid&total_outstanding|outstanding_total__sum=1")
    assert response.status_code == 200

    payload = response.get_json()
    rows = payload["value"]

    grouped = {bool(row["paid"]): row["outstanding_total"] for row in rows}
    assert grouped[False] == 10_000
    assert grouped[True] == 5_000


def test_join_tokens_normalised_for_column_map(client) -> None:
    response = client.get("/api/invoices?join=invoice-lines,payments,customer&order_by=-date")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["total_count"] == 3

    dates = [entry["date"] for entry in payload["value"]]
    assert dates and dates[0].startswith("2024-03-05")
