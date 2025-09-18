# SQLAlchemy Models

`flarchitect` builds APIs directly from your SQLAlchemy models. To expose a model:
- Inherit from your configured base model.
- Add a `Meta` inner class (required for auto‑registration). Optionally include `tag` and `tag_group` to influence how endpoints are grouped in the docs.
- Define your fields and relationships as you normally would; nested relationships are handled automatically.
Example:
```
class Author(BaseModel):
    __tablename__ = "author"

    class Meta:
        tag = "Author"
        tag_group = "People/Companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
```
That's all that's required to make the model available through the generated API.
> **Warning**
> Models without a `Meta` inner class are not auto‑registered. They will be ignored by route generation and will not appear in the documentation. The `tag` and `tag_group` attributes are optional; add them if you want to control documentation grouping.

## Sections

- [Dump types](dump-types.md)
- [Nested relationship dumping](nested-relationship-dumping.md)
