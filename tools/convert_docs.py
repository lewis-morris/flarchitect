#!/usr/bin/env python3
"""Convert the Sphinx RST documentation into chunked Markdown and llms.txt."""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from docutils import nodes
from docutils.core import publish_doctree

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flarchitect.mcp.index import _prepare_rst_environment, _strip_sphinx_roles  # type: ignore  # noqa: E402

_ADMONITION_DEFAULT_TITLES = {
    nodes.attention: "Attention",
    nodes.caution: "Caution",
    nodes.danger: "Danger",
    nodes.error: "Error",
    nodes.hint: "Hint",
    nodes.important: "Important",
    nodes.note: "Note",
    nodes.tip: "Tip",
    nodes.warning: "Warning",
}

_ADMONITION_NODE_TYPES = (*_ADMONITION_DEFAULT_TITLES.keys(), nodes.admonition)

_LLMS_SUMMARY = (
    "flarchitect automates RESTful APIs from SQLAlchemy models, exposing configuration-rich tooling, "
    "authentication helpers, and documentation assets. It ships with an MCP server and composable hooks "
    "for plugins, callbacks, and schema orchestration."
)

_LLMS_CATEGORY_OVERRIDES = {
    "installation": "Getting Started",
    "quickstart": "Getting Started",
    "getting_started": "Getting Started",
    "advanced_demo": "Getting Started",
    "advanced_configuration": "Configuration",
    "configuration": "Configuration",
    "config_locations": "Configuration",
    "manual_routes": "Guides",
    "models": "Guides",
    "validation": "Guides",
    "extensions": "Guides",
    "plugins": "Guides",
    "authentication": "Security",
    "auth_cookbook": "Security",
    "websockets": "Guides",
    "hooks_cheatsheet": "Guides",
    "error_handling": "Guides",
    "faq": "Optional",
    "roadmap": "Optional",
    "mcp_server": "Developer Tooling",
    "llms": "Developer Tooling",
    "graphql": "Developer Tooling",
    "openapi": "Developer Tooling",
    "_configuration_table": "Configuration",
}

_LLMS_ORDERED_CATEGORIES = [
    "Getting Started",
    "Security",
    "Configuration",
    "Guides",
    "Developer Tooling",
]

_LLMS_PREFERRED_CATEGORY_POSITIONS = {
    "Developer Tooling": {
        "openapi/index.md": 0,
        "llms.md": 1,
        "mcp_server/index.md": 2,
    }
}

_HOSTED_DOCS_BASE = "https://lewis-morris.github.io/flarchitect/"


def _rewrite_refuri(refuri: str) -> str | None:
    if refuri.startswith(("http://", "https://", "mailto:")):
        return refuri
    if ".html#" in refuri:
        refuri = refuri.replace(".html#", "#")
    if refuri.endswith(".html"):
        refuri = refuri[:-5]
    if refuri.startswith("#"):
        return refuri
    # Drop unresolved intra-doc references; the surrounding text remains.
    return None


@dataclass
class SectionChunk:
    """Markdown output for a single document chunk."""

    title: str
    relative_path: Path
    content: str
    summary: str


@dataclass
class DocumentChunks:
    """All markdown chunks generated from a single RST source file."""

    source_path: Path
    output_dir: Path
    chunks: list[SectionChunk]


class MarkdownRenderer:
    """Minimal docutils -> Markdown renderer tailored for flarchitect docs."""

    def __init__(self, base_heading_level: int = 1) -> None:
        self.base_heading_level = base_heading_level

    def render_nodes(self, nodes_seq: Sequence[nodes.Node], *, initial_heading: str | None = None) -> str:
        lines: list[str] = []
        if initial_heading:
            lines.append(self._heading(initial_heading, self.base_heading_level))
            lines.append("")
        for node in nodes_seq:
            block = self._render_block(node, self.base_heading_level)
            if block:
                lines.append(block)
        return self._cleanup("\n".join(lines))

    # ------------------------------------------------------------------
    # Block renderers
    def _render_block(self, node: nodes.Node, level: int) -> str:
        if isinstance(node, nodes.title):
            return ""
        if isinstance(node, nodes.section):
            return self._render_section(node, level)
        if isinstance(node, nodes.paragraph):
            return self._render_inline_children(node)
        if isinstance(node, _ADMONITION_NODE_TYPES):
            return self._render_admonition(node, level)
        if isinstance(node, (nodes.system_message, nodes.comment, nodes.substitution_definition)):
            return ""
        simple_rendered = self._render_simple_block(node, level)
        if simple_rendered is not None:
            return simple_rendered
        return self._render_unknown_block(node, level)

    def _render_section(self, node: nodes.section, level: int) -> str:
        title_node = node.next_node(nodes.title, include_self=False)
        if title_node is None:
            return ""
        parts = [self._heading(self._render_inline_children(title_node), level), ""]
        for child in node.children:
            if child is title_node:
                continue
            rendered = self._render_block(child, level + 1 if isinstance(child, nodes.section) else level)
            if rendered:
                parts.append(rendered)
        return "\n".join(part for part in parts if part)

    def _render_admonition(self, node: nodes.Node, level: int) -> str:
        title_text = _ADMONITION_DEFAULT_TITLES.get(type(node), "Note")
        children = list(node.children)
        if isinstance(node, nodes.admonition) and children and isinstance(children[0], nodes.title):
            title_text = self._render_inline_children(children[0]) or title_text
            children = children[1:]

        body_parts = [rendered for child in children if (rendered := self._render_block(child, level))]
        lines = [f"> **{title_text}**"]
        lines.extend(f"> {part}" if part.strip() else ">" for part in "\n".join(body_parts).splitlines())
        return "\n".join(lines)

    def _render_simple_block(self, node: nodes.Node, level: int) -> str | None:
        if isinstance(node, (nodes.literal_block, nodes.doctest_block)):
            return self._render_code_block(node)
        list_rendered = self._render_list_block(node, level)
        if list_rendered is not None:
            return list_rendered
        if isinstance(node, nodes.table):
            return self._render_table(node)
        if isinstance(node, nodes.definition_list):
            return "\n\n".join(self._render_definition_item(item, level) for item in node.children)
        if isinstance(node, nodes.transition):
            return "\n---\n"
        leaf_rendered = self._render_leaf_block(node)
        if leaf_rendered is not None:
            return leaf_rendered
        return None

    @staticmethod
    def _render_code_block(node: nodes.Node) -> str:
        text = node.astext()
        return f"```\n{text}\n```"

    def _render_list_block(self, node: nodes.Node, level: int) -> str | None:
        if isinstance(node, nodes.bullet_list):
            return "\n".join(self._render_list_item(child, level, False, idx + 1) for idx, child in enumerate(node.children))
        if isinstance(node, nodes.enumerated_list):
            return "\n".join(
                self._render_list_item(child, level, True, idx + 1)
                for idx, child in enumerate(node.children)
            )
        if isinstance(node, nodes.list_item):
            return self._render_list_item(node, level, False, 1)
        if isinstance(node, nodes.block_quote):
            return self._render_block_quote(node, level)
        return None

    def _render_leaf_block(self, node: nodes.Node) -> str | None:
        if isinstance(node, nodes.line_block):
            return "\n".join(child.astext() for child in node.children)
        if isinstance(node, nodes.raw):
            return node.astext()
        if isinstance(node, nodes.reference):
            return self._render_inline_children(node)
        if isinstance(node, nodes.title_reference):
            return self._render_inline_children(node)
        if isinstance(node, nodes.image):
            uri = node.get("uri", "")
            alt = node.get("alt", uri)
            return f"![{alt}]({uri})"
        return None

    def _render_block_quote(self, node: nodes.block_quote, level: int) -> str:
        inner = [self._render_block(child, level) for child in node.children]
        inner_text = "\n".join(line for line in inner if line)
        return "\n".join(f"> {line}" if line else ">" for line in inner_text.splitlines())

    def _render_unknown_block(self, node: nodes.Node, level: int) -> str:
        if hasattr(node, "children"):
            return "\n".join(self._render_block(child, level) for child in node.children)
        return node.astext() if hasattr(node, "astext") else ""

    def _render_list_item(self, node: nodes.list_item, level: int, ordered: bool, index: int) -> str:
        prefix = f"{index}. " if ordered else "- "
        rendered_children = []
        for child in node.children:
            child_level = level + 1 if isinstance(child, nodes.section) else level
            rendered = self._render_block(child, child_level)
            if rendered:
                rendered_children.append(rendered)

        content = "\n".join(rendered_children).strip()
        if not content:
            return prefix.rstrip()

        lines = content.splitlines()
        first_line = lines[0]
        rest_lines = lines[1:]
        indent = "    "
        formatted_rest = []
        for line in rest_lines:
            if not line.strip():
                formatted_rest.append("")
            else:
                formatted_rest.append(f"{indent}{line}")

        return "\n".join([f"{prefix}{first_line}", *formatted_rest])

    def _render_definition_item(self, node: nodes.definition_list_item, level: int) -> str:
        term = next((child for child in node.children if isinstance(child, nodes.term)), None)
        classifiers = [child for child in node.children if isinstance(child, nodes.classifier)]
        definitions = [child for child in node.children if isinstance(child, nodes.definition)]
        header = self._render_inline_children(term) if term else ""
        if classifiers:
            header += f" ({', '.join(self._render_inline_children(c) for c in classifiers)})"
        body = "\n".join(self._render_block(defn, level) for defn in definitions)
        return "\n".join([f"**{header}**", body]).strip()

    def _render_table(self, table: nodes.table) -> str:
        header_rows, body_rows = self._table_rows(table)
        header_rows = self._ensure_table_header(header_rows, body_rows)
        lines: list[str] = []

        if header_rows:
            lines.extend(self._table_header_lines(header_rows[0]))

        lines.extend(self._table_row_line(row, len(header_rows[0]) if header_rows else None) for row in body_rows)

        return "\n".join(lines)

    def _table_rows(self, table: nodes.table) -> tuple[list[list[str]], list[list[str]]]:
        body_rows: list[list[str]] = []
        header_rows: list[list[str]] = []
        for tgroup in table.traverse(nodes.tgroup, include_self=True):
            for child in tgroup.children:
                if isinstance(child, nodes.thead):
                    header_rows.extend(self._extract_rows(child))
                elif isinstance(child, nodes.tbody):
                    body_rows.extend(self._extract_rows(child))
        return header_rows, body_rows

    @staticmethod
    def _ensure_table_header(header_rows: list[list[str]], body_rows: list[list[str]]) -> list[list[str]]:
        if header_rows or not body_rows:
            return header_rows
        if all(len(row) == 2 for row in body_rows):
            return [["Setting", "Details"]]
        return [[f"Column {i + 1}" for i in range(len(body_rows[0]))]]

    @staticmethod
    def _table_header_lines(header: list[str]) -> list[str]:
        separator = ["---"] * len(header)
        return [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |",
        ]

    @staticmethod
    def _table_row_line(row: list[str], width: int | None) -> str:
        if width is not None and len(row) < width:
            row = row + [""] * (width - len(row))
        return "| " + " | ".join(row) + " |"

    def _extract_rows(self, node: nodes.Node) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in node.traverse(nodes.row, include_self=False):
            cells: list[str] = []
            for entry in row.traverse(nodes.entry, include_self=False):
                cells.extend(self._render_table_entry(entry))
            if cells:
                rows.append(cells)
        return rows

    def _render_table_entry(self, entry: nodes.Node) -> list[str]:
        segments: list[str] = []
        meta_parts: list[str] = []
        description_parts: list[str] = []

        for child in entry.children:
            if isinstance(child, nodes.bullet_list):
                description_parts.extend(self._render_table_entry_descriptions(child))
                continue
            meta_text = self._render_table_entry_meta(child)
            if meta_text:
                meta_parts.append(meta_text)

        if meta_parts:
            segments.append("<br>".join(meta_parts))
        if description_parts:
            segments.append(" ".join(description_parts))

        if not segments:
            text = entry.astext().strip()
            return [text] if text else []

        return [segment.strip() for segment in segments if segment.strip()]

    def _render_table_entry_descriptions(self, child: nodes.bullet_list) -> list[str]:
        descriptions: list[str] = []
        for item in child.children:
            rendered = self._render_block(item, self.base_heading_level)
            if not rendered:
                continue
            item_text = self._strip_blockquote(rendered).strip()
            if item_text.startswith("- "):
                item_text = item_text[2:]
            descriptions.append(item_text.replace("\n", " "))
        return descriptions

    def _render_table_entry_meta(self, child: nodes.Node) -> str:
        rendered = self._render_block(child, self.base_heading_level)
        if not rendered:
            return ""
        return self._strip_blockquote(rendered).replace("\n", "<br>").strip()

    @staticmethod
    def _strip_blockquote(text: str) -> str:
        lines = [line.lstrip("> ") for line in text.splitlines()]
        return "\n".join(lines).strip()

    def _render_block_children(self, node: nodes.Node) -> str:
        chunks: list[str] = []
        for child in node.children:
            rendered = self._render_block(child, self.base_heading_level)
            if not rendered:
                continue
            cleaned_lines: list[str] = []
            for line in rendered.splitlines():
                stripped = line.lstrip("> ").rstrip()
                if stripped:
                    cleaned_lines.append(stripped)
            if cleaned_lines:
                chunks.append("\n".join(cleaned_lines))
        return "<br>".join(chunk.strip() for chunk in chunks if chunk.strip())

    # ------------------------------------------------------------------
    # Inline rendering helpers
    def _render_inline_children(self, node: nodes.Node) -> str:
        return "".join(self._render_inline(child) for child in node.children)

    def _render_inline(self, node: nodes.Node) -> str:
        if isinstance(node, nodes.Text):
            return node.astext()
        decorated = self._render_decorated_inline(node)
        if decorated is not None:
            return decorated
        if isinstance(node, nodes.reference):
            return self._render_reference_inline(node)
        if isinstance(node, nodes.image):
            return self._render_image_inline(node)
        if isinstance(node, nodes.math):
            return f"${node.astext()}$"
        if isinstance(node, nodes.problematic):
            return node.astext()
        if hasattr(node, "children"):
            return self._render_inline_children(node)
        return node.astext() if hasattr(node, "astext") else ""

    def _render_decorated_inline(self, node: nodes.Node) -> str | None:
        if isinstance(node, nodes.literal):
            return f"`{self._render_inline_children(node) or node.astext()}`"
        if isinstance(node, nodes.emphasis):
            return f"*{self._render_inline_children(node)}*"
        if isinstance(node, nodes.strong):
            return f"**{self._render_inline_children(node)}**"
        if isinstance(node, nodes.inline):
            return self._render_inline_children(node)
        if isinstance(node, nodes.subscript):
            return f"~{self._render_inline_children(node)}"
        if isinstance(node, nodes.superscript):
            return f"^{self._render_inline_children(node)}"
        return None

    def _render_reference_inline(self, node: nodes.reference) -> str:
        text = self._render_inline_children(node)
        refuri = node.get("refuri")
        if refuri:
            cleaned = _rewrite_refuri(refuri)
            return text if cleaned is None else f"[{text}]({cleaned})"
        refid = node.get("refid")
        return f"[{text}](#{refid})" if refid else text

    @staticmethod
    def _render_image_inline(node: nodes.image) -> str:
        uri = node.get("uri", "")
        alt = node.get("alt", uri)
        return f"![{alt}]({uri})"

    # ------------------------------------------------------------------
    @staticmethod
    def _heading(title: str, level: int) -> str:
        hashes = "#" * max(level, 1)
        return f"{hashes} {title.strip()}"

    @staticmethod
    def _cleanup(markdown: str) -> str:
        lines = markdown.splitlines()
        trimmed: list[str] = []
        prev_blank = True
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                trimmed.append(stripped)
                prev_blank = False
            else:
                if not prev_blank:
                    trimmed.append("")
                prev_blank = True
        text = "\n".join(trimmed).strip()
        # Ensure headings are separated by a blank line for readability.
        text = re.sub(r"(?<!\n\n)\n(#{1,6} )", r"\n\n\1", text)
        return text + "\n"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "section"


def extract_summary(markdown: str) -> str:
    in_code_block = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("- ", "* ", ">", "|", "`")):
            continue
        if stripped.endswith(":"):
            continue
        if stripped.startswith("[") and "]" in stripped and "Back to" in stripped:
            continue
        sentence = stripped.split(". ")[0].strip()
        if sentence and not sentence.endswith("."):
            sentence += "."
        return sentence
    return "Reference material."  # fallback


def has_body(markdown: str) -> bool:
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        return True
    return False


def convert_rst_file(source: Path, target_root: Path) -> DocumentChunks:
    _prepare_rst_environment()
    text = source.read_text(encoding="utf-8")
    sanitized = _strip_sphinx_roles(text)
    settings_overrides = {
        "report_level": 5,
        "halt_level": 6,
        "exit_status_level": 6,
        "warning_stream": io.StringIO(),
    }
    doctree = publish_doctree(
        sanitized,
        source_path=str(source),
        settings_overrides=settings_overrides,
    )

    title_node = next((child for child in doctree.children if isinstance(child, nodes.title)), None)
    document_title = title_node.astext().strip() if title_node else source.stem.replace("_", " ").title()

    sections = [child for child in doctree.children if isinstance(child, nodes.section)]
    intro_nodes = [child for child in doctree.children if child not in sections and not isinstance(child, nodes.title)]

    relative_dir = source.relative_to(source.parents[0]).with_suffix("")
    output_dir = target_root / relative_dir

    chunks: list[SectionChunk] = []

    renderer = MarkdownRenderer(base_heading_level=1)
    intro_content = renderer.render_nodes(intro_nodes, initial_heading=document_title)
    index_path = output_dir / "index.md"
    index_chunk = SectionChunk(
        title=document_title,
        relative_path=index_path.relative_to(target_root),
        content=intro_content,
        summary=extract_summary(intro_content),
    )
    chunks.append(index_chunk)

    existing_slugs: dict[str, int] = {}
    section_links: list[tuple[str, str]] = []
    for section in sections:
        title = section.next_node(nodes.title, include_self=False)
        if title is None:
            continue
        heading_text = title.astext().strip()
        slug = slugify(heading_text)
        count = existing_slugs.get(slug, 0)
        existing_slugs[slug] = count + 1
        if count:
            slug = f"{slug}-{count+1}"
        renderer = MarkdownRenderer(base_heading_level=1)
        content = renderer.render_nodes([section])
        section_path = output_dir / f"{slug}.md"
        navigation = f"[← Back to {document_title} index](index.md)\n\n"
        content_with_nav = navigation + content + "\n"
        chunks.append(
            SectionChunk(
                title=heading_text,
                relative_path=section_path.relative_to(target_root),
                content=content_with_nav,
                summary=extract_summary(content),
            )
        )
        section_links.append((heading_text, f"{slug}.md"))

    if section_links:
        if not has_body(index_chunk.content):
            title_list = ", ".join(title for title, _ in section_links[:3])
            summary_line = f"{document_title} covers {title_list}." if title_list else f"Overview of {document_title}."
            index_chunk.content = f"# {document_title}\n\n{summary_line}\n"
        sections_md = [index_chunk.content.rstrip(), "", "## Sections", ""]
        for title, filename in section_links:
            sections_md.append(f"- [{title}]({filename})")
        sections_md.append("")
        index_chunk.content = "\n".join(sections_md)
        index_chunk.summary = extract_summary(index_chunk.content)
    elif not has_body(index_chunk.content):
        index_chunk.content = f"# {document_title}\n\nOverview of {document_title}.\n"
        index_chunk.summary = extract_summary(index_chunk.content)

    return DocumentChunks(source_path=source, output_dir=output_dir, chunks=chunks)


def write_chunks(chunks: DocumentChunks, target_root: Path) -> None:
    for chunk in chunks.chunks:
        output_path = target_root / chunk.relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(chunk.content, encoding="utf-8")


def _llms_category_for_chunk(chunk: SectionChunk) -> str:
    parts = chunk.relative_path.parts
    base = parts[0] if parts else chunk.relative_path.stem
    return _LLMS_CATEGORY_OVERRIDES.get(base, "Guides")


def _group_llms_chunks(doc_chunks: Iterable[DocumentChunks]) -> dict[str, list[SectionChunk]]:
    sections: dict[str, list[SectionChunk]] = defaultdict(list)
    for doc in doc_chunks:
        for chunk in doc.chunks:
            sections[_llms_category_for_chunk(chunk)].append(chunk)
    return sections


def _ordered_llms_categories(sections: dict[str, list[SectionChunk]]) -> list[str]:
    ordered_categories = list(_LLMS_ORDERED_CATEGORIES)
    for cat in list(sections.keys()):
        if cat not in ordered_categories:
            ordered_categories.append(cat)
    return ordered_categories


def _hosted_link(path: str) -> str:
    return _HOSTED_DOCS_BASE.rstrip("/") + "/" + path.lstrip("/")


def _chunk_sort_key(chunk: SectionChunk, category: str) -> tuple[int, int, str]:
    preferred = _LLMS_PREFERRED_CATEGORY_POSITIONS.get(category, {})
    position = preferred.get(chunk.relative_path.as_posix())
    if position is not None:
        return (0, position, chunk.title.lower())
    is_index = 0 if chunk.relative_path.name == "index.md" else 1
    return (1, is_index, chunk.title.lower())


def _append_llms_section(lines: list[str], category: str, chunks: list[SectionChunk], seen_links: set[str]) -> None:
    if not chunks:
        return
    lines.extend([f"## {category}", ""])
    for chunk in sorted(chunks, key=lambda c: _chunk_sort_key(c, category)):
        link_path = chunk.relative_path.as_posix()
        if link_path in seen_links:
            continue
        seen_links.add(link_path)
        description = chunk.summary.rstrip(".") + "."
        lines.append(f"- [{chunk.title}]({_hosted_link(link_path)}): {description}")
    lines.append("")


def build_llms_index(doc_chunks: Iterable[DocumentChunks], target_path: Path) -> str:
    sections = _group_llms_chunks(doc_chunks)
    optional_chunks = sections.pop("Optional", [])
    lines = ["# flarchitect", "", f"> {_LLMS_SUMMARY}", "", "<!-- Generated by tools/convert_docs.py; do not edit manually. -->", ""]
    seen_links: set[str] = set()

    for category in _ordered_llms_categories(sections):
        _append_llms_section(lines, category, sections.get(category, []), seen_links)
    _append_llms_section(lines, "Optional", optional_chunks, seen_links)

    text = "\n".join(lines).rstrip() + "\n"
    target_path.write_text(text, encoding="utf-8")
    return text


def _create_llms_manifest_chunk(target_root: Path, llms_path: Path) -> DocumentChunks:
    summary = "Canonical llms.txt manifest for the flarchitect documentation set."
    relative_path = Path("llms.md")
    chunk = SectionChunk(
        title="llms.txt Manifest",
        relative_path=relative_path,
        content="",
        summary=summary,
    )
    return DocumentChunks(
        source_path=llms_path,
        output_dir=target_root,
        chunks=[chunk],
    )


def convert_all(source_dir: Path, target_dir: Path, llms_path: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    doc_chunks = [convert_rst_file(rst_file, target_dir) for rst_file in sorted(source_dir.rglob("*.rst"))]

    llms_manifest = _create_llms_manifest_chunk(target_dir, llms_path)
    doc_chunks.append(llms_manifest)

    llms_text = build_llms_index(doc_chunks, llms_path)
    manifest_chunk = llms_manifest.chunks[0]
    manifest_chunk.content = llms_text

    for chunks in doc_chunks:
        write_chunks(chunks, target_dir)

    extra_manifest_path = PROJECT_ROOT / "docs" / "source" / "_extra" / "llms.md"
    extra_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    extra_manifest_path.write_text(llms_text, encoding="utf-8")



def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert RST docs to Markdown and generate llms.txt")
    parser.add_argument("--source", type=Path, default=PROJECT_ROOT / "docs" / "source")
    parser.add_argument("--target", type=Path, default=PROJECT_ROOT / "docs" / "md")
    parser.add_argument("--llms", type=Path, default=PROJECT_ROOT / "llms.txt")
    args = parser.parse_args(argv)

    convert_all(args.source.resolve(), args.target.resolve(), args.llms.resolve())


if __name__ == "__main__":
    main()
