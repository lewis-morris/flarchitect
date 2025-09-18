[← Back to Advanced Configuration index](index.md)

# Case conventions
`flarchitect` can reshape field and schema names to match different
case conventions. These options keep the API's payloads, schemas and
endpoints consistent with the style used by your clients.

## API_FIELD_CASE <configuration.html#FIELD_CASE>
Controls the casing for fields in JSON responses. By default, field names
use `snake` case. Setting API_FIELD_CASE <configuration.html#FIELD_CASE> changes the output to match
other naming styles:
```
class Config:
    API_FIELD_CASE = "camel"
```
```
{
    "statusCode": 200,
    "value": {
        "publicationDate": "2024-05-10"
    }
}
```
Switching to `kebab` case instead renders the same field as
`publication-date`. Supported options include `snake`, `camel`,
`pascal`, `kebab` and `screaming_snake`.

## API_SCHEMA_CASE <configuration.html#SCHEMA_CASE>
Defines the naming convention for generated schema names in the OpenAPI
document. The default, `camel`, produces schema identifiers such as
`apiCalls`. Other styles are also available:
```
class Config:
    API_SCHEMA_CASE = "screaming_snake"
```

## Interplay with API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>
API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE> controls the casing of the generated URL paths. To
maintain a consistent style across paths, schemas and payloads, combine
API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE> with the appropriate API_FIELD_CASE <configuration.html#FIELD_CASE> and
API_SCHEMA_CASE <configuration.html#SCHEMA_CASE> values. For example, selecting `kebab` endpoint
casing pairs naturally with `kebab` field names.

