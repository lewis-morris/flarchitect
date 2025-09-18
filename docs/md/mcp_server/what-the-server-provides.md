[← Back to MCP Documentation Server index](index.md)

# What the Server Provides
**Resources**
Every Markdown document under `docs/md` (plus `llms.txt`) is exposed as an MCP resource. Resource metadata includes a human-readable title, the file's relative path, and an appropriate `mimeType` (`text/markdown` or `text/plain`). When `docs/md` is missing from the supplied `--project-root`, the CLI automatically falls back to the copy bundled with the installed *flarchitect* package so clients can still browse the canonical docs. The original `docs/source` tree remains the authority; a conversion script keeps the Markdown in sync.

**Tools**
Three MCP tools are registered:
**`list_docs`**
Returns the available document identifiers and titles to help clients discover what can be searched or fetched.

**`search_docs`**
Performs a case-insensitive substring search across the indexed documentation set and returns matching snippets with line numbers and headings. Each item includes `doc_id`, `title`, `url` (`flarchitect-doc://`), `score` (float), `snippet`, and optional `heading`/`line` metadata for precise citations.
Responses follow the MCP tool result schema, wrapping the payload under a `result` key inside `structuredContent` and duplicating the JSON block in a text `application/json` entry so humans and machines can consume the same data.

**`get_doc_section`**
Fetches an entire document or a single heading. Markdown and reStructuredText headings are detected heuristically so callers can request focused sections such as `{"doc_id": "docs/source/getting_started.rst", "heading": "Installation"}`.
The returned payload appears under `structuredContent` with a `result` object containing `doc_id`, `title`, `url`, `content` (plain text), and the requested `heading` (when provided). A JSON text content block mirrors the same data for easy inspection.

**Incremental indexing**
The server loads content on startup using flarchitect.mcp.index.DocumentIndex. Restart the process after documentation changes to refresh the cache.

