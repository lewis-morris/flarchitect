[← Back to Authentication index](index.md)

# Error responses
Authentication failures are serialised with create_response, so each
payload includes standard metadata like the API version, timestamp and response
time.
Missing or invalid credentials return a `401`:
```
{
  "api_version": "0.1.0",
  "datetime": "2024-01-01T00:00:00+00:00",
  "status_code": 401,
  "errors": {"error": "Unauthorized", "reason": "Authorization header missing"},
  "response_ms": 5.0,
  "total_count": 1,
  "next_url": null,
  "previous_url": null,
  "value": null
}
```
Expired tokens also yield a `401`:
```
{
  "api_version": "0.1.0",
  "datetime": "2024-01-01T00:00:00+00:00",
  "status_code": 401,
  "errors": {"error": "Unauthorized", "reason": "Token has expired"},
  "response_ms": 5.0,
  "total_count": 1,
  "next_url": null,
  "previous_url": null,
  "value": null
}
```
Refresh failures fall into two categories:
- Invalid refresh JWT (bad format, wrong signature, wrong `iss`/`aud`) → `401` with reason `Invalid token`.
- Unknown, revoked or expired-in-store refresh token → `403` with reason `Invalid or expired refresh token`.
Example `403` response:
```
{
  "api_version": "0.1.0",
  "datetime": "2024-01-01T00:00:00+00:00",
  "status_code": 403,
  "errors": {"error": "Forbidden", "reason": "Invalid or expired refresh token"},
  "response_ms": 5.0,
  "total_count": 1,
  "next_url": null,
  "previous_url": null,
  "value": null
}
```

