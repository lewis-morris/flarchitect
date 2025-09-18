[← Back to MCP Documentation Server index](index.md)

# Quick Start
1. Install the optional dependency group (installs `fastmcp`):
    ```
    pip install flarchitect[mcp]
    ```
2. Launch the server from the repository root, preferring `fastmcp` but falling back automatically when it is missing:
    ```
    flarchitect-mcp-docs --project-root . --backend fastmcp
    ```
3. Configure your MCP-aware client to connect to the new `flarchitect-docs` endpoint. Resources use the `flarchitect-doc://` URI scheme and expose the semantic-chunked Markdown generated in `docs/md` (the server falls back to the packaged copy when the directory is missing).
> **Note**
> The reference backend (--backend reference) requires the upstream `mcp` package. Install it manually when you need the pure JSON-RPC server:
> ```
> pip install 'mcp @ git+https://github.com/modelcontextprotocol/python-sdk@main'
> ```

