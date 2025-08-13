Validation
==========

flarchitect ships with a suite of field validators that hook directly into
`Marshmallow`_.  Validators can be attached to a model column via the SQLAlchemy
``info`` mapping or inferred automatically from column names and formats.

Basic usage
-----------

.. code-block:: python

    class Author(db.Model):
        email = db.Column(
            db.String,
            info={"validate": "email"},
        )
        website = db.Column(
            db.String,
            info={"format": "uri"},  # auto adds URL validation
        )

When invalid data is sent to the API a ``400`` response is returned:

.. code-block:: json

    {
      "errors": {"error": {"email": ["Email address is not valid."]}},
      "status_code": 400,
      "value": null
    }

Available validators
--------------------

``validate_by_type`` supports the following names:

* ``email``
* ``url``
* ``ipv4``
* ``ipv6``
* ``mac``
* ``slug``
* ``uuid``
* ``card``
* ``country_code``
* ``domain``
* ``md5``
* ``sha1``
* ``sha256``
* ``sha512``
* ``date``
* ``datetime``
* ``time``
* ``boolean``
* ``decimal``

.. _Marshmallow: https://marshmallow.readthedocs.io/
