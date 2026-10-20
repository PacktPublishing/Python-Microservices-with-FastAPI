import typing as ty
from pathlib import Path

import pytest

from customer_support.__main__ import main
from customer_support.knowledge import (
    Document,
    KnowledgeRepository,
)


def test_ingest_command_persists_documents(
    ingestion_environment: Path,
    open_repository: ty.Callable[[Path], KnowledgeRepository],
    source_documents: list[Document],
    retrieval_query: str,
) -> None:
    """Run `ingest`, then retrieve from a new persistent client."""
    main(["ingest"])
    reopened = open_repository(ingestion_environment)
    assert (
        reopened.search(retrieval_query)[0] == source_documents[0]
    ), (
        "A new client must retrieve the imported cancellation passage."
    )


def test_ingest_flag_overrides_environment(
    ingestion_environment: Path,
    cli_storage_path: Path,
    open_repository: ty.Callable[[Path], KnowledgeRepository],
    source_documents: list[Document],
    retrieval_query: str,
) -> None:
    """Check `--storage-path` wins over the environment variable."""
    main(["ingest", "--storage-path", str(cli_storage_path)])
    reopened = open_repository(cli_storage_path)
    assert (
        reopened.search(retrieval_query)[0] == source_documents[0]
    ), "The flag's directory must hold the imported passages."
    assert not ingestion_environment.exists(), (
        "The environment's directory must not be created."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
