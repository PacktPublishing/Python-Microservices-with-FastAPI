from pathlib import Path

import pytest
from pydantic import ValidationError
from unstructured.partition.common import (
    UnsupportedFileFormatError,
)

from customer_support.config import KnowledgeSettings
from customer_support.ingestion import chunk_document, sync
from customer_support.knowledge import KnowledgeRepository


def test_first_sync_adds_every_file(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
    cancellation_source: str,
    retrieval_query: str,
) -> None:
    """Sync into an empty store and retrieve the right document."""
    report = sync(knowledge_settings, repository)
    assert report.added == sample_sources, (
        "Every Markdown file must be reported as added."
    )
    assert repository.sources() == set(sample_sources), (
        "Every Markdown file must be stored."
    )
    best = repository.search(retrieval_query, limit=1)[0]
    assert best.source == cancellation_source, (
        "The cancellation question must find the policy."
    )


def test_second_sync_skips_unchanged_files(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
) -> None:
    """Re-run the sync without edits and expect no work at all."""
    sync(knowledge_settings, repository)
    report = sync(knowledge_settings, repository)
    assert report.unchanged == sample_sources, (
        "Files whose fingerprint matches must be skipped."
    )
    assert not report.added + report.updated + report.removed, (
        "Nothing may be added, updated or removed."
    )


def test_edited_file_replaces_its_chunks(
    small_chunk_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    source_dir: Path,
    cancellation_source: str,
    retrieval_query: str,
    new_policy_text: str,
) -> None:
    """Edit one file and check only its new text is retrievable."""
    sync(small_chunk_settings, repository)
    edited = source_dir / cancellation_source
    edited.write_text(new_policy_text, encoding="utf-8")
    report = sync(small_chunk_settings, repository)
    assert report.updated == [cancellation_source], (
        "Only the edited file must be reported as updated."
    )
    texts = [
        doc.text
        for doc in repository.search(retrieval_query, limit=100)
        if doc.source == cancellation_source
    ]
    assert texts == [new_policy_text], (
        "The old chunks of an edited file must be deleted."
    )


def test_deleted_file_is_removed(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    source_dir: Path,
    payments_source: str,
) -> None:
    """Delete one file and check its chunks leave the store."""
    sync(knowledge_settings, repository)
    (source_dir / payments_source).unlink()
    report = sync(knowledge_settings, repository)
    assert report.removed == [payments_source], (
        "The deleted file must be reported as removed."
    )
    assert payments_source not in repository.sources(), (
        "The deleted file must not be stored anymore."
    )


def test_chunk_settings_change_rechunks(
    knowledge_settings: KnowledgeSettings,
    small_chunk_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
) -> None:
    """Change the chunk size and expect every file re-chunked."""
    sync(knowledge_settings, repository)
    report = sync(small_chunk_settings, repository)
    assert report.updated == sample_sources, (
        "Chunking settings are part of the fingerprint."
    )


def test_chunks_respect_size_and_ids(
    small_chunk_settings: KnowledgeSettings,
    source_dir: Path,
    cancellation_source: str,
) -> None:
    """Split one file and check chunk sizes and numbered IDs."""
    chunks = chunk_document(
        cancellation_source,
        source_dir / cancellation_source,
        small_chunk_settings,
    )
    assert len(chunks) > 1, (
        "A small chunk size must split the file."
    )
    assert all(
        len(doc.text) <= small_chunk_settings.chunk_size
        for doc in chunks
    ), "No chunk may exceed the chunk size."
    assert [doc.id for doc in chunks] == [
        f"{cancellation_source}#{n}" for n in range(len(chunks))
    ], "Chunk IDs must be the source path plus a counter."


def test_overlap_must_be_smaller_than_chunk_size(
    source_dir: Path,
) -> None:
    """Reject settings whose overlap is not below the chunk size."""
    with pytest.raises(ValidationError):
        KnowledgeSettings(
            source_dir=source_dir,
            chunk_size=100,
            chunk_overlap=100,
        )


def test_other_formats_are_ingested(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    text_file: Path,
    source_dir: Path,
) -> None:
    """Ingest a `.txt` file next to the Markdown documents."""
    report = sync(knowledge_settings, repository)
    source = text_file.relative_to(source_dir).as_posix()
    assert source in report.added, (
        "Files of any supported format must be ingested."
    )


def test_hidden_files_are_skipped(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    hidden_file: Path,
    sample_sources: list[str],
) -> None:
    """Keep hidden system files out of the knowledge base."""
    sync(knowledge_settings, repository)
    assert repository.sources() == set(sample_sources), (
        f"{hidden_file.name} must not be ingested."
    )


def test_unsupported_file_fails_before_writing(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    unsupported_file: Path,
) -> None:
    """Fail on an unreadable file before anything is stored."""
    with pytest.raises(UnsupportedFileFormatError):
        sync(knowledge_settings, repository)
    assert not repository.sources(), (
        f"Nothing may be stored when {unsupported_file.name} fails."
    )


@pytest.mark.parametrize(
    "folder", ["missing_source_dir", "empty_source_dir"]
)
def test_unusable_folder_keeps_the_store(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
    folder: str,
    request: pytest.FixtureRequest,
) -> None:
    """Fail on a missing or empty folder instead of deleting all."""
    sync(knowledge_settings, repository)
    broken = knowledge_settings.model_copy(
        update={"source_dir": request.getfixturevalue(folder)}
    )
    with pytest.raises(ValueError):
        sync(broken, repository)
    assert repository.sources() == set(sample_sources), (
        "A failed sync must leave the stored documents untouched."
    )


def test_blank_file_fails_before_writing(
    knowledge_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    blank_file: Path,
) -> None:
    """Reject a file with no text before anything is stored."""
    with pytest.raises(ValueError, match=blank_file.name):
        sync(knowledge_settings, repository)
    assert not repository.sources(), (
        "No file may be stored when one file is invalid."
    )


def test_folder_inside_hidden_folder_is_read(
    nested_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
) -> None:
    """Read documents whose project lives inside a dot-folder."""
    report = sync(nested_settings, repository)
    assert report.added == sample_sources, (
        "A dot-folder above `source_dir` must not hide its files."
    )


def test_relative_folder_with_parent_parts_is_read(
    relative_settings: KnowledgeSettings,
    repository: KnowledgeRepository,
    sample_sources: list[str],
) -> None:
    """Accept a `source_dir` such as `../knowledge`."""
    report = sync(relative_settings, repository)
    assert report.added == sample_sources, (
        "Relative paths with `..` must give the same source IDs."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
