[← Back to Custom Serialisation index](index.md)

# Depth and relation inclusion
Two additional knobs affect what appears in the output:
- `API_ADD_RELATIONS` (default `True`) controls whether relationships are
    included at all.
- `API_SERIALIZATION_DEPTH` (default `0`) limits how many levels render as
    nested JSON. When `0`, relationships remain URLs even if `dump` is
    `json`/`hybrid`, and `dump=dynamic` falls back to URLs unless a join
    explicitly names the relationship. Increase to nest that many levels before
    falling back to URLs.
Tip: For dashboards or detail views, `dump=dynamic` with `join` targets
keeps payloads small while still embedding the specific related objects you
need, even when the global depth is zero.

