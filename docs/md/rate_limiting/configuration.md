[← Back to Rate Limiting index](index.md)

# Configuration
Global limit:
```
class Config:
    API_RATE_LIMIT = "200 per day"
```
Per‑model limit:
```
class Book(db.Model):
    class Meta:
        rate_limit = "5 per minute"  # API_RATE_LIMIT
```

