Custom Serialisation
====================

flarchitect controls how relationships are represented in responses through a
configurable serialisation mode. You can set a global default and override it
per request.

Serialisation modes
-------------------

Set the default with ``API_SERIALIZATION_TYPE`` (globally or per‑model):

- ``url`` (default): relationships render as URLs (stable, compact).
- ``json``: relationships always render as nested objects.
- ``dynamic``: only relationships listed in ``join`` render as nested objects;
  all others remain URLs.
- ``hybrid``: to‑one relationships render as nested objects; collections render
  as URLs.

Per‑request override
--------------------

Clients can override the mode with a ``dump`` query parameter. Invalid values
are ignored and the configured default is used.

Examples::

    # dynamic serialisation for this request only
    GET /api/invoices?dump=dynamic&join=invoice-lines,payments,customer

    # always nest all relations
    GET /api/books?dump=json


Depth and relation inclusion
----------------------------

Two additional knobs affect what appears in the output:

- ``API_ADD_RELATIONS`` (default ``True``) controls whether relationships are
  included at all.
- ``API_SERIALIZATION_DEPTH`` (default ``0``) controls nested eager‑loading
  depth for safe serialisation without extra lazy loads. Set to ``1`` or more
  to eagerly load first/nested relations.

Tip: For dashboards or detail views, ``dump=dynamic`` with ``join`` targets
keeps payloads small while still embedding the specific related objects you
need.

