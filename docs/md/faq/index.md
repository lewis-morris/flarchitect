# FAQ

By default URL endpoints are `pluralised kebab-case`, resources are `camelCase` and resource fields are
`snake_case`.
You can change the default behaviour easily by adding the below global Flask configurations:
> API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>
> API_FIELD_CASE <configuration.html#FIELD_CASE>
> API_SCHEMA_CASE <configuration.html#SCHEMA_CASE>
Options are: camel, pascal, snake, kebab, screaming_kebab, screaming_snake
Make your code changes and commit them first. Then run `bumpwright auto --commit --tag` to let BumpWright
determine the next version and record it in a separate commit (and optional tag). Finally, push both the
feature commit and the bump commit, along with any tags, to your remote repository.
- `bumpwright decide` inspects your recent commits or API differences and reports the release type without
    modifying any files.
- `bumpwright bump` increments the version. Add `--dry-run` to preview the change before writing.
- `bumpwright auto` combines deciding and bumping into a single command, ideal for most release workflows.
HTTP methods <[https://developer.mozilla.org/docs/Web/HTTP/Methods](https://developer.mozilla.org/docs/Web/HTTP/Methods)> can be blocked easily, on a global or a model level. See here for full information on how to block
methods.
> API_BLOCK_METHODS <configuration.html#BLOCK_METHODS>
Example blocking all `DELETE` and `POST` methods:
```
app.config['API_BLOCK_METHODS'] = ['DELETE', 'POST']
```
Example blocking `DELETE` and `POST` methods on a specific model:
```
class MyModel(Model):
    class Meta:
        block_methods = ['DELETE', 'POST']
```
Alternatively, if you want to only allow `GET` requests you can turn on the
API_READ_ONLY <configuration.html#READ_ONLY> option in the Flask configuration, which will block all but `GET`
requests from being served.
If you need to perform some custom logic or actions, you can use callbacks. Callbacks are functions
that fire:
- before the database query is performed
- before the data is returned to the API
- on an exception being raised
See the below configuration values that can be defined globally as Flask configurations or on a model level.
> API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>
> API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>
> API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>
If you need to perform soft deletes, you can use the API_SOFT_DELETE <configuration.html#SOFT_DELETE> configuration
as a Flask global configuration. See soft-delete for an example.
Additional configuration values are needed to specify the attribute storing
the delete flag and the values representing the `active` and `deleted`
states. See the below configuration values that can be defined globally as
Flask configurations or on a model level.
> API_SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE>
> API_SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES>
Yes. When API_CREATE_DOCS <configuration.html#CREATE_DOCS> is enabled the schema is automatically
generated at start-up and served at `/openapi.json` (and under the docs UI at
`/docs/apispec.json`). See
openapi for examples on exporting or customising the document.
Restart your application. The specification is rebuilt on boot and will
include any newly registered models or routes.

## Sections

- [Troubleshooting](troubleshooting.md)
