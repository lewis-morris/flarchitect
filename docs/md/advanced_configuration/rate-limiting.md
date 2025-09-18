[← Back to Advanced Configuration index](index.md)

# Rate limiting
Rate limits can be applied globally, per HTTP method or per model. For
example, to shield a public search endpoint from abuse, you might allow only
`100` GET requests per minute.
**Global limit**
```
class Config:
    API_RATE_LIMIT = "200 per day"
```
**Model specific**
```
class Book(db.Model):
    __tablename__ = "book"

    class Meta:
        rate_limit = "5 per minute"      # becomes API_RATE_LIMIT
```
Because limits depend on counting requests, those counts must live
somewhere.

