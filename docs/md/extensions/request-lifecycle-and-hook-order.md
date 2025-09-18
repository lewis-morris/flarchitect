[← Back to Extensions index](index.md)

# Request lifecycle and hook order
This is the high‑level order in which flarchitect processes a request and where
each callback/plugin hook sits. Understanding the flow helps you choose the
right extension point and the available context.
1. `request_started` plugin hook
    - Called at the very beginning of the request (`@app.before_request`).
    - Signature: `request_started(request: flask.Request) -> None`.
2. Authentication
    - For routes not wrapped by `schema_constructor`, global auth runs via
    > `Architect._global_authentication`.
    - For `schema_constructor` routes, auth runs inside the wrapper before
        schemas and rate limiting are applied.
    - Plugin hooks around auth:
        - `before_authenticate(context: dict) -> dict | None` – may update context.
        - `after_authenticate(context: dict, success: bool, user: Any | None) -> None`.
    - `context` keys: `model` (type | None), `method` (str), optionally
        `output_schema` / `input_schema`.
3. Route execution (`schema_constructor` routes)
    a. Plugin `before_model_op`
    > - Called with a rich context before any model operation. Return a dict to
    >     merge into context/kwargs.
    1. Global/Model callbacks in order:
        - `API_GLOBAL_SETUP_CALLBACK` (method‑aware) → may mutate kwargs
        - `API_SETUP_CALLBACK` (method‑aware) → may mutate kwargs
    2. CRUD service action runs (get/add/update/delete)
        - Internally may call:
        > - `API_FILTER_CALLBACK(query, model, params)` to adjust the query
        > - `API_ADD_CALLBACK(obj, model)` before commit on POST
        > - `API_UPDATE_CALLBACK(obj, model)` before commit on PATCH
        > - `API_REMOVE_CALLBACK(obj, model)` before delete/soft‑delete on DELETE
    3. `API_RETURN_CALLBACK` (method‑aware) → adjust/replace action output
    4. Plugin `after_model_op` (may replace the output)
4. Response wrapping and serialisation
    - Marshmallow dump occurs inside the `schema_constructor` wrapper. After
    > Marshmallow serialises data, `API_DUMP_CALLBACK(data, **kwargs)` runs.
    - The final payload is wrapped by `create_response` to a standard JSON
        envelope. Before the response is serialised, `API_FINAL_CALLBACK` can
        mutate the response dictionary.
    - Errors (raised exceptions or error statuses) trigger `API_ERROR_CALLBACK`.
5. `request_finished` plugin hook
    - Runs in `@app.after_request`. May return a replacement `Response`.
    - Signature: `request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None`.

