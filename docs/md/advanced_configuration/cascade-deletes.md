[← Back to Advanced Configuration index](index.md)

# Cascade deletes
When removing a record, related rows may block the operation. These
settings let `flarchitect` clean up relationships automatically when
explicitly requested.
API_ALLOW_CASCADE_DELETE <configuration.html#ALLOW_CASCADE_DELETE> permits clients to trigger cascading
removal by adding `?cascade_delete=1` to the request. Without this
flag or query parameter, deletes that would orphan related records raise
`409 Conflict` instead of proceeding:
```
DELETE /api/books/1?cascade_delete=1
```
```
class Config:
    API_ALLOW_CASCADE_DELETE = True
```
API_ALLOW_DELETE_RELATED <configuration.html#ALLOW_DELETE_RELATED> governs whether child objects referencing
the target can be removed automatically. Disable it to require manual
cleanup of related rows:
```
class Book(db.Model):
    class Meta:
        delete_related = False  # API_ALLOW_DELETE_RELATED
```
API_ALLOW_DELETE_DEPENDENTS <configuration.html#ALLOW_DELETE_DEPENDENTS> covers dependent objects such as
association table entries. Turning it off forces clients to delete those
records explicitly:
```
class Book(db.Model):
    class Meta:
        delete_dependents = False  # API_ALLOW_DELETE_DEPENDENTS
```
See configuration <configuration> for default values and additional
context on these options.

