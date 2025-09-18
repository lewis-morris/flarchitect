[← Back to Configuration index](index.md)

# Core Settings
Essential configuration values needed to run `flarchitect` and control automatic route generation.
| Setting | Details |
| --- | --- |
| `API_TITLE`<br>default: `None`<br>type `str`<br>Required Global | Sets the display title of the generated documentation. Provide a concise project name or API identifier. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_VERSION`<br>default: `None`<br>type `str`<br>Required Global | Defines the version string shown in the docs header, helping consumers track API revisions. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `FULL_AUTO`<br>default: `True`<br>type `bool`<br>Optional Global<br>Example:<br>```<br>class Config:<br>FULL_AUTO = False<br>``` | When `True` `flarchitect` registers CRUD routes for all models at startup. Set to `False` to define routes manually. |
| `AUTO_NAME_ENDPOINTS`<br>default: `True`<br>type `bool`<br>Optional Global | Automatically generates OpenAPI summaries from the schema and HTTP method when no summary is supplied. Disable to preserve custom summaries. Example: ``` class Config: AUTO_NAME_ENDPOINTS = False ``` |

