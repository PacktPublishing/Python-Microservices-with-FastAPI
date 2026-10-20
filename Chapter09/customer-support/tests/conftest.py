import shutil
import typing as ty
import uuid
from pathlib import Path

import chromadb
import pytest
from fastapi.testclient import TestClient

from customer_support import Settings
from customer_support.api import app
from customer_support.config import KnowledgeSettings
from customer_support.knowledge import KnowledgeRepository


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
def source_dir(tmp_path: Path, tests_dir: Path) -> Path:
    """Copy of the sample `knowledge/` folder that tests may edit."""
    target = tmp_path / "knowledge"
    shutil.copytree(tests_dir.parent / "knowledge", target)
    return target


@pytest.fixture
def knowledge_settings(source_dir: Path) -> KnowledgeSettings:
    """Default chunking settings over the copied sample folder."""
    return KnowledgeSettings(source_dir=source_dir)


@pytest.fixture
def small_chunk_settings(source_dir: Path) -> KnowledgeSettings:
    """Settings whose chunk size forces several chunks per file."""
    return KnowledgeSettings(
        source_dir=source_dir, chunk_size=80, chunk_overlap=20
    )


@pytest.fixture
def sample_sources(source_dir: Path) -> list[str]:
    """Relative POSIX paths of the sample Markdown files, sorted."""
    return sorted(
        path.relative_to(source_dir).as_posix()
        for path in source_dir.rglob("*.md")
    )


@pytest.fixture
def cancellation_source() -> str:
    """Relative path of the sample cancellation policy."""
    return "policies/cancellation.md"


@pytest.fixture
def payments_source() -> str:
    """Relative path of the sample payments FAQ."""
    return "faq/payments.md"


@pytest.fixture
def retrieval_query() -> str:
    """Question that the cancellation policy answers."""
    return "What is the cancellation policy?"


@pytest.fixture
def new_policy_text() -> str:
    """Replacement body for the edited cancellation policy."""
    return "Cancellation now requires 48 hours of notice."


@pytest.fixture
def text_file(source_dir: Path) -> Path:
    """A plain-text document, which the sync must ingest too."""
    path = source_dir / "notes.txt"
    path.write_text(
        "Draft notes, not knowledge.", encoding="utf-8"
    )
    return path


@pytest.fixture
def blank_file(source_dir: Path) -> Path:
    """A Markdown file with no text, which cannot be chunked."""
    path = source_dir / "faq" / "blank.md"
    path.write_text("   \n", encoding="utf-8")
    return path


@pytest.fixture
def empty_source_dir(tmp_path: Path) -> Path:
    """A folder that holds nothing but a hidden system file."""
    path = tmp_path / "empty"
    path.mkdir()
    (path / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
    return path


@pytest.fixture
def hidden_file(source_dir: Path) -> Path:
    """A hidden system file the sync must skip."""
    path = source_dir / ".DS_Store"
    path.write_bytes(b"\x00\x00\x00\x01Bud1")
    return path


@pytest.fixture
def unsupported_file(source_dir: Path) -> Path:
    """A binary file that no parser can read."""
    path = source_dir / "faq" / "data.bin"
    path.write_bytes(bytes(range(256)))
    return path


@pytest.fixture
def missing_source_dir(tmp_path: Path) -> Path:
    """A source folder path that does not exist."""
    return tmp_path / "missing"


@pytest.fixture
def ingestion_environment(
    monkeypatch: pytest.MonkeyPatch,
    source_dir: Path,
    tmp_path: Path,
) -> Path:
    """Point the CLI at the copied folder and a temporary store."""
    storage = tmp_path / "chroma"
    prefix = "CUSTOMER_SUPPORT_KNOWLEDGE_"
    monkeypatch.setenv(prefix + "SOURCE_DIR", str(source_dir))
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


@pytest.fixture
def nested_settings(
    tmp_path: Path, tests_dir: Path
) -> KnowledgeSettings:
    """Settings for a copy of `knowledge/` under a dot-folder."""
    target = tmp_path / ".book" / "knowledge"
    shutil.copytree(tests_dir.parent / "knowledge", target)
    return KnowledgeSettings(source_dir=target)


@pytest.fixture
def relative_settings(
    tmp_path: Path,
    source_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> KnowledgeSettings:
    """Settings that reach the copied folder through a `..` path."""
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    return KnowledgeSettings(
        source_dir=Path("..") / source_dir.name
    )
