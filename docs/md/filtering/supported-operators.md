[← Back to Filtering index](index.md)

# Supported operators
The following operators are available. Values are automatically converted to
the correct type where possible (e.g. integers, floats, dates). `like`/`ilike`
wrap the value with `%` for substring matching.
| Operator | Description / Example |
| --- | --- |
| `eq` | Equals. `author_id__eq=1` |
| `ne` / `neq` | Not equal. `rating__ne=5` |
| `lt` | Less than. `price__lt=20` |
| `le` | Less than or equal. `published_year__le=2010` |
| `gt` | Greater than. `pages__gt=300` |
| `ge` | Greater than or equal. `stock__ge=1` |
| `in` | In list. `id__in=(1,2,3)` |
| `nin` | Not in list. `status__nin=(archived,draft)` |
| `like` | Case‑sensitive substring. `title__like=Python` |
| `ilike` | Case‑insensitive substring. `name__ilike=acme` |

