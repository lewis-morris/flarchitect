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
       all_items {
           id
           name
       }
   }

Visit ``/graphql`` in a browser to access the interactive GraphiQL editor, or
send HTTP ``POST`` requests with a ``query`` payload.

Relationships
-------------

``create_schema_from_models`` also exposes SQLAlchemy relationships. Nested
objects can be queried by traversing relationship fields. Given ``Parent`` and
``Child`` models:

.. code-block:: python

   class Parent(Base):
       __tablename__ = "parent"
       id: Mapped[int] = mapped_column(primary_key=True)
       children: Mapped[list["Child"]] = relationship(back_populates="parent")

   class Child(Base):
       __tablename__ = "child"
       id: Mapped[int] = mapped_column(primary_key=True)
       parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
       parent: Mapped[Parent] = relationship(back_populates="children")

The generated schema allows nested queries:

.. code-block:: graphql

   query {
       all_parents {
           id
           children { id }
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
