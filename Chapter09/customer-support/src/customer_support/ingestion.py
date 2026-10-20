__all__ = ["SyncReport", "chunk_document", "read_sources", "sync"]


import hashlib
from pathlib import Path

from loguru import logger
from pydantic import BaseModel
from semantic_text_splitter import MarkdownSplitter

from .config import KnowledgeSettings
from .knowledge import Document, KnowledgeRepository


class SyncReport(BaseModel):
    """What one sync changed, as lists of source paths."""

    added: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    removed: list[str] = []


def read_sources(source_dir: Path) -> dict[str, str]:
    """Read every Markdown file under `source_dir`.

    Args:
        source_dir (Path): Folder holding the knowledge documents.

    Returns:
        dict[str, str]: Text of each file, keyed by relative path.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"No folder at {source_dir}")
    paths = sorted(source_dir.rglob("*.md"))
    if not paths:
        raise ValueError(f"No Markdown files in {source_dir}")
    return {
        path.relative_to(source_dir).as_posix(): path.read_text(
            encoding="utf-8"
        )
        for path in paths
    }


def chunk_document(
    source: str, text: str, splitter: MarkdownSplitter
) -> list[Document]:
    """Split one document into chunks with stable, numbered IDs.

    Args:
        source (str): Relative path of the document.
        text (str): Full Markdown text of the document.
        splitter (MarkdownSplitter): Splitter with chunk settings.

    Returns:
        list[Document]: Chunks, with IDs such as `faq/a.md#0`.
    """
    chunks = splitter.chunks(text)
    if not chunks:
        raise ValueError(f"{source} has no text to index")
    return [
        Document(id=f"{source}#{n}", text=chunk, source=source)
        for n, chunk in enumerate(chunks)
    ]


def fingerprint(text: str, settings: KnowledgeSettings) -> str:
    """Hash a document together with the settings that chunk it.

    Args:
        text (str): Full Markdown text of the document.
        settings (KnowledgeSettings): Chunk size and overlap used.

    Returns:
        str: Hex digest that changes when text or settings change.
    """
    data = (
        f"{settings.chunk_size}:{settings.chunk_overlap}:{text}"
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sync(
    settings: KnowledgeSettings, repository: KnowledgeRepository
) -> SyncReport:
    """Make the repository match the Markdown files on disk.

    Args:
        settings (KnowledgeSettings): Source folder and chunking.
        repository (KnowledgeRepository): Collection to update.

    Returns:
        SyncReport: Sources added, updated, unchanged and removed.
    """
    texts = read_sources(settings.source_dir)
    splitter = MarkdownSplitter(
        settings.chunk_size, settings.chunk_overlap
    )
    chunks = {
        source: chunk_document(source, text, splitter)
        for source, text in texts.items()
    }
    stored = repository.sources()
    report = SyncReport()
    for source, text in texts.items():
        digest = fingerprint(text, settings)
        if repository.stored_fingerprint(source) == digest:
            report.unchanged.append(source)
            continue
        if source in stored:
            report.updated.append(source)
        else:
            report.added.append(source)
        repository.replace_source(source, chunks[source], digest)
    for source in sorted(stored - texts.keys()):
        repository.delete_source(source)
        report.removed.append(source)
    logger.info("Knowledge base synced: {}", report)
    return report
