[← Back to MCP Documentation Server index](index.md)

# Configuration Reference
The `flarchitect-mcp-docs` CLI accepts a handful of flags to make integration simple:
**`--project-root`**
Path to the repository root. Defaults to the current working directory. This is used to locate `docs/source` and ancillary Markdown files.

**`--name`**
Override the server name advertised to clients. The default is `flarchitect-docs`.

**`--description`**
Human-friendly description for clients. Defaults to `Documentation browser for the flarchitect REST API generator`.

**`--backend`**
Select the server runtime. `fastmcp` uses the high-level library from Firecrawl, `reference` pins to the low-level `modelcontextprotocol` implementation, and `auto` (default) tries `fastmcp` first before falling back.

