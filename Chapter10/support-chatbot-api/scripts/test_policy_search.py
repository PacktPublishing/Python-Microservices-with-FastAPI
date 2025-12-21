"""Script to test policy search accuracy."""
from infrastructure.vector.store import get_vector_store


def test_search(query: str, expected_section: str):
    """Test that search returns the expected policy section."""
    store = get_vector_store()
    results = store.search(query, n_results=1)

    if results:
        top_result = results[0]
        actual = top_result['metadata']['subsection']
        distance = top_result['distance']
        is_match = expected_section.lower() in actual.lower()

        print(f"\nQuery: {query}")
        print(f"Expected: {expected_section}")
        print(f"Got: {actual}")
        print(f"Distance: {distance:.3f}")
        print(f"Match: {'y' if is_match else 'n'}")
        return actual
    return None


if __name__ == "__main__":
    test_cases = [
        ("Can I get my money back if the sitter cancels?", "Full Refunds"),
        ("How much does the sitter earn per booking?", "Sitter Compensation"),
        ("Are sitters background checked?", "Required Verification"),
        ("What if there's an emergency during the booking?", "Emergency Procedures"),
        ("Can I pay with Venmo?", "Payment Methods"),
    ]

    correct = 0
    for query, expected in test_cases:
        result = test_search(query, expected)
        if result and expected.lower() in result.lower():
            correct += 1

    print(f"\n{'='*60}")
    print(f"Results: {correct}/{len(test_cases)} queries returned correct section")
