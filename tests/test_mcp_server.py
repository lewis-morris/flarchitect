import asyncio
import sys
import types
from pathlib import Path
from typing import ClassVar

import pytest

from flarchitect.mcp.index import DocumentIndex, DocumentRecord, SearchHit
from flarchitect.mcp.server import (
    DOC_URI_PREFIX,
    ServerConfig,
    _build_doc_url,
    _build_resource_payload,
    _build_text_contents_payload,
    _build_tool_definition,
    _build_tool_result,
    _document_id_candidates,
    _extract_arguments,
    _format_hit,
    _get_doc_section_payload,
    _guess_mime,
    _instantiate,
    _resolve_attr,
    _run_docs_tool,
    build_index,
    create_server,
)


class _FakeTextResource:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeToolResult:
    def __init__(self, content=None, structured_content=None):
        if content is None and structured_content is None:
            raise ValueError("ToolResult requires content or structured_content")
        if content is None:
            content = structured_content
        self.content = content
        self.structured_content = structured_content
        self.structuredContent = structured_content


class _FakeFastMCP:
    instances: ClassVar[list["_FakeFastMCP"]] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.tools: dict[str, dict[str, object]] = {}
        self.resources: list[_FakeTextResource] = []
        self.run_called = False
        type(self).instances.append(self)

    def add_resource(self, resource):
        self.resources.append(resource)
        return resource

    def tool(self, *args, **kwargs):
        if args and callable(args[0]):
            fn = args[0]
            name = fn.__name__
            self.tools[name] = {"func": fn, "metadata": {"name": name}}
            return fn

        name = kwargs.get("name")

        def decorator(fn):
            tool_name = name or fn.__name__
            self.tools[tool_name] = {
                "func": fn,
                "metadata": kwargs,
            }
            return fn

        return decorator

    def run(self):
        self.run_called = True


class _FakeMCPModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeTextContent(_FakeMCPModel):
    pass


class _FakeLowLevelServer:
    instances: ClassVar[list["_FakeLowLevelServer"]] = []

    def __init__(self, name: str, version: str, instructions: str):
        self.name = name
        self.version = version
        self.instructions = instructions
        self.handlers: dict[str, object] = {}
        type(self).instances.append(self)

    def list_resources(self):
        def decorator(fn):
            self.handlers["list_resources"] = fn
            return fn

        return decorator

    def read_resource(self):
        def decorator(fn):
            self.handlers["read_resource"] = fn
            return fn

        return decorator

    def list_tools(self):
        def decorator(fn):
            self.handlers["list_tools"] = fn
            return fn

        return decorator

    def call_tool(self):
        def decorator(fn):
            self.handlers["call_tool"] = fn
            return fn

        return decorator

    def create_initialization_options(self):
        return {"name": self.name, "version": self.version}


class _FakeLegacyServer:
    instances: ClassVar[list["_FakeLegacyServer"]] = []

    def __init__(self, name: str, version: str, description: str):
        self.name = name
        self.version = version
        self.description = description
        self.handlers: dict[str, object] = {}
        type(self).instances.append(self)

    def method(self, name: str):
        def decorator(fn):
            self.handlers[name] = fn
            return fn

        return decorator


@pytest.fixture()
def doc_index(tmp_path: Path) -> DocumentIndex:
    docs_dir = tmp_path / "docs" / "source"
    docs_dir.mkdir(parents=True)
    (docs_dir / "guide.rst").write_text(
        "Guide\n=====\n\nSome details about installation.\n",
        encoding="utf-8",
    )
    (docs_dir / "advanced_configuration.rst").write_text(
        "Callbacks\n==========\n\nHooks for create, read, update, delete.\n",
        encoding="utf-8",
    )
    llms_file = tmp_path / "llms.txt"
    llms_file.write_text("LLM index", encoding="utf-8")
    return DocumentIndex(tmp_path, extra_files={llms_file: "llms.txt"})


def test_build_index_falls_back_to_packaged_docs(tmp_path: Path) -> None:
    index = build_index(tmp_path)

    documents = index.list_documents()
    assert documents, "Expected fallback index to expose packaged documentation"
    doc_ids = {doc.doc_id for doc in documents}
    assert any(doc_id.startswith(("docs/source/", "docs/md/")) for doc_id in doc_ids)
    assert "llms.txt" in doc_ids

    hits = index.search("installation")
    assert hits, "Expected packaged docs to include installation guidance"


def test_fastmcp_backend_registration(monkeypatch, doc_index: DocumentIndex) -> None:
    module = types.ModuleType("fastmcp")
    module.FastMCP = _FakeFastMCP
    resources_module = types.ModuleType("fastmcp.resources")
    resources_module.TextResource = _FakeTextResource
    tools_module = types.ModuleType("fastmcp.tools")
    tools_module.__path__ = []  # treat as package so submodule import works
    tool_submodule = types.ModuleType("fastmcp.tools.tool")
    tool_submodule.ToolResult = _FakeToolResult
    monkeypatch.setitem(sys.modules, "fastmcp", module)  # type: ignore[name-defined]
    monkeypatch.setitem(sys.modules, "fastmcp.resources", resources_module)
    monkeypatch.setitem(sys.modules, "fastmcp.tools", tools_module)
    monkeypatch.setitem(sys.modules, "fastmcp.tools.tool", tool_submodule)

    config = ServerConfig(project_root=doc_index.roots[0].parent.parent)
    server = create_server(config, doc_index, backend="auto")

    fake_instance = _FakeFastMCP.instances[-1]
    assert {"search_docs", "get_doc_section"} <= set(fake_instance.tools.keys())
    assert fake_instance.resources, "Expected resources to be registered"
    first_resource = fake_instance.resources[0]
    assert first_resource.uri.startswith("flarchitect-doc://")
    resource_names = {resource.name for resource in fake_instance.resources}
    assert "llms.txt" in resource_names

    search_tool = fake_instance.tools["search_docs"]["func"]
    result = asyncio.run(search_tool(query="guide"))
    structured = result.structured_content
    assert structured["result"], "Expected search results"
    first = structured["result"][0]
    assert {"doc_id", "title", "url", "score", "snippet"} <= set(first.keys())
    assert first["url"].startswith("flarchitect-doc://")
    assert isinstance(first["score"], (int, float))
    assert first["snippet"]
    assert 0 < first["score"] <= 1
    assert result.content[0]["type"] == "text"

    get_section_tool = fake_instance.tools["get_doc_section"]["func"]
    section = asyncio.run(get_section_tool(doc_id="docs/source/guide.rst", heading=None))
    assert "Guide" in section.structured_content["result"]["content"]

    normalized_section = asyncio.run(get_section_tool(doc_id="GUIDE", heading=None))
    assert "installation" in normalized_section.structured_content["result"]["content"].lower()

    list_docs_tool = fake_instance.tools["list_docs"]["func"]
    listed = asyncio.run(list_docs_tool())
    docs_payload = listed.structured_content["result"]
    titles = {item["title"] for item in docs_payload}
    assert "Guide" in titles
    assert any(item["doc_id"].endswith("guide.rst") for item in docs_payload)
    assert any(item["doc_id"] == "llms.txt" for item in docs_payload)

    # The server wrapper should call the run method when serve() is invoked.
    assert fake_instance.run_called is False
    server.serve()
    assert fake_instance.run_called is True


def test_auto_backend_falls_back_to_reference(monkeypatch, doc_index: DocumentIndex) -> None:
    monkeypatch.delitem(sys.modules, "fastmcp", raising=False)

    sentinel = object()
    monkeypatch.setattr("flarchitect.mcp.server._create_fastmcp_server", lambda config, index: None)
    monkeypatch.setattr("flarchitect.mcp.server._create_reference_server", lambda config, index: sentinel)

    config = ServerConfig(project_root=doc_index.roots[0].parent.parent)
    server = create_server(config, doc_index, backend="auto")
    assert server is sentinel


def test_fastmcp_backend_requires_library(monkeypatch, doc_index: DocumentIndex) -> None:
    monkeypatch.setattr("flarchitect.mcp.server._create_fastmcp_server", lambda config, index: None)
    config = ServerConfig(project_root=doc_index.roots[0].parent.parent)
    with pytest.raises(RuntimeError):
        create_server(config, doc_index, backend="fastmcp")


def test_lowlevel_reference_backend_registers_resources_and_tools(monkeypatch, doc_index: DocumentIndex) -> None:
    mcp_module = types.ModuleType("mcp")
    mcp_types = types.ModuleType("mcp.types")
    mcp_types.Resource = _FakeMCPModel
    mcp_types.Tool = _FakeMCPModel
    mcp_types.TextContent = _FakeTextContent
    mcp_module.types = mcp_types

    server_module = types.ModuleType("mcp.server")
    server_module.__path__ = []
    stdio_module = types.ModuleType("mcp.server.stdio")
    lowlevel_module = types.ModuleType("mcp.server.lowlevel")
    lowlevel_module.Server = _FakeLowLevelServer

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.types", mcp_types)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.stdio", stdio_module)
    monkeypatch.setitem(sys.modules, "mcp.server.lowlevel", lowlevel_module)

    config = ServerConfig(project_root=doc_index.roots[0].parent.parent, name="docs", version="1.2.3")
    server = create_server(config, doc_index, backend="reference")
    fake_server = _FakeLowLevelServer.instances[-1]

    assert fake_server.name == "docs"
    assert fake_server.version == "1.2.3"

    resources = asyncio.run(fake_server.handlers["list_resources"]())
    assert resources
    assert resources[0].uri.startswith(DOC_URI_PREFIX)

    content = asyncio.run(fake_server.handlers["read_resource"]("flarchitect-doc://GUIDE"))
    assert "installation" in content.lower()
    with pytest.raises(ValueError, match="No document"):
        asyncio.run(fake_server.handlers["read_resource"]("flarchitect-doc://missing"))

    tools = asyncio.run(fake_server.handlers["list_tools"]())
    tool_names = {tool.name for tool in tools}
    assert {"list_docs", "search_docs", "get_doc_section"} <= tool_names

    text_entries, structured = asyncio.run(
        fake_server.handlers["call_tool"]("search_docs", {"query": "installation"})
    )
    assert structured["result"]
    assert text_entries[0].type == "text"
    assert "installation" in text_entries[0].text.lower()

    assert hasattr(server, "serve")


def test_legacy_reference_backend_registers_protocol_methods(monkeypatch, doc_index: DocumentIndex) -> None:
    monkeypatch.delitem(sys.modules, "mcp", raising=False)
    monkeypatch.delitem(sys.modules, "mcp.server.lowlevel", raising=False)

    standard_module = types.ModuleType("modelcontextprotocol.standard")
    for name in (
        "InitializeResult",
        "ServerCapabilities",
        "ResourceServerCapabilities",
        "ToolServerCapabilities",
        "ListResourcesResult",
        "ReadResourceResult",
        "Resource",
        "TextResourceContents",
        "Tool",
        "ToolResult",
    ):
        setattr(standard_module, name, _FakeMCPModel)

    server_module = types.ModuleType("modelcontextprotocol.server")
    server_module.Server = _FakeLegacyServer
    types_module = types.ModuleType("modelcontextprotocol.types")
    for name in ("CallToolRequest", "InitializeRequest", "ListResourcesRequest", "ReadResourceRequest"):
        setattr(types_module, name, _FakeMCPModel)

    monkeypatch.setitem(sys.modules, "modelcontextprotocol.standard", standard_module)
    monkeypatch.setitem(sys.modules, "modelcontextprotocol.server", server_module)
    monkeypatch.setitem(sys.modules, "modelcontextprotocol.types", types_module)

    config = ServerConfig(project_root=doc_index.roots[0].parent.parent, name="legacy-docs", version="2.0")
    server = create_server(config, doc_index, backend="reference")
    fake_server = _FakeLegacyServer.instances[-1]

    initialized = asyncio.run(fake_server.handlers["initialize"](_FakeMCPModel()))
    assert initialized.protocolVersion
    assert initialized.serverInfo["name"] == "legacy-docs"

    listed = asyncio.run(fake_server.handlers["resources/list"](_FakeMCPModel()))
    assert listed.resources
    assert listed.resources[0].uri.startswith(DOC_URI_PREFIX)

    read = asyncio.run(fake_server.handlers["resources/read"](_FakeMCPModel(uri="flarchitect-doc://GUIDE")))
    assert "installation" in read.contents[0].text.lower()

    with pytest.raises(ValueError, match="uri"):
        asyncio.run(fake_server.handlers["resources/read"](_FakeMCPModel(params={})))

    tools = asyncio.run(fake_server.handlers["tools/list"](_FakeMCPModel()))
    assert {tool.name for tool in tools["tools"]} == {"list_docs", "search_docs", "get_doc_section"}

    called = asyncio.run(
        fake_server.handlers["tools/call"](
            _FakeMCPModel(name="get_doc_section", arguments={"doc_id": "GUIDE", "heading": None})
        )
    )
    assert "installation" in called.structuredContent["result"]["content"].lower()
    assert hasattr(server, "method")


def test_create_server_rejects_unknown_backend(doc_index: DocumentIndex) -> None:
    config = ServerConfig(project_root=doc_index.roots[0].parent.parent)

    with pytest.raises(ValueError, match="backend must be one of"):
        create_server(config, doc_index, backend="unknown")


def test_create_server_reports_missing_reference_backend(monkeypatch, doc_index: DocumentIndex) -> None:
    monkeypatch.setattr("flarchitect.mcp.server._create_fastmcp_server", lambda config, index: None)
    monkeypatch.setattr("flarchitect.mcp.server._create_reference_server", lambda config, index: None)
    config = ServerConfig(project_root=doc_index.roots[0].parent.parent)

    with pytest.raises(RuntimeError, match="Unable to construct"):
        create_server(config, doc_index, backend="reference")


def test_docs_tool_payloads_resolve_aliases_and_errors(doc_index: DocumentIndex) -> None:
    list_payload = _run_docs_tool(doc_index, "list_docs", {})
    assert any(item["doc_id"].endswith("guide.rst") for item in list_payload["result"])

    search_payload = _run_docs_tool(doc_index, "search_docs", {"query": "installation", "limit": "2"})
    assert search_payload["result"]
    assert search_payload["result"][0]["url"].startswith(DOC_URI_PREFIX)

    section_payload = _run_docs_tool(doc_index, "get_doc_section", {"doc_id": "GUIDE", "heading": None})
    assert section_payload["result"]["doc_id"] == "docs/source/guide.rst"
    assert "installation" in section_payload["result"]["content"].lower()

    with pytest.raises(ValueError, match="doc_id"):
        _get_doc_section_payload(doc_index, "", None)
    with pytest.raises(ValueError, match="No document"):
        _get_doc_section_payload(doc_index, "missing", None)
    with pytest.raises(ValueError, match="Unknown tool"):
        _run_docs_tool(doc_index, "missing_tool", {})


def test_document_id_candidates_and_search_hit_formatting(doc_index: DocumentIndex, tmp_path: Path) -> None:
    assert _document_id_candidates("Guide") == ("Guide", "Guide.md", "Guide.rst", "guide", "guide.md", "guide.rst")

    known_hit = SearchHit(
        doc_id="docs/source/guide.rst",
        path=doc_index.roots[0] / "guide.rst",
        line_number=-5,
        heading="Guide",
        snippet="installation",
    )
    formatted = _format_hit(doc_index, known_hit)
    assert formatted["score"] == 1
    assert formatted["heading"] == "Guide"

    unknown_path = tmp_path / "missing_topic.rst"
    unknown_hit = SearchHit(
        doc_id="missing_topic.rst",
        path=unknown_path,
        line_number=3,
        heading=None,
        snippet="fallback title",
    )
    fallback = _format_hit(doc_index, unknown_hit)
    assert fallback["title"] == "Missing Topic"
    assert "heading" not in fallback


def test_payload_builders_fallbacks_and_class_construction(tmp_path: Path) -> None:
    rst_path = tmp_path / "guide.rst"
    rst_path.write_text("Guide\n=====\n", encoding="utf-8")
    md_path = tmp_path / "guide.md"
    md_path.write_text("# Guide\n", encoding="utf-8")
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("notes\n", encoding="utf-8")

    rst_record = DocumentRecord("guide.rst", rst_path, "Guide", (), rst_path.read_text(encoding="utf-8"))
    md_record = DocumentRecord("guide.md", md_path, "Guide", (), md_path.read_text(encoding="utf-8"))
    txt_record = DocumentRecord("notes.txt", txt_path, "Notes", (), txt_path.read_text(encoding="utf-8"))

    assert _guess_mime(md_record) == "text/markdown"
    assert _guess_mime(rst_record) == "text/x-rst"
    assert _guess_mime(txt_record) == "text/plain"
    assert _build_doc_url("guide.rst") == f"{DOC_URI_PREFIX}guide.rst"

    outside_record = DocumentRecord("outside.rst", tmp_path.parent / "outside.rst", "Outside", (), "outside")
    resource = _build_resource_payload(None, None, outside_record, tmp_path)
    assert resource["description"] == "outside.rst"
    assert resource["mimeType"] == "text/x-rst"

    contents = _build_text_contents_payload(None, "uri", rst_record)
    assert contents["text"] == rst_record.content
    assert contents["mimeType"] == "text/x-rst"

    tool_result = _build_tool_result(None, None, {"result": [{"doc_id": "guide.rst"}]})
    assert tool_result["structuredContent"]["result"][0]["doc_id"] == "guide.rst"
    assert tool_result["content"][0]["mimeType"] == "application/json"

    tool_definition = _build_tool_definition(
        None,
        name="search_docs",
        description="Search docs",
        input_schema={"type": "object"},
        output_schema=None,
        tags=None,
        annotations=None,
    )
    assert tool_definition == {
        "name": "search_docs",
        "title": "Search docs",
        "description": "Search docs",
        "inputSchema": {"type": "object"},
    }

    class CamelOnly:
        def __init__(self, mimeType: str) -> None:  # noqa: N803 - external SDK style
            self.mime_type = mimeType

    assert _instantiate(CamelOnly, {"mimeType": "text/plain"}).mime_type == "text/plain"
    assert _instantiate(None, {}) is None


def test_resolve_attr_and_argument_extraction() -> None:
    class Runner:
        def run(self) -> str:
            return "ran"

    assert _resolve_attr(Runner(), ("serve", "run"))() == "ran"
    assert _resolve_attr(object(), ("serve", "run")) is None

    assert _extract_arguments(None) == {}
    assert _extract_arguments({"arguments": {"limit": 2}}) == {"limit": 2}
    assert _extract_arguments({"params": {"arguments": {"query": "docs"}}}) == {"query": "docs"}
    assert _extract_arguments({"params": {"query": "docs"}}) == {"query": "docs"}
