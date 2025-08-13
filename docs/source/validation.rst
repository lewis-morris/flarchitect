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
      "errors": {"email": ["Email address is not valid."]},
      "status_code": 400,
      "value": null
    }

Field validation
----------------

``flarchitect`` inspects the ``info`` mapping and the optional ``format``
attribute on SQLAlchemy columns to determine which validators to apply.  When
``API_AUTO_VALIDATE`` is enabled, common formats such as ``email`` or ``date``
are added automatically based on column names.  Any validator supported by
``validate_by_type`` can also be assigned manually:

.. code-block:: python

    class Payment(db.Model):
        account = db.Column(db.String, info={"validate": "iban"})
        cron = db.Column(db.String, info={"format": "cron"})

This associates the ``iban`` and ``cron`` validators with the ``account`` and
``cron`` columns respectively.  Invalid values cause Marshmallow to raise a
``ValidationError`` and the API will respond with ``400``.

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
* ``sha224``
* ``sha256``
* ``sha384``
* ``sha512``
* ``hostname``
* ``iban``
* ``cron``
* ``base64``
* ``currency``
* ``date``
* ``datetime``
* ``time``
* ``boolean``
* ``decimal``

.. _Marshmallow: https://marshmallow.readthedocs.io/
