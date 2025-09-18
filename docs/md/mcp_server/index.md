# MCP Documentation Server

The Model Context Protocol (MCP) server bundled with *flarchitect* exposes the project's documentation so tools and agents can query, search, and cite it without bespoke glue code. It indexes the Sphinx `docs/source` tree, converts reStructuredText into plain text, and makes the content available over the MCP standard resource and tool APIs.
> **Tip**
> The MCP server installs as an optional extra. Install it with `pip install flarchitect[mcp]` or `uv pip install '.[mcp]'` inside your virtual environment.

## Sections

- [Quick Start](quick-start.md)
- [What the Server Provides](what-the-server-provides.md)
- [Configuration Reference](configuration-reference.md)
- [Integration Tips](integration-tips.md)
- [Testing Strategy](testing-strategy.md)
