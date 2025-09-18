[← Back to API Documentation index](index.md)

# Security scheme
flarchitect defines a `bearerAuth` security scheme using HTTP bearer tokens
with JWTs. Routes that require authentication reference this scheme via a
`security` declaration instead of documenting an explicit `Authorization`
header parameter.

