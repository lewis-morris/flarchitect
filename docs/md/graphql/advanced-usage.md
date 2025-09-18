[← Back to GraphQL index](index.md)

# Advanced usage

## Custom type mappings
`flarchitect` maps common SQLAlchemy column types to Graphene scalars via the
`SQLA_TYPE_MAPPING` dictionary. Extend this mapping to support application
specific types:
```
from datetime import datetime
import graphene
from flarchitect.graphql import SQLA_TYPE_MAPPING

SQLA_TYPE_MAPPING[datetime] = graphene.DateTime
```

## Relationships
`create_schema_from_models` automatically inspects SQLAlchemy relationships
and adds fields returning the related object types. The example below links
`Item` to `Category` so a query for items can also retrieve the owning
category. Relationships are eagerly loaded using `joinedload` to avoid N+1
query issues.
```
class Category(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)

class Item(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)
    category_id = mapped_column(ForeignKey("category.id"))
    category = relationship(Category)
```
`Item` now exposes a `category` field and `Category` a `items` field. A
single request can retrieve nested data:
```
query {
    all_items {
        name
        category { name }
    }
}
```

## Filtering and pagination
Queries accept optional `limit` and `offset` arguments to page through large
datasets. Additional arguments can be introduced to perform simple filtering:
```
query {
    all_items(name: "Foo", limit: 5, offset: 10) {
        id
        name
    }
}
```

## CRUD mutations
`create_schema_from_models` exposes a full set of CRUD mutations out of the
box, letting clients insert, modify and remove records without manual schema
definitions.

