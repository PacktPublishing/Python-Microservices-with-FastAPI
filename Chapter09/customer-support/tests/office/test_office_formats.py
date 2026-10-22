import pytest

from customer_support.knowledge import KnowledgeBase


def test_pdf_and_word_documents_are_added(
    knowledge_base: KnowledgeBase, office_sources: list[str]
) -> None:
    """Add the PDF and the Word file like any other document."""
    report = knowledge_base.sync()
    assert set(office_sources) <= set(report.added), (
        "The PDF and the Word file must be added."
    )


@pytest.mark.usefixtures("office_sources")
def test_pdf_pages_form_one_document(
    knowledge_base: KnowledgeBase,
    refund_query: str,
    refund_source: str,
    second_page_text: str,
) -> None:
    """Find the PDF, with both of its pages in the same chunk."""
    knowledge_base.sync()
    best = knowledge_base.search(refund_query, limit=1)[0]
    assert best.source == refund_source, (
        "The refund question must find the refund PDF."
    )
    assert second_page_text in " ".join(best.text.split()), (
        "Both pages of the PDF must be in the same document."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
