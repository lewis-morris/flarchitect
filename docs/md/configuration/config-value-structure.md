[← Back to Configuration index](index.md)

# Config Value Structure
Every configuration value has a specific structure that defines where it can be used and how it should be written.
These structures are indicated by the badges in the configuration tables next to each value.
Please note the badge for each configuration value, as it defines where the value can be used and how it should be written.
Global
Global configuration values are the lowest priority and apply to all requests unless overridden by a more specific configuration.
They are applied in the Flask config object and are prefixed with `API_`.
These settings are ideal for defining application-wide defaults such as API metadata, documentation behaviour,
or pagination policies. Any option listed in the configuration table can be supplied here using its
global `API_` form (for example `API_TITLE` or `API_PREFIX`) and may accept strings, integers,
booleans, lists, or dictionaries depending on the option.
Use this level when you need a single setting to apply consistently across all models and methods.
Example:
```
class Config:
    API_TITLE = "My API"           # text shown in documentation header
    API_PREFIX = "/v1"             # apply a versioned base route
    API_CREATE_DOCS = True          # generate Redoc documentation
```
See the Global <config_locations/global_> page for more information.
Model
Model configuration values override any global Flask configuration.
They are applied in the SQLAlchemy model's `Meta` class, omit the `API_` prefix, and are written in lowercase.
Configure this level when a single model requires behaviour different from the rest of the application,
such as marking a model read only, changing its serialisation depth, or blocking specific methods.
Options correspond directly to the global keys but in lowercase without the prefix (for example `rate_limit`
or `pagination_size_default`) and accept the same data types noted in the configuration table.
Example:
```
class Article(db.Model):
    __tablename__ = "article"

    class Meta:
        rate_limit = "10 per second"         # API_RATE_LIMIT in Flask config
        pagination_size_default = 10           # API_PAGINATION_SIZE_DEFAULT
        blocked_methods = ["DELETE", "POST"]  # API_BLOCK_METHODS
```
See the Model<config_locations/model> page for more information.
Model Method
Model method configuration values have the highest priority and override all other configuration.
They are applied in the SQLAlchemy model's `Meta` class, omit the `API_` prefix, are lowercase, and are prefixed with the method.
Use these settings to fine-tune behaviour for a specific model-method combination. This is useful when
a model should provide different documentation summaries or authentication requirements per HTTP method.
Any model-level option can be adapted by prefixing it with the
HTTP method name (such as `get_description` or `post_authenticate`) and follows the same value types as the
corresponding model option.
Example:
```
class Article(db.Model):
    __tablename__ = "article"

    class Meta:
        get_description = "Detail view of an article"
        post_authenticate = True
```
See the Model Method<config_locations/model_method> page for more information.

