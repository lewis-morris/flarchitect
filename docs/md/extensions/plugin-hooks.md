[← Back to Extensions index](index.md)

# Plugin hooks
Plugins provide a structured way to observe and influence behaviour across the
app. Configure with `API_PLUGINS` as a list of classes/instances/factories
deriving from `flarchitect.plugins.PluginBase`.
Available hooks and signatures:
- `request_started(request: flask.Request) -> None`
- `request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None`
- `before_authenticate(context: dict[str, Any]) -> dict[str, Any] | None`
> - Context keys: `model` (type | None), `method` (str), optional
>     `output_schema` / `input_schema`.
- `after_authenticate(context: dict[str, Any], success: bool, user: Any | None) -> None`
- `before_model_op(context: dict[str, Any]) -> dict[str, Any] | None`
    - Context keys mirror Setup kwargs, plus `method` (str) and `many` (bool).
- `after_model_op(context: dict[str, Any], output: Any) -> Any | None`
- `spec_build_started(spec: Any) -> None`
- `spec_build_completed(spec_dict: dict[str, Any]) -> dict[str, Any] | None`
Example plugin:
```
from flarchitect.plugins import PluginBase

class AuditPlugin(PluginBase):
    def before_model_op(self, context):
        # attach correlation fields
        return {"audit": {"path": context.get("relation_name"), "method": context["method"]}}

    def after_model_op(self, context, output):
        # inject audit trail into result dicts
        if isinstance(output, dict):
            out = dict(output)
            out["audit"] = context.get("audit")
            return out
        return None
```

