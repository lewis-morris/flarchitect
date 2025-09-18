[← Back to Auth Cookbook index](index.md)

# JWT patterns
Minimal configuration:
```
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],
    ACCESS_SECRET_KEY=os.environ["ACCESS_SECRET_KEY"],
    REFRESH_SECRET_KEY=os.environ["REFRESH_SECRET_KEY"],
    API_USER_MODEL=User,
    API_USER_LOOKUP_FIELD="username",
    API_CREDENTIAL_CHECK_METHOD="check_password",
    API_JWT_EXPIRY_TIME=360,             # minutes
    API_JWT_REFRESH_EXPIRY_TIME=2880,    # minutes
    API_JWT_ALLOWED_ALGORITHMS=["HS256"],
)
```
Endpoints:
- `POST /auth/login` → returns `access_token` and `refresh_token`.
- `POST /auth/refresh` → accepts JSON `{"refresh_token": "<token>"}` (a
    leading `"Bearer "` prefix is tolerated and removed), then rotates the
    refresh token and issues a new access token. Invalid refresh JWTs respond
    with `401`; unknown/revoked/expired refresh tokens respond with `403`.
- `POST /auth/logout` → clears user context (stateless logout).

## Key rotation with RS256
Prefer asymmetric keys in production. Keep multiple active keys and use
`kid` headers for selection:
```
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],
    API_JWT_ALGORITHM="RS256",
    # Current signing keys (PEM strings). Store via secrets, not in code.
    ACCESS_PRIVATE_KEY=os.environ["ACCESS_PRIVATE_KEY"],
    REFRESH_PRIVATE_KEY=os.environ["REFRESH_PRIVATE_KEY"],
    # Verification keys (public). Support multiple for rotation.
    ACCESS_PUBLIC_KEY=os.environ["ACCESS_PUBLIC_KEY"],
    REFRESH_PUBLIC_KEY=os.environ["REFRESH_PUBLIC_KEY"],
    API_JWT_ALLOWED_ALGORITHMS=["RS256"],
)
```
When issuing tokens, include a `kid` header and keep a small in‑memory map of
active public keys. Rotate by introducing a new keypair, marking the old public
key as still valid for verification, then retiring it after all issued tokens
expire. See authentication for claim settings (`iss`, `aud`,
`leeway`).

## Production tips
- Store secrets in environment variables or file‑based secrets mounted into the
    container. Never commit secrets to source control.
- Restrict algorithms via `API_JWT_ALLOWED_ALGORITHMS`; set `iss` and
    `aud` claims and validate them for defence in depth.
- Keep refresh tokens single‑use (default) and log rotation events for audit.

