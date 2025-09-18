[← Back to Manual Routes index](index.md)

# Input and output schemas
You can validate request bodies and serialise responses with Marshmallow
schemas. Use `input_schema` for inbound data and `output_schema` for the
response. For endpoints returning a list, pass `many=True` to control how
serialisation is applied.
If you don't want flarchitect to serialise the response, set
`output_schema=None`. In this mode the wrapper skips field selection and
Marshmallow dumping entirely and your handler's return value (dict or list)
is wrapped unchanged in the standard JSON envelope.
```
class ItemIn(Schema):
    name = fields.String(required=True)

class ItemOut(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)

@app.post("/items")
@architect.schema_constructor(input_schema=ItemIn, output_schema=ItemOut)
def create_item():
    # Access validated input via Flask's request.json in your handler
    ...
    return {"id": 1, "name": "example"}
```

