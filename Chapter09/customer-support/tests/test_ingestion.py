from pathlib import Path

import pytest
from pydantic import TypeAdapter

from customer_support.ingestion import (
    ingest,
    load_documents,
)
from customer_support.knowledge import (
    Document,
    KnowledgeRepository,
)


def test_load_documents(
    knowledge_file: Path, source_documents: list[Document]
) -> None:
    """Check that JSON loading preserves IDs, text and sources."""
    assert load_documents(knowledge_file) == source_documents, (
        "Loading must preserve every passage and its source."
    )


def test_ingest_twice(
    knowledge_file: Path,
    source_documents: list[Document],
    repository: KnowledgeRepository,
    retrieval_query: str,
) -> None:
    """Import twice and verify one stored record per stable ID."""
    count = ingest(knowledge_file, repository)
    assert count == len(source_documents), (
        "Report submitted records."
    )
    ingest(knowledge_file, repository)
    results = repository.search(
        retrieval_query, limit=len(source_documents) + 1
    )
    assert sorted(results, key=lambda doc: doc.id) == sorted(
        source_documents, key=lambda doc: doc.id
    ), "Repeated imports must not duplicate or change passages."


def test_ingest_updated_text(
    knowledge_file: Path,
    updated_documents: list[Document],
    repository: KnowledgeRepository,
    retrieval_query: str,
) -> None:
    """Reimport changed text and retrieve the replacement passage."""
    ingest(knowledge_file, repository)
    knowledge_file.write_bytes(
        TypeAdapter(list[Document]).dump_json(updated_documents)
    )
    ingest(knowledge_file, repository)
    results = repository.search(
        retrieval_query, limit=len(updated_documents)
    )
    assert sorted(results, key=lambda doc: doc.id) == sorted(
        updated_documents, key=lambda doc: doc.id
    ), (
        "A stable ID must replace old text and preserve other records."
    )


def test_invalid_input_does_not_write(
    invalid_knowledge_file: Path,
    repository: KnowledgeRepository,
    retrieval_query: str,
) -> None:
    """Reject invalid input before writing any records."""
    with pytest.raises(ValueError):
        ingest(invalid_knowledge_file, repository)
    assert not repository.search(retrieval_query), (
        "Invalid input must leave the collection empty."
    )


def test_duplicate_ids_do_not_write(
    duplicate_knowledge_file: Path,
    repository: KnowledgeRepository,
    retrieval_query: str,
) -> None:
    """Reject duplicate IDs before any valid records are stored."""
    with pytest.raises(ValueError):
        ingest(duplicate_knowledge_file, repository)
    assert not repository.search(retrieval_query), (
        "A duplicate late in the file must not cause a partial import."
    )


def test_empty_input(
    empty_knowledge_file: Path,
    repository: KnowledgeRepository,
    retrieval_query: str,
) -> None:
    """Allow an empty array without writing any passage."""
    assert not load_documents(empty_knowledge_file), (
        "Load no records."
    )
    assert not ingest(empty_knowledge_file, repository), (
        "An empty import must report no submitted records."
    )
    assert not repository.search(retrieval_query), (
        "An empty import must leave the collection empty."
    )


def test_missing_input(missing_knowledge_file: Path) -> None:
    """Surface missing files instead of treating them as empty."""
    with pytest.raises(FileNotFoundError):
        load_documents(missing_knowledge_file)


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
