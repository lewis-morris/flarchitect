[← Back to Filtering index](index.md)

# Enable or disable filtering
Filtering is enabled by default. Disable it globally or per model when you want
fixed endpoints without ad‑hoc query predicates.
```

# Global toggle (default True)
app.config["API_ALLOW_FILTERS"] = True  # or False


# Per‑model override
class Book(db.Model):
    class Meta:
        allow_filters = True  # or False
```

