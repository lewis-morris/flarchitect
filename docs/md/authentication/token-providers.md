[← Back to Authentication index](index.md)

# Token providers
Configure `API_AUTH_TOKEN_PROVIDERS` to control how JWTs are discovered. The default list is
`["header"]` (`Authorization: Bearer …`). Add `"cookie"` (honouring `API_AUTH_COOKIE_NAME` –
`"access_token"` by default) or provide custom callables/dotted imports to try multiple credential
sources in order for both auto-generated endpoints and the jwt_authentication decorator.

