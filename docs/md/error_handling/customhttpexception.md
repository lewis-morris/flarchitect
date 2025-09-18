[← Back to Error Handling index](index.md)

# CustomHTTPException
`CustomHTTPException` is a lightweight wrapper around an HTTP status code and
optional reason. Raise it in your views when you need to abort a request with a
specific status:
```
from flarchitect.exceptions import CustomHTTPException

@app.get("/widgets/<int:id>")
def get_widget(id: int):
    widget = Widget.query.get(id)
    if widget is None:
        raise CustomHTTPException(404, "Widget not found")
    return widget
```
The exception exposes a `to_dict` method which yields a structured payload
containing the `status_code`, `status_text` and `reason` fields.

