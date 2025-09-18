[← Back to Advanced Configuration index](index.md)

# Extensions, validators and hooks
`flarchitect` offers several extension points for tailoring behaviour beyond
configuration files. These hooks let you alter request handling, apply
additional field validation and tweak responses on a per-route basis.

## Response callbacks
Return callbacks run after database operations but before the response is
serialised. Use them to adjust the output or append metadata.
```
from datetime import datetime

def add_timestamp(model, output, **kwargs):
    output["generated"] = datetime.utcnow().isoformat()
    return {"output": output}

class Config:
    API_RETURN_CALLBACK = add_timestamp
```
See flarchitect.core.routes.create_route_function for details on how
responses are constructed.

## Custom validators
Attach validators to SQLAlchemy columns via the `info` mapping.
Validators are looked up in flarchitect.schemas.validators and
applied automatically.
```
class User(db.Model):
    email = db.Column(
        db.String,
        info={"validator": "email", "validator_message": "Invalid email"},
    )
```
See validation for the full list of available validators.

## Per-route hooks
Execute custom logic before or after a specific route by defining setup or
return callbacks in configuration or on a model's `Meta` class.
```
from flask import abort
from flask_login import current_user

def ensure_admin(model, **kwargs):
    if not current_user.is_admin:
        abort(403)
    return kwargs

class Book(db.Model):
    class Meta:
        return_callback = add_timestamp

class Config:
    API_SETUP_CALLBACK = ensure_admin
```
For more examples see the extensions page.

