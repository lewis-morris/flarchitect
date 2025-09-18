[← Back to Manual Routes index](index.md)

# Route handler signature
Decorated handlers may optionally accept `deserialized_data` to receive the
validated request body when `input_schema` is provided. Extra wrapper kwargs
such as `model` are filtered and only arguments declared in your function
signature are passed, so both of the following are valid:
```
@app.post("/echo")
@architect.schema_constructor(input_schema=ItemIn, output_schema=None)
def echo(deserialized_data=None):
    return deserialized_data


# or
@app.post("/echo2")
@architect.schema_constructor(input_schema=ItemIn, output_schema=None)
def echo2(deserialized_data=None, **kwargs):  # kwargs may include 'model'
    return deserialized_data
```

