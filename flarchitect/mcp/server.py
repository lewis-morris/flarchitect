"""Model Context Protocol server exposing the flarchitect documentation set."""

from __future__ import annotations

import argparse
import inspect
import json
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

from flarchitect import __version__ as PACKAGE_VERSION

from .index import DocumentIndex, DocumentRecord, SearchHit


PROTOCOL_VERSION = "2025-06-18"
DOC_URI_PREFIX = "flarchitect-doc://"

_SEARCH_INPUT_SCHEMA = {
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
}

_SECTION_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_id": {
            "type": "string",
            "description": "Document identifier as returned by tools/list",
        },
        "heading": {
            "type": ["string", "null"],
            "description": "Optional heading to slice out of the document",
        },
    },
    "required": ["doc_id"],
}

_TOOL_DEFINITIONS: tuple[tuple[str, str, dict[str, Any]], ...] = (
    (
        "search_docs",
        "Search flarchitect documentation for matching text.",
        _SEARCH_INPUT_SCHEMA,
    ),
    (
        "get_doc_section",
        "Return a full document or a named section by heading.",
        _SECTION_INPUT_SCHEMA,
    ),
)


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
            "Unable to construct the reference MCP server. Install the upstream 'mcp' package (https://github.com/modelcontextprotocol/python-sdk) to enable the reference backend."
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

    if not _configure_fastmcp(app, config, index):
        return None

    run_callable = _resolve_attr(app, ("serve", "run", "start"))
    if run_callable is None:
        return None

    return _CallableServer(run_callable)


def _configure_fastmcp(app: Any, config: ServerConfig, index: DocumentIndex) -> bool:
    add_resource = getattr(app, "add_resource", None)
    tool_decorator = getattr(app, "tool", None)
    if add_resource is None or tool_decorator is None:
        return False

    try:
        from typing import Annotated

        from pydantic import Field

        resources_module = import_module("fastmcp.resources")
        TextResource = getattr(resources_module, "TextResource")

        tools_module = import_module("fastmcp.tools")
        ToolResultCls = getattr(tools_module, "ToolResult", None)
        if ToolResultCls is None:
            tool_module = import_module("fastmcp.tools.tool")
            ToolResultCls = getattr(tool_module, "ToolResult", None)
    except Exception:  # pragma: no cover - fastmcp not available or incompatible
        return False

    from_standard = _load_standard_models()

    project_root = config.project_root
    for record in index.list_documents():
        try:
            description = str(record.path.relative_to(project_root))
        except ValueError:
            description = record.path.name
        resource = _build_resource_payload(TextResource, TextResource, record, project_root)
        add_resource(resource)

    @tool_decorator(
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
        hits = index.search(query, limit=int(limit))
        structured = {"result": [_format_hit(index, hit) for hit in hits]}
        return _build_tool_result(ToolResultCls, from_standard.tool_result, structured)

    @tool_decorator(
        name="get_doc_section",
        description="Return a full document or a named section by heading.",
    )
    async def get_doc_section(
        doc_id: Annotated[
            str,
            Field(
                description="Document identifier as returned by tools/list",
            ),
        ],
        heading: Annotated[
            str | None,
            Field(
                description="Optional heading to slice out of the document",
            ),
        ] = None,
    ) -> Any:
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
        structured = {
            "result": {
                "doc_id": doc_id,
                "title": record.title,
                "heading": heading,
                "content": content,
                "url": _build_doc_url(doc_id),
            }
        }
        return _build_tool_result(ToolResultCls, from_standard.tool_result, structured)

    return True


@dataclass(slots=True)
class _StandardModels:
    initialize_result: Any | None
    server_capabilities: Any | None
    resource_capabilities: Any | None
    tool_capabilities: Any | None
    list_resources_result: Any | None
    read_resource_result: Any | None
    resource: Any | None
    text_contents: Any | None
    tool: Any | None
    tool_result: Any | None


def _load_standard_models() -> _StandardModels:
    try:
        import mcp
        from mcp import types as mcp_types

        return _StandardModels(
            getattr(mcp, "InitializeResult", None),
            getattr(mcp, "ServerCapabilities", None),
            getattr(mcp, "ResourcesCapability", None),
            getattr(mcp, "ToolsCapability", None),
            getattr(mcp, "ListResourcesResult", None),
            getattr(mcp, "ReadResourceResult", None),
            getattr(mcp_types, "Resource", None),
            getattr(mcp_types, "TextResourceContents", None),
            getattr(mcp_types, "Tool", None),
            getattr(mcp_types, "CallToolResult", None),
        )
    except Exception:
        try:
            standard = import_module("modelcontextprotocol.standard")
        except Exception:  # pragma: no cover - optional dependency
            return _StandardModels(*(None,) * 10)

        def _get(name: str) -> Any | None:
            return getattr(standard, name, None)

        return _StandardModels(
            _get("InitializeResult"),
            _get("ServerCapabilities"),
            _get("ResourceServerCapabilities"),
            _get("ToolServerCapabilities"),
            _get("ListResourcesResult"),
            _get("ReadResourceResult"),
            _get("Resource"),
            _get("TextResourceContents"),
            _get("Tool"),
            _get("ToolResult"),
        )


def _build_initialize_payload(config: ServerConfig, models: _StandardModels) -> Any:
    server_info = {
        "name": config.name,
        "title": config.description,
        "version": config.version,
    }
    capabilities = {
        "resources": {"listChanged": True},
        "tools": {"listChanged": True},
    }
    if models.initialize_result is None or models.server_capabilities is None:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": server_info,
            "capabilities": capabilities,
        }
    server_caps = models.server_capabilities(
        resources=models.resource_capabilities(listChanged=True)
        if models.resource_capabilities is not None
        else None,
        tools=models.tool_capabilities(listChanged=True)
        if models.tool_capabilities is not None
        else None,
    )
    return models.initialize_result(
        protocolVersion=PROTOCOL_VERSION,
        serverInfo=server_info,
        capabilities=server_caps,
    )


def _create_reference_server(config: ServerConfig, index: DocumentIndex):
    from_standard = _load_standard_models()

    try:
        from mcp.server.lowlevel import Server as MCPServer
        from mcp.server import stdio as mcp_stdio
        from mcp import types as mcp_types
    except ImportError:
        MCPServer = None  # type: ignore[assignment]

    if MCPServer is not None:
        server = MCPServer(config.name, config.version, instructions=config.description)

        @server.list_resources()
        async def _list_resources() -> list[Any]:
            return [
                _build_resource_payload(
                    mcp_types.Resource,
                    None,
                    record,
                    config.project_root,
                )
                for record in index.list_documents()
            ]

        @server.read_resource()
        async def _read_resource(uri: str) -> str:
            doc_id = str(uri).replace(DOC_URI_PREFIX, "", 1)
            try:
                record = index.get(doc_id)
            except KeyError as exc:
                raise ValueError(f"No document with id '{doc_id}'") from exc
            return record.content

        tool_definitions = [
            _build_tool_definition(mcp_types.Tool, *definition)
            for definition in _TOOL_DEFINITIONS
        ]

        @server.list_tools()
        async def _list_tools() -> list[Any]:
            return tool_definitions

        @server.call_tool()
        async def _call_tool(name: str, arguments: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
            if name == "search_docs":
                hits = index.search(str(arguments.get("query") or ""), limit=int(arguments.get("limit", 10)))
                structured = {"result": [_format_hit(index, hit) for hit in hits]}
                text = mcp_types.TextContent(type="text", text=json.dumps(structured, indent=2))
                return ([text], structured)

            if name == "get_doc_section":
                doc_id = arguments.get("doc_id")
                if not doc_id:
                    raise ValueError("'doc_id' is required")
                try:
                    record = index.get(doc_id)
                except KeyError as exc:
                    raise ValueError(str(exc)) from exc
                heading = arguments.get("heading")
                try:
                    content = index.get_section(doc_id, heading)
                except KeyError as exc:
                    raise ValueError(str(exc)) from exc
                structured = {
                    "result": {
                        "doc_id": doc_id,
                        "title": record.title,
                        "heading": heading,
                        "content": content,
                        "url": _build_doc_url(doc_id),
                    }
                }
                text = mcp_types.TextContent(type="text", text=json.dumps(structured, indent=2))
                return ([text], structured)

            raise ValueError(f"Unknown tool '{name}'")

        init_options = server.create_initialization_options()

        class _StdIOServer:
            def __init__(self, srv: MCPServer, stdio_mod: Any, init_opts: Any) -> None:
                self._server = srv
                self._stdio = stdio_mod
                self._init_options = init_opts

            def serve(self) -> None:
                import anyio

                async def runner() -> None:
                    async with self._stdio.stdio_server() as (read_stream, write_stream):
                        await self._server.run(read_stream, write_stream, self._init_options)

                anyio.run(runner)

        return _StdIOServer(server, mcp_stdio, init_options)

    try:
        from modelcontextprotocol.server import Server
        from modelcontextprotocol.types import (
            CallToolRequest,
            InitializeRequest,
            ListResourcesRequest,
            ReadResourceRequest,
        )
    except ImportError:
        return None

    server = Server(config.name, config.version, description=config.description)

    @server.method("initialize")
    async def _initialize(_: InitializeRequest):  # type: ignore[name-defined]
        return _build_initialize_payload(config, from_standard)

    @server.method("resources/list")
    async def _resources_list(_: ListResourcesRequest):  # type: ignore[name-defined]
        resources = [
            _build_resource_payload(from_standard.resource, None, record, config.project_root)
            for record in index.list_documents()
        ]
        if from_standard.list_resources_result is not None:
            return from_standard.list_resources_result(resources=resources)
        return {"resources": resources}

    @server.method("resources/read")
    async def _resources_read(request: ReadResourceRequest):  # type: ignore[name-defined]
        uri = getattr(request, "uri", None) or getattr(request, "params", {}).get("uri")
        if not uri:
            raise ValueError("'uri' is required to read a resource")
        doc_id = str(uri).replace(DOC_URI_PREFIX, "", 1)
        try:
            record = index.get(doc_id)
        except KeyError as exc:
            raise ValueError(f"No document with id '{doc_id}'") from exc
        contents = _build_text_contents_payload(from_standard.text_contents, uri, record)
        if from_standard.read_resource_result is not None:
            return from_standard.read_resource_result(contents=[contents])
        return {"contents": [contents]}

    tool_definitions: list[Any] = []

    @server.method("tools/list")
    async def _tools_list(_: Any):  # type: ignore[name-defined]
        return {"tools": list(tool_definitions)}

    @server.method("tools/call")
    async def _tools_call(request: CallToolRequest):  # type: ignore[name-defined]
        tool_name = getattr(request, "name", None) or getattr(request, "tool", None)
        arguments = _extract_arguments(request)
        if tool_name == "search_docs":
            hits = index.search(str(arguments.get("query") or ""), limit=int(arguments.get("limit", 10)))
            structured = {"result": [_format_hit(index, hit) for hit in hits]}
            return _build_tool_result(None, from_standard.tool_result, structured)
        if tool_name == "get_doc_section":
            doc_id = arguments.get("doc_id")
            if not doc_id:
                raise ValueError("'doc_id' is required")
            try:
                record = index.get(doc_id)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc
            heading = arguments.get("heading")
            try:
                content = index.get_section(doc_id, heading)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc
            structured = {
                "result": {
                    "doc_id": doc_id,
                    "title": record.title,
                    "heading": heading,
                    "content": content,
                    "url": _build_doc_url(doc_id),
                }
            }
            return _build_tool_result(None, from_standard.tool_result, structured)
        raise ValueError(f"Unknown tool '{tool_name}'")

    for definition in _TOOL_DEFINITIONS:
        tool_definitions.append(
            _build_tool_definition(from_standard.tool, *definition)
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
    from_standard: _StandardModels,
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

    _attach_tool_metadata(
        func,
        from_standard.tool,
        name=name,
        description=description,
        input_schema=input_schema,
    )


def _resolve_attr(obj: Any, names: Sequence[str]) -> Optional[Callable[..., Any]]:
    for name in names:
        candidate = getattr(obj, name, None)
        if callable(candidate):
            return candidate
    return None


def _build_resource_payload(
    standard_resource: Any,
    fastmcp_resource: Any,
    record: DocumentRecord,
    project_root: Path,
) -> Any:
    try:
        description = str(record.path.relative_to(project_root))
    except ValueError:
        description = record.path.name
    mime = _guess_mime(record)
    base = {
        "uri": _build_doc_url(record.doc_id),
        "name": record.doc_id,
        "title": record.title,
        "description": description,
        "mimeType": mime,
        "mime_type": mime,
    }

    fastmcp_payload = dict(base)
    fastmcp_payload["text"] = record.content
    obj = _instantiate(fastmcp_resource, fastmcp_payload)
    if obj is not None:
        return obj

    obj = _instantiate(standard_resource, base)
    if obj is not None:
        return obj

    return {
        "uri": base["uri"],
        "name": base["name"],
        "title": base["title"],
        "description": description,
        "mimeType": mime,
    }


def _build_text_contents_payload(standard_contents: Any, uri: str, record: DocumentRecord) -> Any:
    mime = _guess_mime(record)
    payload = {
        "uri": uri,
        "name": record.doc_id,
        "title": record.title,
        "mimeType": mime,
        "mime_type": mime,
        "text": record.content,
    }
    obj = _instantiate(standard_contents, payload)
    if obj is not None:
        return obj
    return {
        "uri": uri,
        "name": record.doc_id,
        "title": record.title,
        "mimeType": mime,
        "text": record.content,
    }


def _build_tool_result(fastmcp_result: Any, standard_result: Any, structured: dict[str, Any]) -> Any:
    json_text = json.dumps(structured, ensure_ascii=False, indent=2)
    content_entry = {
        "type": "text",
        "text": json_text,
        "mimeType": "application/json",
        "mediaType": "application/json",
    }
    payload = {
        "content": [content_entry],
        "structuredContent": structured,
        "structured_content": structured,
    }

    obj = _instantiate(fastmcp_result, payload)
    if obj is not None:
        return obj

    obj = _instantiate(standard_result, payload)
    if obj is not None:
        return obj

    return {
        "content": [
            {
                "type": "text",
                "mimeType": "application/json",
                "text": json_text,
            }
        ],
        "structuredContent": structured,
    }


def _attach_tool_metadata(
    func: Any,
    tool_cls: Any,
    *,
    name: str,
    description: str,
    input_schema: dict[str, Any],
) -> None:
    func.definition = _build_tool_definition(tool_cls, name, description, input_schema)  # type: ignore[attr-defined]


def _build_tool_definition(
    tool_cls: Any,
    name: str,
    description: str,
    input_schema: dict[str, Any],
) -> Any:
    definition_payload = {
        "name": name,
        "title": description,
        "description": description,
        "inputSchema": input_schema,
        "input_schema": input_schema,
    }
    obj = _instantiate(tool_cls, definition_payload)
    if obj is not None:
        return obj
    return {
        "name": name,
        "title": description,
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
    return f"{DOC_URI_PREFIX}{doc_id}"


def _instantiate(cls: Any, payload: dict[str, Any]) -> Any | None:
    if cls is None:
        return None
    try:
        signature = inspect.signature(cls)
    except (TypeError, ValueError):
        try:
            return cls(**payload)
        except TypeError:  # pragma: no cover - incompatible signature
            return None

    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
        try:
            return cls(**payload)
        except TypeError:  # pragma: no cover - incompatible signature
            pass

    kwargs: dict[str, Any] = {}
    for name in signature.parameters:
        if name in payload:
            kwargs[name] = payload[name]
            continue
        camel = _to_camel(name)
        if camel in payload:
            kwargs[name] = payload[camel]
    try:
        return cls(**kwargs)
    except TypeError:  # pragma: no cover - incompatible signature
        return None


def _to_camel(name: str) -> str:
    parts = name.split("_")
    if not parts:
        return name
    first, *rest = parts
    return first + "".join(word.capitalize() for word in rest)


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


def _extract_arguments(request: Any) -> dict[str, Any]:
    if request is None:
        return {}
    arguments = _get_field(request, "arguments")
    if isinstance(arguments, dict):
        return dict(arguments)
    params = _get_field(request, "params")
    if isinstance(params, dict):
        if isinstance(params.get("arguments"), dict):
            return dict(params["arguments"])
        return dict(params)
    return {}


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
