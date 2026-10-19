[← Back to Extend the generated API index](index.md)

# Actions: add business logic
```
@architect.action(Order, "approve", methods=["POST"])
def approve_order(order, context):
    order.approved = True
    return order
```
This adds `POST /api/orders/<id>/approve` using the model's actual path and
primary-key converter. It also follows `API_PREFIX` and alternate
`Meta.endpoint` paths. Existing CRUD and relationship routes remain available.
POST is the default; GET, PATCH, PUT and DELETE are also supported. Actions are
record-level; use `route` for a collection-wide or unrelated operation.
The framework loads the record within the configured policy scope, checks read
access and, for writes, update access (delete access for DELETE). These policy
calls receive the action name, such as `approve`. Authentication, role and
rate-limit settings are inherited from the model. A blocked method or read-only
model cannot gain a write endpoint through an action.
Use `permission` for an additional business permission; it must return a
truthy value to allow the action. It cannot bypass the model's policy checks.
```
from marshmallow import Schema, fields

class ApprovalInput(Schema):
    reason = fields.String(required=True)

@architect.action(
    Order,
    "approve",
    input_schema=ApprovalInput,
    roles=["manager"],
    permission=lambda order, context: order.status == "pending",
)
def approve_order(order, context):
    order.approval_reason = context.data["reason"]
    order.status = "approved"
    return order
```
Action input is not inferred from the model: declare `input_schema` when the
action accepts a body, then read validated values from `context.data`. Output
defaults to the model's generated schema. Override `output_schema` for a
different response, or use `output_schema=None` for a plain dictionary.
`summary`, `group_tag`, `roles`, `roles_any_of` and `auth` are passed to
the existing schema wrapper. `auth=False` is an explicit authentication opt-out;
it does not disable access policies.
