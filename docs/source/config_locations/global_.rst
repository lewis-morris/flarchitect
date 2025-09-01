Config Globals
==============================

    **Global** < Model < Model Method

:bdg-dark-line:`Global`

These are the global configuration variables which are defined in `Flask`_.

-  They should always be uppercase
-  They should always start with ``API_``

Values defined here apply globally unless a more specific value is defined.

These values are overridden by :bdg-dark-line:`Model` or :bdg-dark-line:`Model Method` configurations.

Example
--------------

.. code:: python

    class Config:
        # the rate limit across all endpoints in your API
        # If any other, more specific, rate limit is defined, it will
        # override this one for the particular endpoint / method / model.
        API_RATE_LIMIT = "1 per minute"  # see :ref:`RATE_LIMIT <RATE_LIMIT>`
