import asyncio
import sys
import types
from pathlib import Path

import pytest

from flarchitect.mcp.index import DocumentIndex
from flarchitect.mcp.server import ServerConfig, create_server


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
    instances = []

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
        return None


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
    return DocumentIndex(tmp_path)


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
