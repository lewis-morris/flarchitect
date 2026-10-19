[← Back to Extend the generated API index](index.md)

# Register before initialisation
Create `Architect()` without an app, register your extensions, then call
`init_app` inside your application context, after configuring your models.
This lets flarchitect resolve generated paths, detect conflicts and include
all the routes in OpenAPI from the start. Registration after `init_app` raises
a clear error. Create a separate Architect instance for each application.
```
architect = Architect()

@architect.hook(Order, "before_create")
def set_owner(order, context):
    order.owner_id = context.user.id
    return order

with app.app_context():
    architect.init_app(app)
```
No extensions are required for ordinary CRUD. Existing `Architect(app)` setup
continues to work when you do not need these registrations.
