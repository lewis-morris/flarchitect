[← Back to MCP Documentation Server index](index.md)

# Integration Tips
- Sphinx builds are **not** required; the MCP server works with the source files directly so updates are instantly available to clients after restart.
- The `DocumentIndex` helper normalises document identifiers (`doc_id`) to match the `flarchitect-doc://` URIs. Use the `list_resources` capability of your MCP client to discover the available values.
- When writing new documentation, prefer explicit headings so `get_doc_section` can slice sections accurately.
- To test the server manually, run `flarchitect-mcp-docs` in one terminal and use an MCP client or curl-style helper to issue `list_resources` and `call_tool` requests.
- Validate tool responses by confirming the `structuredContent` block. For example, calling `search_docs` with `"home working summary"` should return `{"result": [...]}` inside `structuredContent` (plus a text echo) including `doc_id` and `snippet` fields.
- The server implements the 2025-06-18 MCP verbs (resources/list, resources/read, tools/list, and tools/call) and advertises capabilities during the initial handshake.
- The repository ships an `llms.txt` manifest (generated alongside the Markdown) so external tooling that follows the llmstxt.org <[https://llmstxt.org](https://llmstxt.org)> proposal can discover the curated documentation index.
- Regenerate the Markdown chunks and `llms.txt` after updating `docs/source` by running `python tools/convert_docs.py` from the project root. The script is idempotent and will overwrite any manual edits to the generated files.

