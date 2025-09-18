[← Back to Configuration index](index.md)

# Core Settings
Essential configuration values needed to run `flarchitect` and control automatic route generation.
| > `API_TITLE`
> :bdg:`default:` `None`
> :bdg:`type` `str`
> :bdg-danger:`Required` :bdg-dark-line:`Global` - Sets the display title of the generated documentation. Provide a concise project name or API identifier. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| --- |
| > `API_VERSION`
> :bdg:`default:` `None`
> :bdg:`type` `str`
> :bdg-danger:`Required` :bdg-dark-line:`Global` - Defines the version string shown in the docs header, helping consumers track API revisions. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| > `FULL_AUTO`
> :bdg:`default:` `True`
> :bdg:`type` `bool`
> :bdg-secondary:`Optional` :bdg-dark-line:`Global` - When `True` `flarchitect` registers CRUD routes for all models at
    startup. Set to `False` to define routes manually. Example: ```
class Config:
    FULL_AUTO = False
``` |
| > `AUTO_NAME_ENDPOINTS`
> :bdg:`default:` `True`
> :bdg:`type` `bool`
> :bdg-secondary:`Optional` :bdg-dark-line:`Global` - Automatically generates OpenAPI summaries from the schema and HTTP
    method when no summary is supplied. Disable to preserve custom
    summaries.
    Example:
    ```
    class Config:
        AUTO_NAME_ENDPOINTS = False
    ``` |

