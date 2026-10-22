import os
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from customer_support.config import KnowledgeSettings
from customer_support.knowledge import KnowledgeBase


def test_first_sync_adds_every_document(
    knowledge_base: KnowledgeBase, sample_sources: list[str]
) -> None:
    """Add every document of the folder on the first sync."""
    report = knowledge_base.sync()
    assert report.added == sample_sources, (
        "Every sample document must be added."
    )


def test_second_sync_skips_unchanged_documents(
    knowledge_base: KnowledgeBase, sample_sources: list[str]
) -> None:
    """Leave documents alone when nothing changed."""
    knowledge_base.sync()
    report = knowledge_base.sync()
    assert report.unchanged == sample_sources, (
        "Nothing changed, so every document must be unchanged."
    )


def test_touch_is_not_a_change(
    knowledge_base: KnowledgeBase,
    source_dir: Path,
    payments_source: str,
) -> None:
    """Ignore a newer modification time on the same content."""
    knowledge_base.sync()
    later = time.time() + 60
    os.utime(source_dir / payments_source, (later, later))
    report = knowledge_base.sync()
    assert payments_source in report.unchanged, (
        "Saving a file without changes must not re-index it."
    )


def test_edit_replaces_old_chunks(
    small_chunk_settings: KnowledgeSettings,
    source_dir: Path,
    cancellation_source: str,
    new_policy_text: str,
) -> None:
    """Replace every chunk of an edited document."""
    knowledge_base = KnowledgeBase(small_chunk_settings)
    knowledge_base.sync()
    path = source_dir / cancellation_source
    path.write_text(new_policy_text, encoding="utf-8")
    report = knowledge_base.sync()
    assert report.updated == [cancellation_source], (
        "Only the edited document must be updated."
    )
    chunks = [
        chunk
        for chunk in knowledge_base.search(new_policy_text, 100)
        if chunk.source == cancellation_source
    ]
    assert chunks, "The edited document must be searchable."
    assert all(
        chunk.text in new_policy_text for chunk in chunks
    ), "No chunk of the old version may survive the edit."


def test_deleted_document_is_removed(
    knowledge_base: KnowledgeBase,
    source_dir: Path,
    payments_source: str,
) -> None:
    """Remove the chunks of a document deleted from the folder."""
    knowledge_base.sync()
    (source_dir / payments_source).unlink()
    report = knowledge_base.sync()
    assert report.removed == [payments_source], (
        "The deleted document must be reported as removed."
    )
    sources = {
        c.source for c in knowledge_base.search("card", 100)
    }
    assert payments_source not in sources, (
        "No chunk of the deleted document may remain."
    )


def test_settings_change_rechunks_everything(
    knowledge_base: KnowledgeBase,
    small_chunk_settings: KnowledgeSettings,
    sample_sources: list[str],
) -> None:
    """Re-chunk every document when the chunk settings change."""
    knowledge_base.sync()
    report = KnowledgeBase(small_chunk_settings).sync()
    assert report.updated == sample_sources, (
        "New chunk settings must re-chunk every document."
    )


def test_model_change_reembeds_everything(
    knowledge_base: KnowledgeBase,
    knowledge_settings: KnowledgeSettings,
    other_embedding_model: str,
    sample_sources: list[str],
) -> None:
    """Re-embed every document when the embedding model changes."""
    knowledge_base.sync()
    settings = knowledge_settings.model_copy(
        update={"embedding_model": other_embedding_model}
    )
    report = KnowledgeBase(settings).sync()
    assert report.updated == sample_sources, (
        "A new embedding model must re-embed every document."
    )


def test_overlap_must_be_smaller_than_chunk_size() -> None:
    """Reject an overlap that is not smaller than the chunk size."""
    with pytest.raises(ValidationError, match="overlap"):
        KnowledgeSettings(chunk_size=64, chunk_overlap=64)


@pytest.mark.usefixtures("hidden_files", "unsupported_file")
def test_hidden_and_unsupported_files_are_ignored(
    knowledge_base: KnowledgeBase, sample_sources: list[str]
) -> None:
    """Skip dot-files, dot-folders and unknown extensions."""
    report = knowledge_base.sync()
    assert report.added == sample_sources, (
        "Only the sample documents may be added."
    )


def test_broken_file_leaves_the_store_unchanged(
    knowledge_base: KnowledgeBase,
    broken_file: Path,
    sample_sources: list[str],
) -> None:
    """Fail on an unreadable file before writing anything."""
    with pytest.raises(Exception, match="Error loading file"):
        knowledge_base.sync()
    broken_file.unlink()
    report = knowledge_base.sync()
    assert report.added == sample_sources, (
        "The failed sync must not have stored anything."
    )


@pytest.mark.parametrize(
    "folder", ["missing_source_dir", "empty_source_dir"]
)
def test_unusable_folder_keeps_the_store(
    knowledge_settings: KnowledgeSettings,
    knowledge_base: KnowledgeBase,
    sample_sources: list[str],
    folder: str,
    request: pytest.FixtureRequest,
) -> None:
    """Fail on a missing or empty folder instead of deleting all."""
    knowledge_base.sync()
    broken = knowledge_settings.model_copy(
        update={"source_dir": request.getfixturevalue(folder)}
    )
    with pytest.raises(ValueError):
        KnowledgeBase(broken).sync()
    report = knowledge_base.sync()
    assert report.unchanged == sample_sources, (
        "The failed sync must leave every document in place."
    )


def test_folder_inside_hidden_folder_is_read(
    nested_settings: KnowledgeSettings, sample_sources: list[str]
) -> None:
    """Read documents whose project lives inside a dot-folder."""
    report = KnowledgeBase(nested_settings).sync()
    assert report.added == sample_sources, (
        "A dot-folder above `source_dir` must not hide files."
    )


def test_relative_folder_with_parent_parts_is_read(
    relative_settings: KnowledgeSettings,
    sample_sources: list[str],
) -> None:
    """Accept a `source_dir` such as `../knowledge`."""
    report = KnowledgeBase(relative_settings).sync()
    assert report.added == sample_sources, (
        "Relative paths with `..` must give the same source IDs."
    )


def test_search_survives_a_restart(
    knowledge_base: KnowledgeBase,
    knowledge_settings: KnowledgeSettings,
    retrieval_query: str,
    cancellation_source: str,
) -> None:
    """Search a knowledge base reopened from disk."""
    knowledge_base.sync()
    reopened = KnowledgeBase(knowledge_settings)
    chunks = reopened.search(retrieval_query, limit=2)
    assert len(chunks) == 2, "The search must honour `limit`."
    assert chunks[0].source == cancellation_source, (
        "The closest chunk must be from the cancellation policy."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
