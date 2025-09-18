[← Back to Advanced Configuration index](index.md)

# Response metadata
`flarchitect` can attach additional metadata to every response. These
keys let you toggle each field individually. Including version numbers, for
example, helps client developers cache against the correct release:
| Key | Default | Effect |
| --- | --- | --- |
| API_DUMP_HYBRID_PROPERTIES <configuration.html#DUMP_HYBRID_PROPERTIES> | `True` | Include SQLAlchemy hybrid properties in serialised output. |
| API_DUMP_DATETIME <configuration.html#DUMP_DATETIME> | `True` | Append the current UTC timestamp as `datetime`. |
| API_DUMP_VERSION <configuration.html#DUMP_VERSION> | `True` | Embed the API version string as `api_version`. |
| API_DUMP_STATUS_CODE <configuration.html#DUMP_STATUS_CODE> | `True` | Add the HTTP status code to the payload. |
| API_DUMP_RESPONSE_MS <configuration.html#DUMP_RESPONSE_MS> | `True` | Include elapsed processing time in milliseconds as `response_ms`. |
| API_DUMP_TOTAL_COUNT <configuration.html#DUMP_TOTAL_COUNT> | `True` | Provide a `total_count` field for collection endpoints. |
| API_DUMP_REQUEST_ID <configuration.html#DUMP_REQUEST_ID> | `False` | Include the per-request correlation identifier as `request_id`. The header `X-Request-ID` is always sent. |
| API_DUMP_NULL_NEXT_URL <configuration.html#DUMP_NULL_NEXT_URL> | `True` | Show `next_url` with `null` when no further page exists. |
| API_DUMP_NULL_PREVIOUS_URL <configuration.html#DUMP_NULL_PREVIOUS_URL> | `True` | Show `previous_url` with `null` when at the first page. |
| API_DUMP_NULL_ERRORS <configuration.html#DUMP_NULL_ERRORS> | `True` | Always include an `errors` field, defaulting to `null`. |

## Example
With metadata enabled (defaults):
```
{
    "data": [...],
    "datetime": "2024-01-01T00:00:00Z",
    "api_version": "0.0.0",
    "status_code": 200,
    "response_ms": 15,
    "total_count": 1,
    "next_url": null,
    "previous_url": null,
    "errors": null
}
```
Disabling all metadata:
```
class Config:
    API_DUMP_DATETIME = False
    API_DUMP_VERSION = False
    API_DUMP_STATUS_CODE = False
    API_DUMP_RESPONSE_MS = False
    API_DUMP_TOTAL_COUNT = False
    API_DUMP_NULL_NEXT_URL = False
    API_DUMP_NULL_PREVIOUS_URL = False
    API_DUMP_NULL_ERRORS = False

{
    "data": [...]
}
```

