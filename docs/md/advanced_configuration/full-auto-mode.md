[← Back to Advanced Configuration index](index.md)

# Full auto mode
`flarchitect` enables automatic route creation by default. With
`FULL_AUTO = True` the ~flarchitect.Architect scans your models at
startup and registers CRUD routes for each one. This is convenient for new
projects but may conflict with custom blueprints or hand-written views.
Disable `FULL_AUTO` when you need to manage routes manually or only expose a
subset of models. After turning it off you must call `init_api` explicitly to
register any automatic routes you still require.
```
app = Flask(__name__)
app.config["FULL_AUTO"] = False
arch = Architect(app)
arch.init_api(app=app)  # manually trigger route generation
```
Use this mode when integrating with existing applications or when automatic
registration would create unwanted endpoints.

