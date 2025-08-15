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
An ``all_items`` query returns every ``Item`` and accepts optional column
arguments for filtering. Pagination is supported via ``limit`` and
``offset`` arguments, and a ``create_item`` mutation adds a new record.

Type mapping
------------

``create_schema_from_models`` converts SQLAlchemy column types into Graphene
scalars using :data:`flarchitect.graphql.SQLA_TYPE_MAPPING`. Out of the box it
supports ``Integer``, ``String``, ``Boolean``, ``Float``, ``Date``, ``DateTime``,
``Numeric``, ``JSON`` and ``UUID`` columns. Custom or proprietary SQLAlchemy
types can be mapped by providing a ``type_mapping`` override:

.. code-block:: python

   schema = create_schema_from_models(
       [User], db.session, type_mapping={MyType: graphene.String}
   )

Example mutation
~~~~~~~~~~~~~~~~

``create_schema_from_models`` automatically generates a ``create_<table>``
mutation for each model. The mutation accepts all non-primary-key columns as
arguments. The example below creates a new ``Item``:

.. code-block:: graphql

   mutation {
       create_item(name: "Foo") {
           id
           name
       }
   }

Example query
~~~~~~~~~~~~~

.. code-block:: graphql

   query {
       all_items(name: "Foo", limit: 1, offset: 0) {
           id
           name
       }
   }

Filtering on any column is supported. The following returns all ``Item``
objects with ``name`` equal to ``"Bar"``:

.. code-block:: graphql

   query {
       all_items(name: "Bar") {
           id
           name
       }
   }

Visit ``/graphql`` in a browser to access the interactive GraphiQL editor
served on ``GET`` requests. Programmatic clients should send HTTP ``POST``
requests with a ``query`` payload.

Advanced usage
--------------

Custom type mappings
~~~~~~~~~~~~~~~~~~~~

``flarchitect`` maps common SQLAlchemy column types to Graphene scalars via the
``SQLA_TYPE_MAPPING`` dictionary. Extend this mapping to support application
specific types:

.. code-block:: python

   from datetime import datetime
   import graphene
   from flarchitect.graphql import SQLA_TYPE_MAPPING

   SQLA_TYPE_MAPPING[datetime] = graphene.DateTime

Relationships
~~~~~~~~~~~~~

Model relationships can be exposed by adding fields that return related object
types. The example below links ``Item`` to ``Category`` so a query for items can
also retrieve the owning category:

.. code-block:: python

   class Category(db.Model):
       id = mapped_column(Integer, primary_key=True)
       name = mapped_column(String)

   class Item(db.Model):
       id = mapped_column(Integer, primary_key=True)
       name = mapped_column(String)
       category_id = mapped_column(ForeignKey("category.id"))
       category = relationship(Category)

Filtering and pagination
~~~~~~~~~~~~~~~~~~~~~~~~

Queries accept optional ``limit`` and ``offset`` arguments to page through large
datasets. Additional arguments can be introduced to perform simple filtering:

.. code-block:: graphql

   query {
       all_items(name: "Foo", limit: 5, offset: 10) {
           id
           name
       }
   }

CRUD mutations
~~~~~~~~~~~~~~

Beyond the automatically generated ``create_<table>`` mutation you can extend
the schema with ``update_`` and ``delete_`` operations. These mutations modify
existing records or remove them entirely:

.. code-block:: graphql

   mutation {
       update_item(id: 1, name: "Bar") {
           id
           name
       }
   }


Tips and trade-offs
-------------------

GraphQL offers flexible queries and reduces the number of HTTP round-trips, but
it also introduces additional complexity. Responses are not cacheable by
standard HTTP mechanisms, and naïve schemas can allow very expensive queries.
Ensure resolvers validate user input and consider depth limiting or query cost
analysis for production deployments.

Further examples are available in :mod:`demo.graphql`.
