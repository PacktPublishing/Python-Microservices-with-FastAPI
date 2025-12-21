"""Test script to verify vector store functionality."""
from infrastructure.vector.store import get_vector_store

store = get_vector_store()

store.add_document(
    "refund-policy",
    "Our refund policy states that cancellations made 24 hours before "
    "the booking receive a full refund including platform fees.",
    {"category": "refunds", "section": "cancellations"}
)

store.add_document(
    "payment-processing",
    "Payment is processed immediately when the booking is confirmed. "
    "The sitter receives 85% of the booking fee after completion.",
    {"category": "payments", "section": "processing"}
)

store.add_document(
    "background-checks",
    "All sitters must complete a background check before accepting "
    "bookings. The check includes criminal records and identity verification.",
    {"category": "safety", "section": "verification"}
)

queries = [
    "Can I get my money back?",
    "How does the sitter get paid?",
    "Are sitters verified?"
]

for query in queries:
    print(f"\nQuery: {query}")
    results = store.search(query, n_results=2)

    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc['id']} (distance: {doc['distance']:.3f})")
        print(f"   {doc['text'][:80]}...")
