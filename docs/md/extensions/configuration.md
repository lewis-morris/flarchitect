[← Back to Extensions index](index.md)

# Configuration
Callbacks are referenced by the following configuration keys (global variants
use `API_<KEY>`):
- `GLOBAL_SETUP_CALLBACK` / API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>
- `SETUP_CALLBACK` / API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>
- `FILTER_CALLBACK` / API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>
- `ADD_CALLBACK` / API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>
- `UPDATE_CALLBACK` / API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>
- `REMOVE_CALLBACK` / API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>
- `RETURN_CALLBACK` / API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>
- `DUMP_CALLBACK` / API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>
- `FINAL_CALLBACK` / API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>
- `ERROR_CALLBACK` / API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>
You can apply these keys in several places:
1. **Global Flask config**
    Use `API_<KEY>` to apply a callback to all endpoints.
    ```
    class Config:
        API_SETUP_CALLBACK = my_setup
    ```
2. **Model config**
    Set lowercase attributes on a model's `Meta` class to apply callbacks to
    all endpoints for that model.
    ```
    class Author(db.Model):
        class Meta:
            setup_callback = my_setup
    ```
3. **Model method config**
    Use `<method>_<key>` on the `Meta` class for the highest level of
    specificity.
    ```
    class Author(db.Model):
        class Meta:
            get_return_callback = my_get_return
    ```

