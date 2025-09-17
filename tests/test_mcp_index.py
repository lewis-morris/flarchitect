from pathlib import Path

import pytest

from flarchitect.mcp.index import DocumentIndex


def _create_markdown(path: Path, heading: str, body: str) -> None:
    path.write_text(f"# {heading}\n\n{body}\n", encoding="utf-8")


def _create_rst(path: Path, heading: str, body: str) -> None:
    path.write_text(f"{heading}\n{'=' * len(heading)}\n\n{body}\n", encoding="utf-8")


@pytest.fixture()
def sample_index(tmp_path: Path) -> DocumentIndex:
    docs_dir = tmp_path / "docs" / "source"
    docs_dir.mkdir(parents=True)
    rst_file = docs_dir / "guide.rst"
    _create_rst(rst_file, "Guide", "Details about the system.")

    readme = tmp_path / "README.md"
    _create_markdown(readme, "Overview", "Project introduction.")

    return DocumentIndex(
        [docs_dir],
        aliases={docs_dir: "docs/source"},
        extra_files={readme: "README.md"},
    )


def test_list_documents_includes_aliases(sample_index: DocumentIndex) -> None:
    documents = sample_index.list_documents()
    doc_ids = {doc.doc_id for doc in documents}
    assert "docs/source/guide.rst" in doc_ids
    assert "README.md" in doc_ids


def test_get_section_returns_markdown_heading(sample_index: DocumentIndex) -> None:
    content = sample_index.get_section("README.md", "Overview")
    assert "Project introduction." in content
    assert "# Overview" not in content


def test_search_returns_hits(sample_index: DocumentIndex) -> None:
    hits = sample_index.search("project")
    assert hits, "Expected at least one search hit"
    hit_doc_ids = {hit.doc_id for hit in hits}
    assert "README.md" in hit_doc_ids
