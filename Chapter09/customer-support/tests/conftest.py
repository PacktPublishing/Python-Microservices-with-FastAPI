import typing as ty
import uuid
from pathlib import Path

import chromadb
import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from customer_support import Settings
from customer_support.api import app
from customer_support.knowledge import (
    Document,
    KnowledgeRepository,
)


@pytest.fixture
def tests_dir() -> Path:
    """Location to this `tests` folder."""
    return Path(__file__).parent


@pytest.fixture
def client() -> TestClient:
    """Test client for the customer support API."""
    return TestClient(app)


@pytest.fixture
def repository() -> KnowledgeRepository:
    """Knowledge repository backed by an in-memory ChromaDB."""
    return KnowledgeRepository(
        chromadb.EphemeralClient(),
        name=f"test-{uuid.uuid4().hex}",
    )


@pytest.fixture
def source_documents(tests_dir: Path) -> list[Document]:
    """Load the example passages as expected ingestion results."""
    source = tests_dir.parent / "knowledge.json"
    return TypeAdapter(list[Document]).validate_json(
        source.read_text(encoding="utf-8")
    )


@pytest.fixture
def knowledge_file(
    tmp_path: Path, source_documents: list[Document]
) -> Path:
    """Write a temporary JSON input from the expected passages."""
    path = tmp_path / "knowledge.json"
    path.write_bytes(
        TypeAdapter(list[Document]).dump_json(source_documents)
    )
    return path


@pytest.fixture
def updated_documents(
    source_documents: list[Document],
) -> list[Document]:
    """Change the cancellation passage while preserving its ID."""
    updated = source_documents[0].model_copy()
    updated.text = "Cancellation requires 48 hours of notice."
    return [updated, *source_documents[1:]]


@pytest.fixture
def retrieval_query() -> str:
    """Provide the cancellation question for ingestion tests."""
    return "What is the cancellation policy?"


@pytest.fixture(
    params=[
        "{",
        '[{"id": "missing-fields"}]',
        '[{"id": " ", "text": "text", "source": "faq"}]',
        '[{"id": "blank", "text": " ", "source": "faq"}]',
        '[{"id": "blank", "text": "text", "source": " "}]',
    ]
)
def invalid_knowledge_file(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Path:
    """Write malformed JSON or a passage with blank fields."""
    path = tmp_path / "invalid.json"
    path.write_text(str(request.param), encoding="utf-8")
    return path


@pytest.fixture
def empty_knowledge_file(tmp_path: Path) -> Path:
    """Provide an empty but valid input array."""
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")
    return path


@pytest.fixture
def duplicate_knowledge_file(
    knowledge_file: Path, source_documents: list[Document]
) -> Path:
    """Append a duplicate ID after otherwise valid passages."""
    documents = [*source_documents, source_documents[0]]
    knowledge_file.write_bytes(
        TypeAdapter(list[Document]).dump_json(documents)
    )
    return knowledge_file


@pytest.fixture
def missing_knowledge_file(tmp_path: Path) -> Path:
    """Provide a path that does not exist."""
    return tmp_path / "missing.json"


@pytest.fixture
def ingestion_environment(
    monkeypatch: pytest.MonkeyPatch,
    knowledge_file: Path,
    tmp_path: Path,
) -> Path:
    """Configure an isolated persistent import through settings."""
    storage = tmp_path / "chroma"
    prefix = "CUSTOMER_SUPPORT_KNOWLEDGE_"
    monkeypatch.setenv(prefix + "INPUT_FILE", str(knowledge_file))
    monkeypatch.setenv(prefix + "STORAGE_PATH", str(storage))
    monkeypatch.setenv(prefix + "COLLECTION", "ingestion-test")
    return storage


@pytest.fixture
def cli_storage_path(tmp_path: Path) -> Path:
    """Storage directory passed as a flag, overriding the environment."""
    return tmp_path / "chroma-from-cli"


@pytest.fixture
def open_repository() -> ty.Callable[[Path], KnowledgeRepository]:
    """Reopen the configured collection with a new persistent client."""

    def _open(storage: Path) -> KnowledgeRepository:
        """Build a repository over `storage` and the configured name.

        Args:
            storage (Path): ChromaDB persistence directory to open.

        Returns:
            KnowledgeRepository: Repository on a fresh client.
        """
        return KnowledgeRepository(
            chromadb.PersistentClient(path=str(storage)),
            name=Settings().knowledge.collection,
        )

    return _open
