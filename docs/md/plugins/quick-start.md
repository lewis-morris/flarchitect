[← Back to Plugins index](index.md)

# Quick start
1. Implement a plugin by subclassing `flarchitect.plugins.PluginBase`:
    ```
    from flarchitect.plugins import PluginBase

    class AuditPlugin(PluginBase):
        def before_model_op(self, context):
            # e.g. attach actor/tenant to the payload
            data = context.get("deserialized_data") or {}
            if isinstance(data, dict):
                data = {**data, "actor": context.get("request_id")}
                return {"deserialized_data": data}

        def after_model_op(self, context, output):
            # e.g. emit an audit log
            print("AUDIT:", context.get("method"), context.get("model"), output)
    ```
2. Register your plugin via Flask config:
    ```
    app.config["API_PLUGINS"] = [AuditPlugin()]
    ```

