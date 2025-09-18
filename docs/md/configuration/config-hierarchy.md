[← Back to Configuration index](index.md)

# Config Hierarchy
To offer flexibility and control, **flarchitect** follows a hierarchy of configuration priorities:
- **Lowest Priority – Global Flask config options** are added to `app.config` with an `API_` prefix
    (for example `API_TITLE`). These defaults apply to every request unless overridden by a more specific
    configuration.  See Global<config_locations/global_> for details.
- **Model-based – SQLAlchemy model ``Meta`` attributes** are written in lowercase without the `API_` prefix
    (for example `rate_limit`) and override any global settings for that model.  See Model<config_locations/model>.
- **Highest Priority – Model method-specific ``Meta`` attributes** prefix the lowercase option name with an HTTP
    method (such as `get_description` or `post_authenticate`) to target a single model-method combination.
    These settings override all others.  See Model Method<config_locations/model_method>.
> **Note**
> Each configuration value below is assigned a tag, which defines where the value can be used and its priority:
> Pri 1. Model Method - View here<config_locations/model_method>
> Pri 2. Model - View here<config_locations/model>
> Pri 3. Global - View here<config_locations/global_>

