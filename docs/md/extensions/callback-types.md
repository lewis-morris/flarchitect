[← Back to Extensions index](index.md)

# Callback types
flarchitect recognises a number of callback hooks that allow you to run custom
logic at various stages of processing:
- **Global setup** – runs before any model-specific processing. `GLOBAL_SETUP_CALLBACK` (global: API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>)
- **Setup** – runs before database operations. Useful for validation, logging
    or altering incoming data. `SETUP_CALLBACK` (global: API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>)
- **Filter** – lets you adjust the SQLAlchemy query object before filtering and
    pagination are applied. `FILTER_CALLBACK` (global: API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>)
- **Add** – called before a new object is committed to the database. `ADD_CALLBACK` (global: API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>)
- **Update** – invoked prior to persisting updates to an existing object. `UPDATE_CALLBACK` (global: API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>)
- **Remove** – executed before an object is deleted. `REMOVE_CALLBACK` (global: API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>)
- **Return** – runs after the database operation but before the response is
    returned. Ideal for adjusting the output or adding headers. `RETURN_CALLBACK` (global: API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>)
- **Dump** – executes after Marshmallow serialisation allowing you to modify
    the dumped data. `DUMP_CALLBACK` (global: API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>)
- **Final** – runs immediately before the response is sent to the client. `FINAL_CALLBACK` (global: API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>)
- **Error** – triggered when an exception bubbles up; handle logging or
    notifications here. `ERROR_CALLBACK` (global: API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>)

