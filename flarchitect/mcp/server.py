"""Model Context Protocol server exposing the flarchitect documentation set."""

from __future__ import annotations

import argparse
import inspect
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

from flarchitect import __version__ as PACKAGE_VERSION

from .index import DocumentIndex, DocumentRecord, SearchHit


@dataclass
class ServerConfig:
    """Runtime configuration for the MCP documentation server."""

    project_root: Path
    name: str = "flarchitect-docs"
    version: str = PACKAGE_VERSION
    description: str = "Documentation browser for the flarchitect REST API generator"


def build_index(project_root: Path) -> DocumentIndex:
    """Construct a :class:`DocumentIndex` with sensible defaults."""

    doc_roots: list[Path] = []
    aliases: dict[Path, str] = {}

    docs_source = project_root / "docs" / "source"
    if docs_source.exists():
        doc_roots.append(docs_source)
        aliases[docs_source] = "docs/source"

    docs_root = project_root / "docs"
    if docs_root.exists() and docs_root != docs_source:
        doc_roots.append(docs_root)
        aliases[docs_root] = "docs"

    project_docs = [
        project_root / "README.md",
        project_root / "CHANGELOG.md",
        project_root / "SUGGESTIONS.md",
        project_root / "AGENTS.md",
    ]
    extra_files = {path: path.name for path in project_docs if path.exists()}

    if not doc_roots:
        raise FileNotFoundError(
            "No documentation roots discovered. Provide --project-root pointing to the repository root or pass custom directories."
        )

    return DocumentIndex(doc_roots, aliases=aliases, extra_files=extra_files)


def create_server(
    config: ServerConfig,
    index: DocumentIndex,
    *,
    backend: str = "auto",
):
    """Instantiate an MCP server using the selected backend."""

    backend = backend.lower()
    if backend not in {"auto", "fastmcp", "reference"}:
        raise ValueError("backend must be one of: auto, fastmcp, reference")

    if backend in {"auto", "fastmcp"}:
        fastmcp_server = _create_fastmcp_server(config, index)
        if fastmcp_server is not None:
            return fastmcp_server
        if backend == "fastmcp":
            raise RuntimeError(
                "fastmcp backend requested but the 'fastmcp' package is unavailable or incompatible. Install flarchitect[mcp]."
            )

    reference_server = _create_reference_server(config, index)
    if reference_server is None:
        raise RuntimeError(
            "Unable to construct the reference MCP server. Ensure 'modelcontextprotocol' is installed via flarchitect[mcp]."
        )
    return reference_server


def _create_fastmcp_server(config: ServerConfig, index: DocumentIndex):
    try:
        fastmcp_module = import_module("fastmcp")
    except ImportError:
        return None

    fastmcp_cls = getattr(fastmcp_module, "FastMCP", None) or getattr(
        fastmcp_module, "FastMCPServer", None
    )
    if fastmcp_cls is None:
        return None

    init_signature = inspect.signature(fastmcp_cls)
    kwargs: dict[str, Any] = {}
    for field in ("name", "version", "description"):
        if field in init_signature.parameters:
            kwargs[field] = getattr(config, field)
    app = fastmcp_cls(**kwargs)

    configured = _configure_fastmcp_modern(app, config, index) or _configure_fastmcp_legacy(
        app, config, index
    )
    if not configured:
        return None

    run_callable = _resolve_attr(app, ("serve", "run", "start"))
    if run_callable is None:
        return None

    return _CallableServer(run_callable)


def _configure_fastmcp_modern(app: Any, config: ServerConfig, index: DocumentIndex) -> bool:
    add_resource = getattr(app, "add_resource", None)
    tool = getattr(app, "tool", None)
    if add_resource is None or tool is None:
        return False

    try:
        from typing import Annotated

        from pydantic import Field

        resources_module = import_module("fastmcp.resources")
        TextResource = getattr(resources_module, "TextResource")

        tools_module = import_module("fastmcp.tools")
        ToolResultCls = getattr(tools_module, "ToolResult", None)
        if ToolResultCls is None:
            tool_submodule = import_module("fastmcp.tools.tool")
            ToolResultCls = getattr(tool_submodule, "ToolResult")
    except Exception:  # pragma: no cover - guard incompatible fastmcp builds
        return False

    try:
        project_root = config.project_root
        for record in index.list_documents():
            try:
                description = str(record.path.relative_to(project_root))
            except ValueError:
                description = record.path.name
            resource = TextResource(
                uri=f"flarchitect-doc://{record.doc_id}",
                name=record.doc_id,
                title=record.title,
                description=description,
                mime_type=_guess_mime(record),
                text=record.content,
            )
            add_resource(resource)
    except Exception:  # pragma: no cover - invalid TextResource wiring
        return False

    @tool(
        name="search_docs",
        description="Search flarchitect documentation for matching text.",
    )
    async def search_docs(
        query: Annotated[str, Field(description="Text to search for")],
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=50,
                description="Maximum number of results to return",
            ),
        ] = 10,
    ) -> Any:
        hits = index.search(query, limit=limit)
        items = [_format_hit(index, hit) for hit in hits]
        return ToolResultCls(structured_content=_wrap_result({"items": items}))

    @tool(
        name="get_doc_section",
        description="Return a full document or a named section by heading.",
    )
    async def get_doc_section(
        doc_id: Annotated[
            str,
            Field(
                description="Document identifier as returned by list_resources",
            ),
        ],
        heading: Annotated[
            str | None,
            Field(
                description="Optional heading to slice out of the document",
            ),
        ] = None,
    ) -> Any:
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        try:
            content = index.get_section(doc_id, heading)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        payload = {
            "doc_id": doc_id,
            "title": record.title,
            "heading": heading,
            "content": content,
            "url": _build_doc_url(doc_id),
        }
        return ToolResultCls(structured_content=_wrap_result(payload))

    return True


def _configure_fastmcp_legacy(app: Any, config: ServerConfig, index: DocumentIndex) -> bool:
    list_hook = _resolve_attr(app, ("list_resources", "on_list_resources"))
    read_hook = _resolve_attr(app, ("read_resource", "on_read_resource"))
    tool_hook = _resolve_attr(app, ("tool", "add_tool"))

    if list_hook is None or read_hook is None or tool_hook is None:
        return False

    # Import MCP standard dataclasses for structured responses.
    try:
        standard = import_module("modelcontextprotocol.standard")
        ListResourcesResult = getattr(standard, "ListResourcesResult")
        ReadResourceResult = getattr(standard, "ReadResourceResult")
        Resource = getattr(standard, "Resource")
        ResourceContents = getattr(standard, "ResourceContents")
        TextResourceContents = getattr(standard, "TextResourceContents")
        Tool = getattr(standard, "Tool")
        ToolResult = getattr(standard, "ToolResult")
    except Exception:  # pragma: no cover - fall back to dict responses
        ListResourcesResult = ReadResourceResult = ToolResult = None
        Resource = ResourceContents = TextResourceContents = Tool = None

    async def _list_resources_impl(*_: Any, **__: Any):
        resources = [
            _build_resource_payload(Resource, record, config.project_root)
            for record in index.list_documents()
        ]
        if ListResourcesResult is not None:
            return ListResourcesResult(resources=resources)
        return {"resources": resources}

    async def _read_resource_impl(request: Any):
        uri = _get_field(request, "uri")
        if uri is None:
            raise ValueError("'uri' is required to read a resource")
        doc_id = str(uri).replace("flarchitect-doc://", "", 1)
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(f"No document with id '{doc_id}'") from exc
        contents_payload = _build_text_contents_payload(
            TextResourceContents,
            uri,
            record.content,
        )
        if ReadResourceResult is not None:
            return ReadResourceResult(contents=[contents_payload])
        return {"contents": [contents_payload]}

    async def _search_docs_impl(request: Any):
        arguments = _get_field(request, "arguments", {}) or {}
        query = arguments.get("query") or ""
        limit = int(arguments.get("limit", 10))
        hits = index.search(query, limit=limit)
        items = [_format_hit(index, hit) for hit in hits]
        result_payload = [{"type": "application/json", "body": _wrap_result({"items": items})}]
        if ToolResult is not None:
            return ToolResult(outputs=result_payload)
        return {"outputs": result_payload}

    async def _get_doc_section_impl(request: Any):
        arguments = _get_field(request, "arguments", {}) or {}
        doc_id = arguments.get("doc_id")
        heading = arguments.get("heading")
        if not doc_id:
            raise ValueError("'doc_id' is required")
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        try:
            content = index.get_section(doc_id, heading)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        payload = {
            "doc_id": doc_id,
            "title": record.title,
            "heading": heading,
            "content": content,
            "url": _build_doc_url(doc_id),
        }
        result_payload = [{"type": "application/json", "body": _wrap_result(payload)}]
        if ToolResult is not None:
            return ToolResult(outputs=result_payload)
        return {"outputs": result_payload}

    _register_callback(list_hook, _list_resources_impl)
    _register_callback(read_hook, _read_resource_impl)

    _register_tool(
        tool_hook,
        _search_docs_impl,
        name="search_docs",
        description="Search flarchitect documentation for matching text.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search for"},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "Maximum number of results to return",
                },
            },
            "required": ["query"],
        },
        Tool=Tool,
    )

    _register_tool(
        tool_hook,
        _get_doc_section_impl,
        name="get_doc_section",
        description="Return a full document or a named section by heading.",
        input_schema={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Document identifier as returned by list_resources",
                },
                "heading": {
                    "type": ["string", "null"],
                    "description": "Optional heading to slice out of the document",
                },
            },
            "required": ["doc_id"],
        },
        Tool=Tool,
    )

    return True


def _create_reference_server(config: ServerConfig, index: DocumentIndex):
    try:
        from modelcontextprotocol.server import Server
        from modelcontextprotocol.standard import (
            ListResourcesResult,
            ReadResourceResult,
            Resource,
            ResourceContents,
            TextResourceContents,
            Tool,
            ToolResult,
        )
        from modelcontextprotocol.types import (
            CallToolRequest,
            ListResourcesRequest,
            ReadResourceRequest,
        )
    except ImportError:
        return None

    server = Server(config.name, config.version, description=config.description)

    @server.list_resources()
    async def _list_resources(_: ListResourcesRequest) -> ListResourcesResult:  # type: ignore[name-defined]
        resources = [
            _build_resource_payload(Resource, record, config.project_root)
            for record in index.list_documents()
        ]
        return ListResourcesResult(resources=resources)

    @server.read_resource()
    async def _read_resource(request: ReadResourceRequest) -> ReadResourceResult:  # type: ignore[name-defined]
        uri = request.uri
        doc_id = str(uri).replace("flarchitect-doc://", "", 1)
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(f"No document with id '{doc_id}'") from exc
        contents = _build_text_contents_payload(
            TextResourceContents,
            uri,
            record.content,
        )
        return ReadResourceResult(contents=[contents])

    @server.tool()
    async def search_docs(request: CallToolRequest) -> ToolResult:  # type: ignore[name-defined]
        params = request.arguments or {}
        query = params.get("query") or ""
        limit = int(params.get("limit", 10))
        hits = index.search(query, limit=limit)
        items = [_format_hit(index, hit) for hit in hits]
        return ToolResult(outputs=[{"type": "application/json", "body": _wrap_result({"items": items})}])

    _attach_tool_metadata(
        search_docs,
        Tool,
        name="search_docs",
        description="Search flarchitect documentation for matching text.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search for"},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "Maximum number of results to return",
                },
            },
            "required": ["query"],
        },
    )

    @server.tool()
    async def get_doc_section(request: CallToolRequest) -> ToolResult:  # type: ignore[name-defined]
        params = request.arguments or {}
        doc_id = params.get("doc_id")
        heading = params.get("heading")
        if not doc_id:
            raise ValueError("'doc_id' is required")
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        try:
            content = index.get_section(doc_id, heading)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        payload = {
            "doc_id": doc_id,
            "title": record.title,
            "heading": heading,
            "content": content,
            "url": _build_doc_url(doc_id),
        }
        return ToolResult(outputs=[{"type": "application/json", "body": _wrap_result(payload)}])

    _attach_tool_metadata(
        get_doc_section,
        Tool,
        name="get_doc_section",
        description="Return a full document or a named section by heading.",
        input_schema={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Document identifier as returned by list_resources",
                },
                "heading": {
                    "type": ["string", "null"],
                    "description": "Optional heading to slice out of the document",
                },
            },
            "required": ["doc_id"],
        },
    )

    return server


class _CallableServer:
    """Wrap a callable ``run`` method so it behaves like a server with ``serve``."""

    def __init__(self, run_callable: Callable[..., Any]):
        self._run = run_callable

    def serve(self) -> Any:
        result = self._run()
        if inspect.isawaitable(result):
            return result
        return result


def _register_callback(hook: Callable[..., Any], func: Callable[..., Any]) -> None:
    try:
        hook(func)
        return
    except TypeError:
        pass
    decorator = hook()
    decorator(func)


def _register_tool(
    hook: Callable[..., Any],
    func: Callable[..., Any],
    *,
    name: str,
    description: str,
    input_schema: dict[str, Any],
    Tool: Any,
) -> None:
    metadata = {"name": name, "description": description, "inputSchema": input_schema}
    decorator = None
    try:
        decorator = hook(**metadata)
    except TypeError:
        try:
            decorator = hook(name, description=description, inputSchema=input_schema)
        except TypeError:
            decorator = None
    if decorator is None:
        hook(func)
    else:
        decorator(func)

    _attach_tool_metadata(func, Tool, name=name, description=description, input_schema=input_schema)


def _resolve_attr(obj: Any, names: Sequence[str]) -> Optional[Callable[..., Any]]:
    for name in names:
        candidate = getattr(obj, name, None)
        if callable(candidate):
            return candidate
    return None


def _build_resource_payload(Resource: Any, record: DocumentRecord, project_root: Path) -> Any:
    uri = f"flarchitect-doc://{record.doc_id}"
    description = str(record.path.relative_to(project_root))
    payload = {
        "uri": uri,
        "name": record.title,
        "description": description,
        "mimeType": _guess_mime(record),
    }
    if Resource is not None:
        return Resource(**payload)
    return payload


def _build_text_contents_payload(TextResourceContents: Any, uri: str, content: str) -> Any:
    payload = {"uri": uri, "text": content}
    if TextResourceContents is not None:
        return TextResourceContents(**payload)
    return payload


def _attach_tool_metadata(func: Any, Tool: Any, *, name: str, description: str, input_schema: dict[str, Any]) -> None:
    if Tool is not None:
        func.definition = Tool(  # type: ignore[attr-defined]
            name=name,
            description=description,
            inputSchema=input_schema,
        )
    else:
        func.definition = {  # type: ignore[attr-defined]
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }


def _guess_mime(record: DocumentRecord) -> str:
    suffix = record.path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix == ".rst":
        return "text/x-rst"
    return "text/plain"


def _build_doc_url(doc_id: str) -> str:
    return f"flarchitect-doc://{doc_id}"


def _wrap_result(payload: Any) -> dict[str, Any]:
    return {"result": payload}


def _format_hit(index: DocumentIndex, hit: SearchHit) -> dict[str, Any]:
    try:
        record = index.get(hit.doc_id)
        title = record.title
    except KeyError:  # pragma: no cover - defensive guard
        title = hit.path.stem.replace("_", " ").title()
    url = _build_doc_url(hit.doc_id)
    item = {
        "doc_id": hit.doc_id,
        "title": title,
        "url": url,
        "uri": url,
        "score": 1.0,
        "snippet": hit.snippet,
        "line": hit.line_number,
    }
    if hit.heading is not None:
        item["heading"] = hit.heading
    return item


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the flarchitect MCP documentation server")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Root of the flarchitect repository (defaults to current directory)",
    )
    parser.add_argument(
        "--name",
        default="flarchitect-docs",
        help="Server name advertised to MCP clients",
    )
    parser.add_argument(
        "--description",
        default="Documentation browser for the flarchitect REST API generator",
        help="Human readable description",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "fastmcp", "reference"],
        default="auto",
        help="Select the MCP backend implementation (auto tries fastmcp then falls back to the reference server).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    config = ServerConfig(
        project_root=args.project_root.resolve(),
        name=args.name,
        description=args.description,
    )
    index = build_index(config.project_root)
    server = create_server(config, index, backend=args.backend)
    result = server.serve()
    if inspect.isawaitable(result):
        import asyncio

        asyncio.run(result)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
