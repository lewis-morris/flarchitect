Grouping & Aggregation
======================

``flarchitect`` can summarise datasets with SQL ``GROUP BY`` clauses and aggregate
functions when explicitly enabled. This guide covers the configuration
flags, supported query syntax, and how the responses are shaped.

Enable support
--------------

Two configuration values control the feature set:

.. code-block:: python

    class Config:
        API_ALLOW_GROUPBY = True
        API_ALLOW_AGGREGATION = True

Both flags can be applied globally on the Flask config (``API_`` prefix) or
per model via the ``Meta`` class (lowercase without the prefix). Aggregation
builds on grouping, so enable both together when you expect to run
summaries from the same endpoint. See :doc:`configuration` for the
configuration hierarchy.

Group results
-------------

Once ``API_ALLOW_GROUPBY`` is active, clients can pass a comma-separated
``groupby`` query parameter to select columns for the ``GROUP BY`` clause.
Columns may be referenced by name or fully qualified when joins are
involved::

    GET /api/books?groupby=author_id
    GET /api/invoices?join=customer&groupby=customer.id,customer.currency

When grouping is used without aggregates the result set contains the
unique combinations of the requested fields. To return those fields
explicitly, combine ``groupby`` with ``fields=``::

    GET /api/books?fields=author_id,title&groupby=author_id

Aggregate functions
-------------------

``API_ALLOW_AGGREGATION`` unlocks computed values such as totals and
counts. Aggregates are expressed in the query string using the pattern::

    <column>|<label>__<function>=<placeholder>

Where:

* ``column`` is the base or joined column to aggregate. Qualify the column
  (``table.column``) when grouping across joins.
* ``label`` is optional. If omitted the API infers ``<column>_<function>``.
* ``function`` is one of ``sum``, ``count``, ``avg``, ``min`` or ``max``.
* ``placeholder`` can be any value (it is ignored); use ``=1`` for clarity.

Examples::

    GET /api/books?groupby=author_id&id|book_count__count=1
    GET /api/invoices?join=customer&groupby=customer.id,total|revenue__sum=1
    GET /api/payments?amount|avg_amount__avg=1

Responses include scalar attributes for each aggregate label alongside any
selected grouping columns::

    {
      "status_code": 200,
      "value": [
        {"author_id": 1, "book_count": 3},
        {"author_id": 2, "book_count": 5}
      ]
    }

Combining with joins and filters
--------------------------------

Grouping and aggregation work with joins, filters, ``fields`` selection and
ordering:

* Join related tables with ``join=`` before referencing joined columns in
  ``groupby`` or aggregate expressions.
* Apply filters (`API_ALLOW_FILTERS`) to narrow the input rows prior to
  aggregation.
* Use ``order_by`` to sort by either grouping columns or aggregate labels.

Spec documentation
------------------

When either flag is enabled ``flarchitect`` adds explanatory cards to the
OpenAPI/Redoc documentation and surfaces the parameters in the generated
schema so consumers see the available query options.

For a concise summary of the feature flags, refer back to
:doc:`advanced_configuration` and the full option table in
:doc:`configuration`.
