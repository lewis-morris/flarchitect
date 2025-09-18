# flarchitect

![Coverage Report](/_static/coverage.svg)
![Tests](https://github.com/lewis-morris/flarchitect/actions/workflows/run-unit-tests.yml/badge.svg?branch=master&event=push)
![PyPI Version](https://img.shields.io/pypi/v/flarchitect.svg)
![GitHub License](https://img.shields.io/github/license/lewis-morris/flarchitect)
![GitHub Repo](https://badgen.net/static/Repo/Github/blue?icon=github&link=https%3A%2F%2Fgithub.com%2Flewis-morris%2Fflarchitect)

---

**Build APIs fast, customise at will.**
**flarchitect** turns your SQLAlchemy models into a polished RESTful API complete with interactive Redoc or Swagger UI documentation.
Hook it into your Flask application and you'll have endpoints, schemas and docs in moments. It reduces boilerplate while letting you tailor behaviour to your needs.
What can it do?
- Automatically create CRUD endpoints for your SQLAlchemy models.
- Generate Redoc or Swagger UI documentation on the fly - no manual OpenAPI spec needed.
- Be configured globally in Flask or per model or method via `Meta` attributes in your models.
- Authenticate users with minimal effort - use JWTs, API keys or Basic Authentication.
- Restrict endpoints to specific roles with roles-required.
- Extend behaviour with response callbacks, custom validators and per-route hooks (advanced-extensions).
- And much more!

## Sections

- [Advanced Configuration](advanced-configuration.md)
