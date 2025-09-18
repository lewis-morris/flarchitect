"""Documentation indexing utilities for the MCP server."""

from __future__ import annotations

import io
import functools
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Mapping, Optional, Sequence

from docutils import nodes
from docutils.core import publish_parts
from docutils.parsers.rst import Directive, directives, roles
from docutils.utils import SystemMessage


_HEADING_CHARS = r"=-`:'\"^_*+#~<>"
_EXCLUDED_FILENAMES = {"README.md", "SUGGESTIONS.md"}
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "crud": ("create", "read", "update", "delete"),
    "filters": ("filter", "filtering"),
    "serialization": ("serialisation", "serialize", "serialise"),
    "roles": ("role", "rbac"),
    "callbacks": ("callback", "hook", "hooks"),
}


@dataclass(frozen=True)
class DocumentSection:
    """A logical section within a documentation file."""

    title: str
    anchor: str
    start_line: int
    end_line: Optional[int]


@dataclass(frozen=True)
class DocumentRecord:
    """A single documentation file with metadata used by the MCP server."""

    doc_id: str
    path: Path
    title: str
    sections: Sequence[DocumentSection]
    content: str


@dataclass(frozen=True)
class SearchHit:
    """A single search result returned by :class:`DocumentIndex`."""

    doc_id: str
    path: Path
    line_number: int
    heading: Optional[str]
    snippet: str


class DocumentIndex:
    """Indexes project documentation directories for quick lookup and search."""

    def __init__(
        self,
        roots_or_project: Iterable[Path] | Path,
        *,
        doc_path: Path | None = None,
        include_extensions: Iterable[str] = (".md", ".rst", ".txt"),
        aliases: Optional[Mapping[Path | str, str]] = None,
        extra_files: Optional[Mapping[Path | str, str | None]] = None,
    ) -> None:
        if isinstance(roots_or_project, Path):
            project_root = roots_or_project.resolve()
            default_doc_path = doc_path.resolve() if doc_path is not None else (project_root / "docs" / "source")
            self._roots = (default_doc_path,)
            alias_value = None
            if aliases is not None:
                alias_input = aliases
            else:
                alias_value = _default_alias(default_doc_path)
                alias_input = {default_doc_path: alias_value} if alias_value is not None else {default_doc_path: ""}
        else:
            resolved_roots = tuple(sorted(Path(root).resolve() for root in roots_or_project))
            if not resolved_roots:
                raise ValueError("DocumentIndex requires at least one root directory")
            self._roots = resolved_roots
            alias_input = aliases or {}
        if not self._roots:
            raise ValueError("DocumentIndex requires at least one root directory")

        missing_roots = [root for root in self._roots if not root.exists()]
        if missing_roots:
            missing_str = ", ".join(str(root) for root in missing_roots)
            raise FileNotFoundError(f"Documentation root(s) not found: {missing_str}")

        alias_map: dict[Path, str] = {}
        for key, value in alias_input.items():
            resolved = Path(key).resolve()
            alias_map[resolved] = value.strip("/") if value else ""
        self._aliases = {root: alias_map.get(root, "") for root in self._roots}

        self._include_extensions = tuple(sorted(ext.lower() for ext in include_extensions))
        self._extra_files: dict[Path, str | None] = {}
        if extra_files:
            for file_path, doc_id in extra_files.items():
                resolved = Path(file_path).resolve()
                self._extra_files[resolved] = doc_id
        self._documents: dict[str, DocumentRecord] = {}
        self.refresh()

    @property
    def roots(self) -> tuple[Path, ...]:
        return self._roots

    def refresh(self) -> None:
        """Refresh the cached representation of all documentation files."""

        documents: dict[str, DocumentRecord] = {}
        for root, path in self._iter_document_paths():
            doc_id = self._doc_id_for_path(root=root, path=path)
            documents[doc_id] = _build_record(doc_id, path)

        for path, explicit_id in self._extra_files.items():
            if not path.exists() or path.suffix.lower() not in self._include_extensions:
                continue
            doc_id = explicit_id or path.name
            documents[doc_id] = _build_record(doc_id, path)

        self._documents = documents

    def list_documents(self) -> list[DocumentRecord]:
        """Return all indexed documents sorted by their document id."""

        return [self._documents[key] for key in sorted(self._documents.keys())]

    def get(self, doc_id: str) -> DocumentRecord:
        try:
            return self._documents[doc_id]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"Unknown document id: {doc_id}") from exc

    def get_section(self, doc_id: str, heading: Optional[str]) -> str:
        record = self.get(doc_id)
        if heading is None:
            return record.content

        normalized = _normalize_anchor(heading)
        lines = record.content.splitlines()
        for section in record.sections:
            if section.anchor == normalized:
                end_line = section.end_line or len(lines)
                snippet_lines = lines[section.start_line - 1 : end_line]
                snippet_lines = _strip_heading(snippet_lines)
                return "\n".join(snippet_lines).strip()

        raise KeyError(
            f"Heading '{heading}' not found in document '{doc_id}'."
        )

    def search(self, query: str, *, limit: int = 20) -> list[SearchHit]:
        """Perform a simple case-insensitive search across all documents."""

        if not query.strip():
            return []

        results: list[SearchHit] = []
        seen: set[tuple[str, int]] = set()
        for term in self._expand_terms(query):
            pattern = re.compile(re.escape(term), flags=re.IGNORECASE)
            for record in self._documents.values():
                lines = record.content.splitlines()
                for line_number, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        key = (record.doc_id, line_number)
                        if key in seen:
                            continue
                        heading = _heading_for_line(record.sections, line_number)
                        snippet = line.strip()
                        results.append(
                            SearchHit(
                                doc_id=record.doc_id,
                                path=record.path,
                                line_number=line_number,
                                heading=heading,
                                snippet=snippet,
                            )
                        )
                        seen.add(key)
                        if len(results) >= limit:
                            return results
        return results

    def _expand_terms(self, query: str) -> list[str]:
        base_terms: list[str] = []
        for term in [query, *re.split(r"\s+", query)]:
            cleaned = term.strip()
            if not cleaned:
                continue
            base_terms.append(cleaned)
            synonyms = _SYNONYMS.get(cleaned.lower())
            if synonyms:
                base_terms.extend(synonyms)
        seen: dict[str, None] = {}
        for term in base_terms:
            if term not in seen:
                seen[term] = None
        return list(seen.keys())

    def _iter_document_paths(self) -> Iterator[tuple[Path, Path]]:
        for root in self._roots:
            if not root.exists():
                continue
            if root.is_file():
                if root.suffix.lower() in self._include_extensions:
                    yield root.parent, root
                continue
            for path in root.rglob("*"):
                if (
                    path.is_file()
                    and path.suffix.lower() in self._include_extensions
                    and not path.name.startswith(".")
                    and path.name not in _EXCLUDED_FILENAMES
                ):
                    yield root, path.resolve()

    def _doc_id_for_path(self, *, root: Path, path: Path) -> str:
        try:
            relative = path.relative_to(root)
        except ValueError:  # pragma: no cover - defensive guard
            relative = path.name
        alias = self._aliases.get(root, "")
        if alias:
            doc_path = Path(alias) / relative
        else:
            doc_path = relative
        return doc_path.as_posix()


def _build_record(doc_id: str, path: Path) -> DocumentRecord:
    raw_content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".rst":
        title, content, sections = _parse_rst_document(raw_content, path)
        if not sections:
            sections = list(_extract_sections(content))
    else:
        content = raw_content
        sections = list(_extract_sections(content))
        title = sections[0].title if sections else path.stem.replace("_", " ").title()
    return DocumentRecord(
        doc_id=doc_id,
        path=path,
        title=title,
        sections=sections,
        content=content,
    )


def _extract_sections(content: str) -> Iterator[DocumentSection]:
    lines = content.splitlines()
    index = 0
    last_section: Optional[DocumentSection] = None
    while index < len(lines):
        header = _parse_heading(lines, index)
        if header is not None:
            title, skip = header
            anchor = _normalize_anchor(title)
            section = DocumentSection(
                title=title.strip(),
                anchor=anchor,
                start_line=index + 1,
                end_line=None,
            )
            if last_section is not None:
                object.__setattr__(last_section, "end_line", index)
            last_section = section
            yield section
            index += skip
            continue
        index += 1

    if last_section is not None and last_section.end_line is None:
        object.__setattr__(last_section, "end_line", len(lines))


def _parse_heading(lines: List[str], index: int) -> Optional[tuple[str, int]]:
    line = lines[index].rstrip()
    if not line.strip():
        return None

    # Markdown style heading
    if line.lstrip().startswith("#"):
        level = len(line) - len(line.lstrip("#"))
        if level == 0:
            return None
        title = line.lstrip("#").strip()
        return title, 1

    # reStructuredText style with underline after the title
    if index + 1 < len(lines):
        underline = lines[index + 1]
        stripped = underline.strip()
        if stripped and all(char == stripped[0] for char in stripped):
            if len(stripped) >= len(line.strip()) and stripped[0] in _HEADING_CHARS:
                title = line.strip()
                return title, 2

    return None


class _RSTHTMLToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._lines: list[str] = []
        self._buffer: list[str] = []
        self._heading_buffer: list[str] | None = None
        self.sections: list[DocumentSection] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        tag = tag.lower()
        if tag in {"p", "div", "section", "ul", "ol", "li"}:
            self._flush_buffer()
        if tag == "br":
            self._flush_buffer()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_buffer()
            self._heading_buffer = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            if self._heading_buffer is not None:
                title = " ".join(self._heading_buffer).strip()
                self._heading_buffer = None
                if title:
                    self._append_line(title)
                    start_line = len(self._lines)
                    section = DocumentSection(
                        title=title,
                        anchor=_normalize_anchor(title),
                        start_line=start_line,
                        end_line=None,
                    )
                    if self.sections:
                        last = self.sections[-1]
                        if last.end_line is None:
                            object.__setattr__(last, "end_line", start_line - 1)
                    self.sections.append(section)
            self._buffer = []
        elif tag in {"p", "div", "section", "li", "ul", "ol", "br"}:
            self._flush_buffer()

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        text = data.strip()
        if not text:
            return
        if self._heading_buffer is not None:
            self._heading_buffer.append(text)
        self._buffer.append(text)

    def get_text(self) -> str:
        self._flush_buffer()
        if self.sections and self.sections[-1].end_line is None:
            object.__setattr__(self.sections[-1], "end_line", len(self._lines))
        return "\n".join(self._lines)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        line = " ".join(self._buffer).strip()
        self._buffer.clear()
        if not line:
            return
        self._lines.append(line)

    def _append_line(self, line: str) -> None:
        if line:
            self._lines.append(line)


def _parse_rst_document(source: str, path: Path) -> tuple[str, str, list[DocumentSection]]:
    _prepare_rst_environment()
    sanitized_source = _strip_sphinx_roles(source)
    try:
        warning_buffer = io.StringIO()
        parts = publish_parts(
            source=sanitized_source,
            source_path=str(path),
            writer_name="html",
            settings_overrides={
                "report_level": 5,
                "halt_level": 6,
                "exit_status_level": 6,
                "warning_stream": warning_buffer,
            },
        )
        title = parts.get("title")
        body = parts.get("body", "")
    except (SystemMessage, ImportError):
        sections = list(_extract_sections(sanitized_source))
        title = sections[0].title if sections else path.stem.replace("_", " ").title()
        return title, sanitized_source, sections

    parser = _RSTHTMLToTextParser()
    parser.feed(body)
    body_text = parser.get_text()
    parsed_sections = parser.sections

    resolved_title = (title or "").strip() or path.stem.replace("_", " ").title()

    body_lines = body_text.splitlines()
    if resolved_title:
        lines = [resolved_title, *body_lines]
        sections: list[DocumentSection] = []
        title_section = DocumentSection(
            title=resolved_title,
            anchor=_normalize_anchor(resolved_title),
            start_line=1,
            end_line=None,
        )
        adjusted_sections: list[DocumentSection] = []
        for sec in parsed_sections:
            adjusted_sections.append(
                DocumentSection(
                    title=sec.title,
                    anchor=sec.anchor,
                    start_line=sec.start_line + 1,
                    end_line=(sec.end_line + 1) if sec.end_line is not None else None,
                )
            )
        if adjusted_sections:
            object.__setattr__(title_section, "end_line", adjusted_sections[0].start_line - 1)
            if adjusted_sections[-1].end_line is None:
                object.__setattr__(adjusted_sections[-1], "end_line", len(lines))
        else:
            object.__setattr__(title_section, "end_line", len(lines))
        sections = [title_section, *adjusted_sections]
    else:
        lines = body_lines
        sections = [
            DocumentSection(
                title=sec.title,
                anchor=sec.anchor,
                start_line=sec.start_line,
                end_line=sec.end_line,
            )
            for sec in parsed_sections
        ]
        if sections and sections[-1].end_line is None:
            object.__setattr__(sections[-1], "end_line", len(lines))

    plain_text = "\n".join(line for line in lines if line).strip()
    if not sections:
        sections = list(_extract_sections(plain_text))
    return resolved_title, plain_text, sections


def _strip_sphinx_roles(source: str) -> str:
    # Remove interpreted text roles such as ``:bdg:`value``` to leave only the payload.
    source = re.sub(r"\:([\w.+-]+)\:`([^`]+)`", r"\2", source)
    # Replace Sphinx-style references ``Foo`_``/``Foo`__`` with plain text.
    source = re.sub(r"`([^`]+)`__?", r"\1", source)
    return source


@functools.lru_cache(maxsize=1)
def _prepare_rst_environment() -> None:
    class _PassthroughDirective(Directive):
        has_content = True
        optional_arguments = 1
        final_argument_whitespace = True
        option_spec: dict[str, Callable[[str], str]] = {}

        def run(self):
            container = nodes.container()
            if self.content:
                self.state.nested_parse(self.content, self.content_offset, container)
            return list(container.children)

    class _IgnoreDirective(Directive):
        has_content = True
        optional_arguments = 0

        def run(self):
            return []

    class _LiteralIncludeDirective(Directive):
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = False
        has_content = False
        option_spec = {
            "language": directives.unchanged,
            "linenos": directives.flag,
        }

        def run(self):
            argument = self.arguments[0]
            language = self.options.get("language")
            show_linenos = "linenos" in self.options

            settings = self.state.document.settings
            source_candidate = (
                getattr(settings, "_source", None)
                or getattr(settings, "_source_path", None)
                or self.state.document.current_source
            )
            base_path = Path(source_candidate or ".").resolve().parent
            include_path = (base_path / argument).resolve()
            try:
                text = include_path.read_text(encoding="utf-8")
            except OSError:
                text = ""
            literal = nodes.literal_block(text, text)
            if language:
                literal["language"] = language
            if show_linenos:
                literal["linenos"] = True
            return [literal]

    directives.register_directive("dropdown", _PassthroughDirective)
    directives.register_directive("tab-set", _PassthroughDirective)
    directives.register_directive("tab-item", _PassthroughDirective)
    directives.register_directive("toctree", _IgnoreDirective)
    directives.register_directive("literalinclude", _LiteralIncludeDirective)

    def _noop_role(role_name, rawtext, text, lineno, inliner, options=None, content=None):
        return [nodes.Text(text)], []

    for role_name in (
        "bdg",
        "bdg-dark-line",
        "bdg-danger",
        "bdg-secondary",
        "ref",
        "doc",
        "class",
        "mod",
        "func",
        "meth",
        "data",
        "program",
    ):
        roles.register_local_role(role_name, _noop_role)


def _normalize_anchor(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "-", value.strip().lower()).strip("-")
    return normalized or "section"


def _strip_heading(lines: list[str]) -> list[str]:
    if not lines:
        return lines

    first = lines[0].lstrip()
    if first.startswith("#"):
        return lines[1:]

    if len(lines) >= 2:
        underline = lines[1].strip()
        if underline and all(char == underline[0] for char in underline):
            if underline[0] in _HEADING_CHARS:
                return lines[2:]
    return lines


def _heading_for_line(sections: Sequence[DocumentSection], line_number: int) -> Optional[str]:
    match = None
    for section in sections:
        if section.start_line <= line_number and (
            section.end_line is None or line_number <= section.end_line
        ):
            match = section.title
        elif section.start_line > line_number:
            break
    return match


def _default_alias(path: Path) -> str | None:
    parts = path.parts
    if len(parts) >= 2 and parts[-2] == "docs" and parts[-1] == "md":
        return "docs/md"
    if len(parts) >= 2 and parts[-2] == "docs" and parts[-1] == "source":
        return "docs/source"
    return path.name if path.name else None
