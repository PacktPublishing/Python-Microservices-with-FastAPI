from pathlib import Path

from loguru import logger
from pydantic import TypeAdapter

from .knowledge import Document, KnowledgeRepository


def load_documents(path: Path) -> list[Document]:
    """Validate all passages before allowing an import.

    Args:
        path (Path): UTF-8 JSON file containing Document records.

    Returns:
        list[Document]: Validated passages with unique, nonblank IDs.
    """
    documents = TypeAdapter(list[Document]).validate_json(
        path.read_text(encoding="utf-8")
    )
    seen: set[str] = set()
    for document in documents:
        fields = (document.id, document.text, document.source)
        if not all(value.strip() for value in fields):
            raise ValueError("Blank document field.")
        if document.id in seen:
            raise ValueError(f"Duplicate ID: {document.id}")
        seen.add(document.id)
    logger.debug(
        "Validated {} passages from {}", len(documents), path
    )
    return documents


def ingest(path: Path, repository: KnowledgeRepository) -> int:
    """Validate and upsert the file without deleting existing records.

    Args:
        path (Path): UTF-8 JSON source to import.
        repository (KnowledgeRepository): Destination collection.

    Returns:
        int: Number of submitted records, including updates.
    """
    documents = load_documents(path)
    repository.add(documents)
    logger.info(
        "Imported {} passages from {}", len(documents), path
    )
    return len(documents)
