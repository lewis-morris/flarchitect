"""Documentation indexing utilities for the MCP server."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, Optional, Sequence


_HEADING_CHARS = r"=-`:'\"^_*+#~<>"


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
        roots: Iterable[Path],
        *,
        include_extensions: Iterable[str] = (".md", ".rst", ".txt"),
        aliases: Optional[Mapping[Path | str, str]] = None,
        extra_files: Optional[Mapping[Path | str, str | None]] = None,
    ) -> None:
        self._roots: tuple[Path, ...] = tuple(sorted(Path(root).resolve() for root in roots))
        if not self._roots:
            raise ValueError("DocumentIndex requires at least one root directory")

        alias_input = aliases or {}
        alias_map: dict[Path, str] = {
            Path(key).resolve(): value.strip("/")
            for key, value in alias_input.items()
        }
        self._aliases = {root: alias_map.get(root, "") for root in self._roots}

        self._include_extensions = tuple(sorted(ext.lower() for ext in include_extensions))
        self._extra_files = {
            Path(path).resolve(): (alias.strip("/") if alias else None)
            for path, alias in (extra_files or {}).items()
        }
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

        for path, alias in self._extra_files.items():
            if not path.exists():  # pragma: no cover - defensive guard
                continue
            doc_id = (alias or path.name).replace("\\", "/")
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

        pattern = re.compile(re.escape(query), flags=re.IGNORECASE)
        results: list[SearchHit] = []
        for record in self._documents.values():
            lines = record.content.splitlines()
            for line_number, line in enumerate(lines, start=1):
                if pattern.search(line):
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
                    if len(results) >= limit:
                        return results
        return results

    def _iter_document_paths(self) -> Iterator[tuple[Path, Path]]:
        for root in self._roots:
            if not root.exists():
                continue
            if root.is_file():
                if root.suffix.lower() in self._include_extensions:
                    yield root.parent, root
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in self._include_extensions:
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
    content = path.read_text(encoding="utf-8")
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
