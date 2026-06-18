from pathlib import Path

import pytest

from flarchitect.mcp.index import (
    DocumentIndex,
    _parse_rst_document,
    _RSTHTMLToTextParser,
    _strip_heading,
)


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

    faq = docs_dir / "faq.rst"
    faq.write_text(
        """
.. dropdown:: Can I extend the functionality of the API?

    The :class:`flarchitect.Architect` integrates :doc:`plugins` and :ref:`hooks-cheatsheet`.
    Use :func:`flarchitect.utils.handle_result` for custom responses.
""".strip()
        + "\n",
        encoding="utf-8",
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


def test_rst_with_sphinx_markup_is_normalised(sample_index: DocumentIndex) -> None:
    content = sample_index.get_section("docs/source/faq.rst", heading=None)
    assert "flarchitect.Architect" in content
    assert "flarchitect.utils.handle_result" in content
    assert ":class:" not in content

    hits = sample_index.search("handle_result")
    assert any(hit.doc_id == "docs/source/faq.rst" for hit in hits)


def test_markdown_docs_are_indexed(tmp_path: Path) -> None:
    md_root = tmp_path / "docs" / "md"
    guide_dir = md_root / "guide"
    guide_dir.mkdir(parents=True)
    (guide_dir / "index.md").write_text(
        """# Guide\n\nIntro paragraph for guide.\n\n## Details\n\nSome markdown content.\n""",
        encoding="utf-8",
    )

    (guide_dir / "details.md").write_text(
        """[← Back to Guide index](index.md)\n\n# Details\n\nExtended information about the guide.\n""",
        encoding="utf-8",
    )

    index = DocumentIndex(tmp_path, doc_path=md_root)
    doc_ids = {doc.doc_id for doc in index.list_documents()}
    assert "docs/md/guide/index.md" in doc_ids
    assert "docs/md/guide/details.md" in doc_ids

    section_content = index.get_section("docs/md/guide/index.md", "Details")
    assert "Some markdown content." in section_content

    hits = index.search("extended information")
    assert any(hit.doc_id == "docs/md/guide/details.md" for hit in hits)


def test_document_index_validates_roots_and_uses_explicit_aliases(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="Documentation root"):
        DocumentIndex(missing)

    with pytest.raises(ValueError, match="at least one root"):
        DocumentIndex([])

    docs_one = tmp_path / "one"
    docs_two = tmp_path / "two"
    docs_one.mkdir()
    docs_two.mkdir()
    _create_markdown(docs_one / "guide.md", "Guide One", "alpha")
    _create_markdown(docs_two / "guide.md", "Guide Two", "beta")

    index = DocumentIndex(
        [docs_two, docs_one],
        aliases={docs_one: "first", docs_two: "second"},
    )

    assert [doc.doc_id for doc in index.list_documents()] == [
        "first/guide.md",
        "second/guide.md",
    ]
    assert index.get_section("first/guide.md", None).startswith("# Guide One")


def test_document_index_handles_file_roots_extra_files_and_refresh(tmp_path: Path) -> None:
    file_root = tmp_path / "standalone.txt"
    file_root.write_text("Standalone searchable text\n", encoding="utf-8")

    extra = tmp_path / "LLMS.txt"
    extra.write_text("# LLM Notes\n\nspecial instructions\n", encoding="utf-8")
    skipped_extra = tmp_path / "ignore.json"
    skipped_extra.write_text("{}", encoding="utf-8")

    index = DocumentIndex(
        [file_root],
        extra_files={extra: None, skipped_extra: "ignored.json"},
    )

    doc_ids = {doc.doc_id for doc in index.list_documents()}
    assert doc_ids == {"standalone.txt", "LLMS.txt"}
    assert index.search("   ") == []
    assert index.search("standalone", limit=1)[0].heading is None

    file_root.write_text("Changed text\n", encoding="utf-8")
    index.refresh()
    assert index.search("standalone") == []
    assert index.search("changed")[0].doc_id == "standalone.txt"


def test_document_index_sections_synonyms_and_unknown_ids(sample_index: DocumentIndex) -> None:
    with pytest.raises(KeyError, match="Unknown document id"):
        sample_index.get("docs/source/missing.rst")

    with pytest.raises(KeyError, match="Heading 'Missing'"):
        sample_index.get_section("docs/source/guide.rst", "Missing")

    hits = sample_index.search("callbacks callbacks", limit=2)
    assert len(hits) <= 2
    assert {hit.doc_id for hit in hits}


def test_rst_parser_falls_back_when_docutils_cannot_parse(monkeypatch, tmp_path: Path) -> None:
    from flarchitect.mcp import index as index_module

    def raise_import_error(*args, **kwargs):
        raise ImportError("docutils unavailable")

    monkeypatch.setattr(index_module, "publish_parts", raise_import_error)

    title, content, sections = _parse_rst_document(
        "Broken\n======\n\nUnparsed body.\n",
        tmp_path / "broken.rst",
    )

    assert title == "Broken"
    assert "Unparsed body" in content
    assert sections[0].anchor == "broken"


def test_rst_literalinclude_directive_reads_existing_and_missing_files(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "source"
    docs_dir.mkdir(parents=True)
    snippet = docs_dir / "snippet.py"
    snippet.write_text("print('hello')\n", encoding="utf-8")
    page = docs_dir / "code.rst"
    page.write_text(
        """Code
====

.. literalinclude:: snippet.py
   :language: python
   :linenos:

.. literalinclude:: missing.py
""",
        encoding="utf-8",
    )

    index = DocumentIndex(tmp_path)
    content = index.get_section("docs/source/code.rst", None)

    assert "print('hello')" in content
    assert "missing.py" not in content


def test_rst_html_parser_tracks_headings_flushes_breaks_and_sections() -> None:
    parser = _RSTHTMLToTextParser()
    parser.feed(
        """
        <section>
          <h1>Main <span>Title</span></h1>
          <p>Intro<br>continued</p>
          <h2>Details</h2>
          <ul><li>First item</li><li>Second item</li></ul>
        </section>
        """
    )

    text = parser.get_text()

    assert "Main Title" in text
    assert "Intro" in text
    assert "continued" in text
    assert [section.title for section in parser.sections] == ["Main Title", "Details"]
    assert parser.sections[0].end_line is not None
    assert parser.sections[-1].end_line == len(text.splitlines())


def test_rst_html_parser_handles_nested_heading_boundaries_and_blank_append() -> None:
    parser = _RSTHTMLToTextParser()
    parser.feed("<h1>One</h1><h2>Two</h2><h3>Three</h3></h4>")
    parser._append_line("")

    assert parser.get_text().splitlines() == ["One", "Two", "Three"]
    assert [section.end_line for section in parser.sections] == [1, 2, 3]


def test_rst_html_parser_ignores_blank_data_and_empty_buffers() -> None:
    parser = _RSTHTMLToTextParser()
    parser.feed("<p>   </p><br><h1>   </h1><span>loose</span>")

    assert parser.get_text() == "loose"
    assert parser.sections == []


def test_strip_heading_handles_empty_markdown_rst_and_plain_lines() -> None:
    assert _strip_heading([]) == []
    assert _strip_heading(["# Title", "body"]) == ["body"]
    assert _strip_heading(["Title", "=====", "body"]) == ["body"]
    assert _strip_heading(["Title", "---", "body"]) == ["body"]
    assert _strip_heading(["Title", "abc", "body"]) == ["Title", "abc", "body"]
    assert _strip_heading(["plain", "body"]) == ["plain", "body"]


def test_rst_parser_handles_html_without_document_title(monkeypatch, tmp_path: Path) -> None:
    from flarchitect.mcp import index as index_module

    monkeypatch.setattr(
        index_module,
        "publish_parts",
        lambda **kwargs: {"title": "", "body": "<h2>Only Heading</h2><p>Body text</p>"},
    )

    title, content, sections = _parse_rst_document("ignored", tmp_path / "untitled.rst")

    assert title == "Untitled"
    assert content == "Untitled\nOnly Heading\nBody text"
    assert [section.title for section in sections] == ["Untitled", "Only Heading"]
