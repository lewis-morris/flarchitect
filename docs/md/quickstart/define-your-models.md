[← Back to Quick Start index](index.md)

# Define your models
Define your models using SQLAlchemy. `flarchitect` automatically resolves
the active database session, whether you're using Flask-SQLAlchemy or plain
SQLAlchemy, so no special `get_session` method is required.
```
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class BaseModel(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=BaseModel)

class Author(db.Model):
    __tablename__ = "author"

    class Meta:  # required for auto-registration; fields inside are optional
        # Optional docs grouping:
        # tag = "Author"
        # tag_group = "People/Companies"
```
This setup gives **flarchitect** access to your models. The library automatically
locates the active SQLAlchemy session. For non-Flask setups, a custom session
resolver can be supplied via API_SESSION_GETTER <configuration.html#SESSION_GETTER> in the Flask config; see
custom-session-getter for details.
> **Warning**
> The `Meta` inner class is required for automatic route generation and documentation. Models without `Meta` are ignored and will not have CRUD endpoints or entries in the docs until you add it. The `tag` and `tag_group` attributes are optional and only affect documentation grouping.

