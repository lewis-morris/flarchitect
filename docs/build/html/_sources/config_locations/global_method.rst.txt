Config by Method Globals
==============================

    Global < **Global Method** < Model < Model Method

:bdg-dark-line:`Global Method`

These values are defined in the `Flask` config and are constrained to a specific `HTTP method`_.

-  They should always be uppercase
-  They should always start with ``API_{method}_``

Values defined here apply globally per method unless a more specific value is defined, and they overwrite the global
value when present.

These values are overridden by :bdg-dark-line:`Model` and :bdg-dark-line:`Model Method` configurations.

Overrides :bdg-dark-line:`Global`


Example
--------------

.. code:: python

    class Config:
        # the rate limit for `POST` requests across all endpoints in your API
        API_POST_RATE_LIMIT = "1 per minute"
        # the rate limit for `GET` requests across all endpoints in your API
        API_GET_RATE_LIMIT = "2 per minute"
        # the rate limit for `PUT` requests across all endpoints in your API
        API_PUT_RATE_LIMIT = "3 per minute"
