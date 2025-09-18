Joining Related Resources
=========================

``flarchitect`` can inline related objects in responses and filter across
relationships by joining tables at query time. This page explains how to enable
joins, how the ``join`` tokens are normalised, how to control SQL join
semantics via ``join_type``, and how this interacts with serialisation.

Enable joins
------------

Joins are disabled by default. Enable them globally or per‑model:

.. code:: python

    app.config["API_ALLOW_JOIN"] = True

    class Book(db.Model):
        class Meta:
            allow_join = True


Normalised join tokens
----------------------

The ``join`` query parameter accepts a comma‑separated list of relationship
names. Each token is normalised so that clients have flexibility when naming
relations:

- Case‑insensitive; leading/trailing whitespace is ignored.
- Hyphens are treated as underscores (``invoice-lines`` → ``invoice_lines``).
- Matches any of the following for each relationship:
  - the endpoint name (pluralised, using ``API_ENDPOINT_CASE``),
  - the relationship key in endpoint case (often singular),
  - the raw SQLAlchemy relationship key.
- Singular/plural variants are resolved automatically.

Examples::

    # join using endpoint names (plural)
    GET /api/books?join=authors

    # join using relationship keys (snake case)
    GET /api/books?join=author

    # multiple joins, any separator: kebab, snake, singular/plural
    GET /api/invoices?join=invoice-lines,payment,payments,customer,customers


Choosing SQL join semantics
---------------------------

Use ``join_type`` to control the SQL join operator applied to each related
table. Supported values:

- ``inner`` (default)
- ``left`` (left outer join)
- ``outer`` (alias of left for ORM compatibility)
- ``right`` (best‑effort right join; ORM may emulate using an outer join)

Example::

    # include base rows even when they have no related books
    GET /api/publishers?join=books&join_type=left

Invalid values yield ``400 Bad Request``.


Pagination with joins
---------------------

Joining one‑to‑many relationships multiplies result rows at the SQL level. To
keep pagination intuitive, flarchitect applies ``DISTINCT`` to the base entity
whenever you request joins without a custom ``fields``/``groupby``/aggregation
projection. This ensures that ``limit`` and ``total_count`` operate over
distinct base rows rather than multiplied join rows.


Serialisation and joins
-----------------------

Joining models does not by itself inline related objects. See
:doc:`custom_serialization` for how to control nested output. In brief:

- ``dump=url`` (default) serialises relationships as URLs.
- ``dump=json`` always nests related objects.
- ``dump=dynamic`` nests only relationships listed in ``join``.
- ``dump=hybrid`` nests to‑one relationships; collections remain URLs.

Example::

    GET /api/books?dump=dynamic&join=author,publisher

Expected output (example)
-------------------------

With ``dump=dynamic`` and ``join=invoice-lines,payments,customer`` you can
expect nested arrays/objects for those relations while other relationships
remain URLs. Example shape::

    {
      "status_code": 200,
      "total_count": 123,
      "value": [
        {
          "id": 1,
          "number": "INV-0001",
          "date": "2025-09-01",
          "invoice_lines": [
            {"id": 10, "description": "Widget", "quantity": 2, "unit_price": 9.99},
            {"id": 11, "description": "Gadget", "quantity": 1, "unit_price": 19.99}
          ],
          "payments": [
            {"id": 5, "amount": 29.98, "method": "card", "date": "2025-09-05"}
          ],
          "customer": {"id": 7, "name": "Acme Ltd", "email": "billing@acme.test"}
        }
      ]
    }
