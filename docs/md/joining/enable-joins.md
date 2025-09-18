[← Back to Joining Related Resources index](index.md)

# Enable joins
Joins are disabled by default. Enable them globally or per‑model:
```
app.config["API_ALLOW_JOIN"] = True

class Book(db.Model):
    class Meta:
        allow_join = True
```

