import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from customer_support.api import app
from customer_support.config import KnowledgeSettings
from customer_support.knowledge import KnowledgeBase


@pytest.fixture
def client() -> TestClient:
    """Test client for the customer support API."""
    return TestClient(app)


@pytest.fixture
def tests_dir() -> Path:
    """Location to this `tests` folder."""
    return Path(__file__).parent


@pytest.fixture
def source_dir(tmp_path: Path, tests_dir: Path) -> Path:
    """Copy of the sample `knowledge/` folder that tests may edit."""
    target = tmp_path / "knowledge"
    shutil.copytree(tests_dir.parent / "knowledge", target)
    return target


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    """Folder holding the vectors and the sync state."""
    return tmp_path / "store"


@pytest.fixture
def knowledge_settings(
    source_dir: Path, storage_path: Path
) -> KnowledgeSettings:
    """Default settings over the copied folder and a fresh store."""
    return KnowledgeSettings(
        source_dir=source_dir, storage_path=storage_path
    )


@pytest.fixture
def small_chunk_settings(
    knowledge_settings: KnowledgeSettings,
) -> KnowledgeSettings:
    """Settings whose chunk size forces several chunks per file."""
    return knowledge_settings.model_copy(
        update={"chunk_size": 32, "chunk_overlap": 8}
    )


@pytest.fixture
def other_embedding_model() -> str:
    """A second small model with the same 384 dimensions."""
    return "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture
def knowledge_base(
    knowledge_settings: KnowledgeSettings,
) -> KnowledgeBase:
    """Knowledge base with the default settings."""
    return KnowledgeBase(knowledge_settings)


@pytest.fixture
def sample_sources() -> list[str]:
    """Relative POSIX paths of the sample documents, sorted."""
    return [
        "faq/payments.md",
        "policies/cancellation.md",
        "resolutions/duplicate-charge.md",
    ]


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
    return (
        "Cancellation now requires 48 hours of notice. "
        "Late cancellations are charged in full. "
        "Bookings made with a voucher cannot be cancelled. "
        "Refunds for cancelled bookings take five working days."
    )


@pytest.fixture
def hidden_files(source_dir: Path) -> None:
    """A hidden system file and a hidden folder to skip."""
    (source_dir / ".DS_Store").write_bytes(
        b"\x00\x00\x00\x01Bud1"
    )
    (source_dir / ".git").mkdir()
    (source_dir / ".git" / "notes.md").write_text(
        "Not knowledge.", encoding="utf-8"
    )


@pytest.fixture
def unsupported_file(source_dir: Path) -> None:
    """A file whose extension is not in `extensions`."""
    (source_dir / "faq" / "data.bin").write_bytes(
        bytes(range(256))
    )


@pytest.fixture
def broken_file(source_dir: Path) -> Path:
    """A PDF that cannot be parsed."""
    path = source_dir / "faq" / "broken.pdf"
    path.write_bytes(b"%PDF-1.4 not really a PDF")
    return path


@pytest.fixture
def missing_source_dir(tmp_path: Path) -> Path:
    """A source folder path that does not exist."""
    return tmp_path / "missing"


@pytest.fixture
def empty_source_dir(tmp_path: Path) -> Path:
    """A folder that holds nothing but a hidden system file."""
    path = tmp_path / "empty"
    path.mkdir()
    (path / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
    return path


@pytest.fixture
def nested_settings(
    tmp_path: Path, tests_dir: Path, storage_path: Path
) -> KnowledgeSettings:
    """Settings for a copy of `knowledge/` under a dot-folder."""
    target = tmp_path / ".local" / "knowledge"
    shutil.copytree(tests_dir.parent / "knowledge", target)
    return KnowledgeSettings(
        source_dir=target, storage_path=storage_path
    )


@pytest.fixture
def relative_settings(
    tmp_path: Path,
    source_dir: Path,
    storage_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> KnowledgeSettings:
    """Settings that reach the copied folder through a `..` path."""
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    return KnowledgeSettings(
        source_dir=Path("..") / source_dir.name,
        storage_path=storage_path,
    )


@pytest.fixture
def ingestion_environment(
    monkeypatch: pytest.MonkeyPatch,
    source_dir: Path,
    storage_path: Path,
) -> KnowledgeSettings:
    """Point the CLI at the copied folder and a temporary store."""
    env = "CUSTOMER_SUPPORT_KNOWLEDGE_"
    monkeypatch.setenv(env + "SOURCE_DIR", str(source_dir))
    monkeypatch.setenv(env + "STORAGE_PATH", str(storage_path))
    return KnowledgeSettings()


@pytest.fixture
def cli_storage_path(tmp_path: Path) -> Path:
    """Storage folder passed as a flag, overriding the environment."""
    return tmp_path / "store-from-cli"
