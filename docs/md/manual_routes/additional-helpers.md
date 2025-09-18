[← Back to Manual Routes index](index.md)

# Additional helpers
If you only need to protect a manual route with JWT and don’t require schema
wrapping or documentation, you can use `jwt_authentication` directly:
```
from flarchitect.core.architect import jwt_authentication

@app.get("/profile")
@jwt_authentication
def profile():
    return {"status": "ok"}
```
This decorator validates the `Authorization: Bearer <token>` header and sets
the current user context.

