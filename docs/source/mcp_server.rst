MCP Documentation Server
========================

The Model Context Protocol (MCP) server bundled with *flarchitect* exposes the project's documentation so tools and agents can query, search, and cite it without bespoke glue code. It wraps the raw documentation sources (Sphinx ``docs/source`` tree plus the project ``README``, ``CHANGELOG`` and ``SUGGESTIONS`` backlogs) and makes them available over the MCP standard resource and tool APIs.

.. tip::
   The MCP server installs as an optional extra. Install it with ``pip install flarchitect[mcp]`` or ``uv pip install '.[mcp]'`` inside your virtual environment.


Quick Start
-----------

#. Install the optional dependency group (installs ``modelcontextprotocol`` and ``fastmcp``)::

      pip install flarchitect[mcp]

#. Launch the server from the repository root, preferring ``fastmcp`` but falling back automatically when it is missing::

      flarchitect-mcp-docs --project-root . --backend fastmcp

#. Configure your MCP-aware client to connect to the new ``flarchitect-docs`` endpoint. Resources use the ``flarchitect-doc://`` URI scheme and expose Markdown and reStructuredText sources directly.


What the Server Provides
------------------------

Resources
   Every documentation file under ``docs/source`` plus ``README.md``, ``CHANGELOG.md`` and ``SUGGESTIONS.md`` is exposed as an MCP resource. Resource metadata includes a human-readable title, the file's relative path, and an appropriate ``mimeType`` (``text/markdown`` or ``text/x-rst``).

Tools
   Two MCP tools are registered:

   ``search_docs``
      Performs a case-insensitive substring search across the indexed documentation set and returns matching snippets with line numbers and headings.

   ``get_doc_section``
      Fetches an entire document or a single heading. Markdown and reStructuredText headings are detected heuristically so callers can request focused sections such as ``{"doc_id": "docs/source/getting_started.rst", "heading": "Installation"}``.

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


Testing Strategy
----------------

Unit tests cover the ``DocumentIndex`` search/section helpers and the backend selection logic (including a stubbed ``fastmcp`` runtime). If you extend the MCP server, add tests under ``tests/`` to keep coverage stable (the repository enforces 90%+ coverage). Use ``pytest tests/test_mcp_index.py tests/test_mcp_server.py`` to exercise the current suite.
