import pytest

from customer_support.knowledge import (
    Document,
    KnowledgeRepository,
)

DOCUMENTS = [
    Document(
        id="cancellation",
        text="Parents can cancel a reservation for free up to "
        "24 hours before it starts.",
        source="faq",
    ),
    Document(
        id="first-aid",
        text="Every babysitter must hold a valid first aid "
        "certificate.",
        source="faq",
    ),
    Document(
        id="payments",
        text="Payments are charged to the saved card when the "
        "session ends.",
        source="faq",
    ),
]


def test_search_returns_relevant_document(
    repository: KnowledgeRepository,
) -> None:
    """Test the most relevant document comes first."""
    repository.add(DOCUMENTS)
    results = repository.search("cancel a reservation", limit=1)
    assert [doc.id for doc in results] == ["cancellation"]


def test_add_replaces_document_with_same_id(
    repository: KnowledgeRepository,
) -> None:
    """Test adding an existing id updates it instead of duplicating."""
    repository.add(DOCUMENTS)
    text = "Once confirmed, a reservation cannot be cancelled."
    updated = DOCUMENTS[0].model_copy(update={"text": text})
    repository.add([updated])
    results = repository.search("cancel a reservation", limit=3)
    texts = [doc.text for doc in results if doc.id == updated.id]
    assert texts == [text]


def test_search_matches_meaning_not_words(
    repository: KnowledgeRepository,
) -> None:
    """Test a question sharing no keyword still finds its answer."""
    repository.add(DOCUMENTS)
    results = repository.search(
        "Is a sitter trained in CPR?", limit=1
    )
    assert [doc.id for doc in results] == ["first-aid"]


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
