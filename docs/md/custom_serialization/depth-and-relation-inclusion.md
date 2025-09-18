[← Back to Custom Serialisation index](index.md)

# Depth and relation inclusion
Two additional knobs affect what appears in the output:
- `API_ADD_RELATIONS` (default `True`) controls whether relationships are
    included at all.
- `API_SERIALIZATION_DEPTH` (default `0`) controls nested eager‑loading
    depth for safe serialisation without extra lazy loads. Set to `1` or more
    to eagerly load first/nested relations.
Tip: For dashboards or detail views, `dump=dynamic` with `join` targets
keeps payloads small while still embedding the specific related objects you
need.

