[← Back to MCP Documentation Server index](index.md)

# Testing Strategy
Unit tests cover the `DocumentIndex` search/section helpers and the backend selection logic (including a stubbed `fastmcp` runtime). If you extend the MCP server, add tests under `tests/` to keep coverage stable (the repository enforces 90%+ coverage). Use `pytest tests/test_mcp_index.py tests/test_mcp_server.py` to exercise the current suite.

