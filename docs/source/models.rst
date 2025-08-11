SQLAlchemy Models
=========================================

``flarchitect`` builds APIs directly from your SQLAlchemy models. To expose a model:

* Inherit from your configured base model.
* Add a ``Meta`` inner class with at least ``tag`` and ``tag_group`` attributes for documentation grouping.
* Define your fields and relationships as you normally would; nested relationships are handled automatically.

Example::

    class Author(BaseModel):
        __tablename__ = "author"

        class Meta:
            tag = "Author"
            tag_group = "People/Companies"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

That's all that's required to make the model available through the generated API.
For extended model examples, explore the demo - `model_extension <https://github.com/arched-dev/flarchitect/tree/master/demo/model_extension>`_.
Unit tests demonstrating model behaviour live in `tests/test_models.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_models.py>`_.
