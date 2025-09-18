[← Back to Auth Cookbook index](index.md)

# Multi‑tenant considerations

## Claims & token shape
Include a tenant identifier in JWTs and validate it on requests:
```

# When issuing tokens
payload = {"sub": user.id, "tenant_id": user.tenant_id, "roles": user.roles}


# During request handling (pseudo‑code)
@jwt_authentication
def view():
    tenant_id = current_user.tenant_id  # derived from token/user
    # Apply tenant scope to queries
    items = Item.query.filter_by(tenant_id=tenant_id).all()
```

## Scoping and isolation
- Persist `tenant_id` on tenant‑owned models; enforce it in query helpers or
    via a session/mapper event so all generated endpoints auto‑scope results.
- For config‑driven roles, ensure roles are interpreted within the tenant’s
    context (e.g., `admin` within a tenant, not globally).
- Consider per‑tenant issuers (`iss`) or audiences (`aud`) to improve
    validation and separate concerns across tenants.

## Operational practices
- Key management: rotate signing keys without cross‑tenant leakage; prefer
    centralised JWKS with short cache TTLs if using multiple issuers.
- Testing: add property tests that randomly mix tenants to catch cross‑tenant
    access regressions.
- Logging: include `tenant_id` in structured logs for traceability.

