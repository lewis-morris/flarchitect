Troubleshooting
===============

Joins don’t work
----------------

- Ensure ``API_ALLOW_JOIN=True`` (globally or per model).
- Use correct tokens: you can pass endpoint names (plural), relationship keys
  (singular), kebab‑ or snake‑case; tokens are normalised and singular/plural
  variants are resolved.

Nested objects don’t appear
---------------------------

- Use ``dump=dynamic`` and list relationships in ``join`` to inline those only.
- Or set ``dump=json`` to inline all relationships.
- ``API_ADD_RELATIONS`` must be enabled and, for deep graphs, consider
  ``API_SERIALIZATION_DEPTH`` for eager loading.

Pagination counts look wrong with joins
--------------------------------------

- flarchitect applies ``DISTINCT`` on base rows for typical join queries so
  ``limit``/``total_count`` operate over base entities instead of multiplied
  join rows. If you use custom ``fields``/``groupby``/aggregations, ensure your
  projection reflects the desired counting semantics.

Performance tips
----------------

- Prefer ``join`` with ``dump=dynamic`` to inline only the relations you need.
- Enable caching for hot GET endpoints and pick a shared backend in prod.
- Use rate limiting for public search routes.

