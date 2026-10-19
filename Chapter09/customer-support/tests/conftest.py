import uuid
from pathlib import Path

import chromadb
import pytest
from fastapi.testclient import TestClient

from customer_support.api import app
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
