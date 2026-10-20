__all__ = ["SyncReport", "chunk_document", "read_sources", "sync"]


import hashlib
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from loguru import logger
from pydantic import BaseModel
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition

from .config import KnowledgeSettings
from .knowledge import Document, KnowledgeRepository


class SyncReport(BaseModel):
    """What one sync changed, as lists of source paths."""

    added: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    removed: list[str] = []


def read_sources(source_dir: Path) -> dict[str, Path]:
    """Find every document under `source_dir`, whatever its format.

    Hidden files and folders, such as `.DS_Store` or `.git`, are
    skipped. `exclude_hidden` is turned off because it checks every
    part of the absolute path, so it would skip everything when the
    project itself lives inside a hidden folder; the `exclude`
    patterns only look below `source_dir`.

    Args:
        source_dir (Path): Folder holding the knowledge documents.

    Returns:
        dict[str, Path]: Path of each file, keyed by relative path.
    """
    root = source_dir.resolve()
    reader = SimpleDirectoryReader(
        input_dir=root,
        recursive=True,
        exclude_hidden=False,
        exclude=["**/.*", "**/.*/**"],
    )
    return {
        Path(path).relative_to(root).as_posix(): Path(path)
        for path in reader.input_files
    }


def chunk_document(
    source: str, path: Path, settings: KnowledgeSettings
) -> list[Document]:
    """Parse one file and split it into chunks with numbered IDs.

    Args:
        source (str): Relative path of the document.
        path (Path): Location of the file on disk.
        settings (KnowledgeSettings): Chunk size and overlap.

    Returns:
        list[Document]: Chunks, with IDs such as `faq/a.md#0`.
    """
    chunks = chunk_by_title(
        partition(filename=str(path)),
        max_characters=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    if not chunks:
        raise ValueError(f"{source} has no text to index")
    return [
        Document(
            id=f"{source}#{n}",
            text=chunk.text,
            source=source,
        )
        for n, chunk in enumerate(chunks)
    ]


def fingerprint(path: Path, settings: KnowledgeSettings) -> str:
    """Hash a file together with the settings that chunk it.

    Args:
        path (Path): File whose bytes are hashed.
        settings (KnowledgeSettings): Chunk size and overlap used.

    Returns:
        str: Hex digest that changes when file or settings change.
    """
    digest = hashlib.sha256(path.read_bytes())
    sizes = f"{settings.chunk_size}:{settings.chunk_overlap}"
    digest.update(sizes.encode())
    return digest.hexdigest()


def sync(
    settings: KnowledgeSettings, repository: KnowledgeRepository
) -> SyncReport:
    """Make the repository match the documents on disk.

    Args:
        settings (KnowledgeSettings): Source folder and chunking.
        repository (KnowledgeRepository): Collection to update.

    Returns:
        SyncReport: Sources added, updated, unchanged and removed.
    """
    paths = read_sources(settings.source_dir)
    digests = {
        source: fingerprint(path, settings)
        for source, path in paths.items()
    }
    changed = [
        source
        for source, digest in digests.items()
        if repository.stored_fingerprint(source) != digest
    ]
    chunks = {
        source: chunk_document(source, paths[source], settings)
        for source in changed
    }
    stored = repository.sources()
    report = SyncReport(
        unchanged=[s for s in paths if s not in chunks]
    )
    for source, documents in chunks.items():
        if source in stored:
            report.updated.append(source)
        else:
            report.added.append(source)
        repository.replace_source(
            source, documents, digests[source]
        )
    for source in sorted(stored - paths.keys()):
        repository.delete_source(source)
        report.removed.append(source)
    logger.info("Knowledge base synced: {}", report)
    return report
