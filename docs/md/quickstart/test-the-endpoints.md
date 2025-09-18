[← Back to Quick Start index](index.md)

# Test the endpoints
Use `curl` to call an endpoint and view the response.
```
curl http://localhost:5000/api/authors
```
Example response:
```
{
  "datetime": "2024-01-01T00:00:00.0000+00:00",
  "api_version": "0.1.0",
  "status_code": 200,
  "response_ms": 15,
  "total_count": 1,
  "next_url": null,
  "previous_url": null,
  "errors": null,
  "value": [
    {"id": 1, "name": "Test Author"}
  ]
}
```
This structured payload is produced by create_response and shows the
standard metadata flarchitect includes by default. To return a bare list,
disable the metadata fields via the `API_DUMP_*` configuration options, for example:
- API_DUMP_DATETIME <configuration.html#DUMP_DATETIME>
- API_DUMP_VERSION <configuration.html#DUMP_VERSION>
- API_DUMP_STATUS_CODE <configuration.html#DUMP_STATUS_CODE>
- API_DUMP_RESPONSE_MS <configuration.html#DUMP_RESPONSE_MS>
- API_DUMP_TOTAL_COUNT <configuration.html#DUMP_TOTAL_COUNT>

