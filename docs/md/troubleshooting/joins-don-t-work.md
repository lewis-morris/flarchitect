[← Back to Troubleshooting index](index.md)

# Joins don’t work
- Ensure `API_ALLOW_JOIN=True` (globally or per model).
- Use correct tokens: you can pass endpoint names (plural), relationship keys
    (singular), kebab‑ or snake‑case; tokens are normalised and singular/plural
    variants are resolved.

