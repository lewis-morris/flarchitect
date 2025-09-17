from pathlib import Path

import pytest

from flarchitect.mcp.index import DocumentIndex


def _create_markdown(path: Path, heading: str, body: str) -> None:
    path.write_text(f"# {heading}\n\n{body}\n", encoding="utf-8")


def _create_rst(path: Path, heading: str, body: str) -> None:
    underline = "=" * len(heading)
    path.write_text(f"{heading}\n{underline}\n\n{body}\n", encoding="utf-8")


@pytest.fixture()
def sample_index(tmp_path: Path) -> DocumentIndex:
    docs_dir = tmp_path / "docs" / "source"
    docs_dir.mkdir(parents=True)

    guide = docs_dir / "guide.rst"
    _create_rst(guide, "Guide", "Installation instructions and CRUD operations.")

    advanced = docs_dir / "advanced_configuration.rst"
    _create_rst(
        advanced,
        "Callbacks",
        "Callbacks allow create, read, update, delete hooks for filtering responses.",
    )

    readme = tmp_path / "README.md"
    _create_markdown(readme, "Overview", "Project introduction.")

    suggestions = tmp_path / "SUGGESTIONS.md"
    suggestions.write_text("- [ ] Pending task\n", encoding="utf-8")

    return DocumentIndex(tmp_path)


def test_list_documents_skips_excluded_files(sample_index: DocumentIndex) -> None:
    documents = sample_index.list_documents()
    doc_ids = {doc.doc_id for doc in documents}
    assert "docs/source/guide.rst" in doc_ids
    assert "docs/source/advanced_configuration.rst" in doc_ids
    assert "README.md" not in doc_ids
    assert "SUGGESTIONS.md" not in doc_ids


def test_get_section_returns_plain_text(sample_index: DocumentIndex) -> None:
    content = sample_index.get_section("docs/source/guide.rst", "Guide")
    assert "Installation instructions" in content
    assert "==" not in content


def test_search_returns_hits(sample_index: DocumentIndex) -> None:
    hits = sample_index.search("crud")
    assert hits, "Expected synonym-backed search results"
    hit_doc_ids = {hit.doc_id for hit in hits}
    assert "docs/source/advanced_configuration.rst" in hit_doc_ids or "docs/source/guide.rst" in hit_doc_ids
