"""Input ingestion: procedure documents, process-map images, code trees.

Produces plain-text bundles with source tags so every downstream finding
can carry an evidence quote traceable to a specific input file.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".json", ".yaml", ".yml"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
CODE_EXT = {
    ".py", ".java", ".js", ".ts", ".cs", ".go", ".sql", ".xml", ".bpmn",
    ".yaml", ".yml", ".json", ".properties", ".kt", ".groovy",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "build", "dist"}


@dataclass
class IngestBundle:
    documents: list[tuple[str, str]] = field(default_factory=list)  # (source, text)
    images: list[str] = field(default_factory=list)                 # process-map paths
    code_snapshot: str = ""                                         # trimmed code tree digest

    def document_block(self, max_chars_per_doc: int = 120_000) -> str:
        parts = []
        for source, text in self.documents:
            parts.append(f"===== SOURCE: {source} =====\n{text[:max_chars_per_doc]}")
        return "\n\n".join(parts) if parts else "(no procedure documents supplied)"


def read_document(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXT:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if ext == ".docx":
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"unsupported document type: {path}")


def snapshot_code_tree(root: str, max_files: int = 200, max_chars_per_file: int = 4000) -> str:
    """Compact digest of a code directory for the code-level audit pass.

    Includes the file tree and trimmed contents of source files, skipping
    dependencies and build output. The LLM looks for hardcoded policy,
    point-to-point integration fragility and manual-step markers.
    """
    lines: list[str] = []
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext not in CODE_EXT:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if seen >= max_files:
                lines.append(f"... truncated at {max_files} files ...")
                return "\n".join(lines)
            seen += 1
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    content = fh.read(max_chars_per_file)
            except OSError:
                continue
            lines.append(f"----- FILE: {rel} -----\n{content}")
    return "\n\n".join(lines)


def build_bundle(
    procedures: list[str] | None = None,
    process_maps: list[str] | None = None,
    code_dir: str | None = None,
    max_code_files: int = 200,
) -> IngestBundle:
    bundle = IngestBundle()
    for path in procedures or []:
        bundle.documents.append((os.path.basename(path), read_document(path)))
    for path in process_maps or []:
        ext = os.path.splitext(path)[1].lower()
        if ext not in IMAGE_EXT:
            raise ValueError(f"process map must be an image ({sorted(IMAGE_EXT)}): {path}")
        bundle.images.append(path)
    if code_dir:
        bundle.code_snapshot = snapshot_code_tree(code_dir, max_files=max_code_files)
    return bundle
