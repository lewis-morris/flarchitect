Validation
==========

flarchitect ships with a suite of field validators that hook directly into
`Marshmallow`_.  Validators can be attached to a model column via the SQLAlchemy
``info`` mapping or inferred automatically from column names and formats.

For a runnable example demonstrating email and URL validation see the `validators demo <https://github.com/lewis-morris/flarchitect/tree/master/demo/validators>`_.

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
`API_AUTO_VALIDATE <configuration.html#AUTO_VALIDATE>`_ is enabled, common formats such as ``email`` or ``date``
are added automatically based on column names.  Any validator supported by
``validate_by_type`` can also be assigned manually:

.. code-block:: python

    class Payment(db.Model):
        account = db.Column(db.String, info={"validate": "iban"})
        cron = db.Column(db.String, info={"format": "cron"})

This associates the ``iban`` and ``cron`` validators with the ``account`` and
``cron`` columns respectively.  Invalid values cause Marshmallow to raise a
``ValidationError`` and the API will respond with ``400``.

Multiple validators can be applied to a single column by providing a list:

.. code-block:: python

    class Contact(db.Model):
        identifier = db.Column(
            db.String,
            info={"validate": ["email", "slug"]},
        )

Submitting invalid data returns messages for each failed validator:

.. code-block:: json

    {
      "errors": {"identifier": ["Email address is not valid.", "Value must be a valid slug."]},
      "status_code": 400,
      "value": null
    }

Custom error messages can also be supplied via a mapping:

.. code-block:: python

    class Employee(db.Model):
        email = db.Column(
            db.String,
            info={"validate": {"email": "Invalid email"}},
        )

Invalid values return the custom message:

.. code-block:: json

    {
      "errors": {"email": ["Invalid email"]},
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
* ``sha224``
* ``sha256``
* ``sha384``
* ``sha512``
* ``hostname``
* ``iban``
* ``cron``
* ``base64``
* ``currency``
* ``phone``
* ``postal_code``
* ``date``
* ``datetime``
* ``time``
* ``boolean``
* ``decimal``
