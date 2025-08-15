GraphQL
=======

`flarchitect` can expose SQLAlchemy models through a GraphQL API. The
:func:`flarchitect.graphql.create_schema_from_models` helper builds a Graphene
schema from your models, while :meth:`flarchitect.Architect.init_graphql`
registers a ``/graphql`` endpoint and documents it in the OpenAPI spec.

Quick start
-----------

The simplest way to enable GraphQL is to feed your models to
``create_schema_from_models`` and register the resulting schema with the
architect:

.. code-block:: python

   schema = create_schema_from_models([User], db.session)
   architect.init_graphql(schema=schema)

The generated schema provides CRUD-style queries and mutations for each model.
An ``all_items`` query returns every ``Item`` and a ``create_item`` mutation adds
a new record.

Example create mutation
~~~~~~~~~~~~~~~~~~~~~~~

``create_schema_from_models`` automatically generates ``create_<table>``,
``update_<table>`` and ``delete_<table>`` mutations for each model. The
``create`` mutation accepts all non-primary-key columns as arguments. The
example below creates a new ``Item``:

.. code-block:: graphql

   mutation {
       create_item(name: "Foo") {
           id
           name
       }
   }

Example update mutation
~~~~~~~~~~~~~~~~~~~~~~~

Updating a record requires the primary key and any columns to change. The
following mutation updates the ``Item`` created above:

.. code-block:: graphql

   mutation {
       update_item(id: 1, name: "Bar") {
           id
           name
       }
   }

Example delete mutation
~~~~~~~~~~~~~~~~~~~~~~~

Deletion requires only the primary key and returns a boolean flag indicating
success:

.. code-block:: graphql

   mutation {
       delete_item(id: 1)
   }

Example query
~~~~~~~~~~~~~

.. code-block:: graphql

   query {
       all_items {
           id
           name
       }
   }

Visit ``/graphql`` in a browser to access the interactive GraphiQL editor, or
send HTTP ``POST`` requests with a ``query`` payload.

Tips and trade-offs
-------------------

GraphQL offers flexible queries and reduces the number of HTTP round-trips, but
it also introduces additional complexity. Responses are not cacheable by
standard HTTP mechanisms, and naïve schemas can allow very expensive queries.
Ensure resolvers validate user input and consider depth limiting or query cost
analysis for production deployments.

Further examples are available in :mod:`demo.graphql`.
