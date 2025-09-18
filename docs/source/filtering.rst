Filtering
=========

``flarchitect`` supports expressive, URL‑based filtering out of the box. This page
explains how to enable/disable filtering, the syntax for predicates, how to
combine conditions with AND/OR, and how to filter across joined models.

Enable or disable filtering
---------------------------

Filtering is enabled by default. Disable it globally or per model when you want
fixed endpoints without ad‑hoc query predicates.

.. code:: python

    # Global toggle (default True)
    app.config["API_ALLOW_FILTERS"] = True  # or False

    # Per‑model override
    class Book(db.Model):
        class Meta:
            allow_filters = True  # or False

Basic syntax
------------

Use the pattern ``<field>__<operator>=<value>``. Multiple filters combine with
AND by default.

.. code:: text

    GET /api/books?title__ilike=python&publication_date__ge=2020-01-01

Supported operators
-------------------

The following operators are available. Values are automatically converted to
the correct type where possible (e.g. integers, floats, dates). ``like``/``ilike``
wrap the value with ``%`` for substring matching.

==================  =========================================================
Operator            Description / Example
==================  =========================================================
``eq``              Equals. ``author_id__eq=1``
``ne`` / ``neq``    Not equal. ``rating__ne=5``
``lt``              Less than. ``price__lt=20``
``le``              Less than or equal. ``published_year__le=2010``
``gt``              Greater than. ``pages__gt=300``
``ge``              Greater than or equal. ``stock__ge=1``
``in``              In list. ``id__in=(1,2,3)``
``nin``             Not in list. ``status__nin=(archived,draft)``
``like``            Case‑sensitive substring. ``title__like=Python``
``ilike``           Case‑insensitive substring. ``name__ilike=acme``
==================  =========================================================

OR conditions
-------------

To express OR logic, wrap a comma‑separated list of full conditions inside a
single ``or[ ... ]`` parameter. The contained conditions are grouped with one
``OR`` clause and combined with any other filters using ``AND``.

.. code:: text

    # Authors with id 2 OR 3
    GET /api/authors?or[id__eq=2,id__eq=3]

Filtering across joins
----------------------

When you join related models, you can qualify a filter with the table name using
``table.column__operator=value``. Combine this with ``join`` to constrain by a
related model’s columns.

.. code:: text

    # Join customers and filter by customer name (case‑insensitive)
    GET /api/invoices?join=customer&customer.name__ilike=acme

    # Multiple filters still combine with AND
    GET /api/invoices?join=customer&customer.name__ilike=acme&total__ge=100

Tips and combinations
---------------------

- Filters compose with other query features like :doc:`joining <joining>`,
  sorting (``order_by``), pagination (``page``/``limit``), and dynamic nesting
  via :doc:`custom_serialization` (e.g. ``dump=dynamic``).
- For list comparisons (``in``/``nin``) pass values in parentheses, comma‑separated
  as shown above.
- When joining one‑to‑many relationships, pagination operates over distinct base
  rows; see :doc:`joining` for details on join semantics.

Examples
--------

.. code:: text

    # Books with "python" in the title, published since 2020
    GET /api/books?title__ilike=python&publication_date__ge=2020-01-01

    # Invoices whose customer name contains "Acme" and total >= 100
    GET /api/invoices?join=customer&customer.name__ilike=acme&total__ge=100

    # Authors with id 2 OR 3, newest first
    GET /api/authors?or[id__eq=2,id__eq=3]&order_by=-id

