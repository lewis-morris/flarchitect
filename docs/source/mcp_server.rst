MCP Documentation Server
========================

The Model Context Protocol (MCP) server bundled with *flarchitect* exposes the project's documentation so tools and agents can query, search, and cite it without bespoke glue code. It indexes the Sphinx ``docs/source`` tree, converts reStructuredText into plain text, and makes the content available over the MCP standard resource and tool APIs.

.. tip::
   The MCP server installs as an optional extra. Install it with ``pip install flarchitect[mcp]`` or ``uv pip install '.[mcp]'`` inside your virtual environment.


Quick Start
-----------

#. Install the optional dependency group (installs ``fastmcp``)::

      pip install flarchitect[mcp]

#. Launch the server from the repository root, preferring ``fastmcp`` but falling back automatically when it is missing::

      flarchitect-mcp-docs --project-root . --backend fastmcp

#. Configure your MCP-aware client to connect to the new ``flarchitect-docs`` endpoint. Resources use the ``flarchitect-doc://`` URI scheme and expose the normalised plain-text representation of the Sphinx sources.

.. note::
   The reference backend (`--backend reference`) requires the upstream ``mcp`` package. Install it manually when you need the pure JSON-RPC server::

      pip install 'mcp @ git+https://github.com/modelcontextprotocol/python-sdk@main'


What the Server Provides
------------------------

Resources
   Every documentation file under ``docs/source`` is exposed as an MCP resource. Resource metadata includes a human-readable title, the file's relative path, and an appropriate ``mimeType`` (``text/markdown`` or ``text/x-rst``). When ``docs/source`` is missing from the supplied ``--project-root``, the CLI automatically falls back to the copy bundled with the installed *flarchitect* package so clients can still browse the canonical docs.

Tools
   Three MCP tools are registered:

   ``list_docs``
      Returns the available document identifiers and titles to help clients discover what can be searched or fetched.

   ``search_docs``
      Performs a case-insensitive substring search across the indexed documentation set and returns matching snippets with line numbers and headings. Each item includes ``doc_id``, ``title``, ``url`` (``flarchitect-doc://``), ``score`` (float), ``snippet``, and optional ``heading``/``line`` metadata for precise citations.
      Responses follow the MCP tool result schema, wrapping the payload under a ``result`` key inside ``structuredContent`` and duplicating the JSON block in a text ``application/json`` entry so humans and machines can consume the same data.

   ``get_doc_section``
      Fetches an entire document or a single heading. Markdown and reStructuredText headings are detected heuristically so callers can request focused sections such as ``{"doc_id": "docs/source/getting_started.rst", "heading": "Installation"}``.
      The returned payload appears under ``structuredContent`` with a ``result`` object containing ``doc_id``, ``title``, ``url``, ``content`` (plain text), and the requested ``heading`` (when provided). A JSON text content block mirrors the same data for easy inspection.

Incremental indexing
   The server loads content on startup using :class:`flarchitect.mcp.index.DocumentIndex`. Restart the process after documentation changes to refresh the cache.


Configuration Reference
-----------------------

The ``flarchitect-mcp-docs`` CLI accepts a handful of flags to make integration simple:

``--project-root``
   Path to the repository root. Defaults to the current working directory. This is used to locate ``docs/source`` and ancillary Markdown files.

``--name``
   Override the server name advertised to clients. The default is ``flarchitect-docs``.

``--description``
   Human-friendly description for clients. Defaults to ``Documentation browser for the flarchitect REST API generator``.

``--backend``
   Select the server runtime. ``fastmcp`` uses the high-level library from Firecrawl, ``reference`` pins to the low-level ``modelcontextprotocol`` implementation, and ``auto`` (default) tries ``fastmcp`` first before falling back.


Integration Tips
----------------

* Sphinx builds are **not** required; the MCP server works with the source files directly so updates are instantly available to clients after restart.
* The ``DocumentIndex`` helper normalises document identifiers (``doc_id``) to match the ``flarchitect-doc://`` URIs. Use the ``list_resources`` capability of your MCP client to discover the available values.
* When writing new documentation, prefer explicit headings so ``get_doc_section`` can slice sections accurately.
* To test the server manually, run ``flarchitect-mcp-docs`` in one terminal and use an MCP client or curl-style helper to issue ``list_resources`` and ``call_tool`` requests.
* Validate tool responses by confirming the ``structuredContent`` block. For example, calling ``search_docs`` with ``"home working summary"`` should return ``{"result": [...]}`` inside ``structuredContent`` (plus a text echo) including ``doc_id`` and ``snippet`` fields.
* The server implements the 2025-06-18 MCP verbs (`resources/list`, `resources/read`, `tools/list`, and `tools/call`) and advertises capabilities during the initial handshake.


Testing Strategy
----------------

Unit tests cover the ``DocumentIndex`` search/section helpers and the backend selection logic (including a stubbed ``fastmcp`` runtime). If you extend the MCP server, add tests under ``tests/`` to keep coverage stable (the repository enforces 90%+ coverage). Use ``pytest tests/test_mcp_index.py tests/test_mcp_server.py`` to exercise the current suite.
