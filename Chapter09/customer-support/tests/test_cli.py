from pathlib import Path

import pytest

from customer_support.__main__ import main
from customer_support.config import KnowledgeSettings
from customer_support.knowledge import KnowledgeBase


def test_ingest_command_syncs_the_folder(
    ingestion_environment: KnowledgeSettings,
    cancellation_source: str,
    retrieval_query: str,
) -> None:
    """Run `ingest`, then search the knowledge base it stored."""
    main(["ingest"])
    knowledge_base = KnowledgeBase(ingestion_environment)
    best = knowledge_base.search(retrieval_query, limit=1)[0]
    assert best.source == cancellation_source, (
        "The synced cancellation policy must be searchable."
    )


def test_ingest_flag_overrides_environment(
    ingestion_environment: KnowledgeSettings,
    cli_storage_path: Path,
    sample_sources: list[str],
) -> None:
    """Check `--storage-path` wins over the environment variable."""
    main(["ingest", "--storage-path", str(cli_storage_path)])
    settings = ingestion_environment.model_copy(
        update={"storage_path": cli_storage_path}
    )
    report = KnowledgeBase(settings).sync()
    assert report.unchanged == sample_sources, (
        "The flag's folder must hold the synced documents."
    )
    assert not ingestion_environment.storage_path.exists(), (
        "The environment's folder must not be created."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
