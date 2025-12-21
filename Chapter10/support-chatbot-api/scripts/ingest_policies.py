"""Script to ingest marketplace policies into the vector store."""
from pathlib import Path

from infrastructure.vector.store import get_vector_store


def load_policy_document() -> str:
    """Load the policies markdown file."""
    policy_path = (
        Path(__file__).parent.parent
        / "domain"
        / "support"
        / "policies.md"
    )
    return policy_path.read_text()


def chunk_by_headers(content: str) -> list[dict]:
    """Split document into chunks based on markdown headers."""
    chunks = []
    lines = content.split('\n')

    current_h1 = ""
    current_h2 = ""
    current_content = []

    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            if current_content and current_h2:
                chunks.append({
                    'section': current_h1,
                    'subsection': current_h2,
                    'content': '\n'.join(current_content).strip()
                })
            current_h1 = line.replace('# ', '').strip()
            current_h2 = ""
            current_content = []

        elif line.startswith('## '):
            if current_content and current_h2:
                chunks.append({
                    'section': current_h1,
                    'subsection': current_h2,
                    'content': '\n'.join(current_content).strip()
                })

            current_h2 = line.replace('## ', '').strip()
            current_content = []

        elif line.strip() and current_h2:
            current_content.append(line)

    if current_content and current_h2:
        chunks.append({
            'section': current_h1,
            'subsection': current_h2,
            'content': '\n'.join(current_content).strip()
        })

    return chunks


def ingest_policies():
    """Load policies and add them to the vector store."""
    print("Loading policies document...")
    content = load_policy_document()

    print("Chunking document by headers...")
    chunks = chunk_by_headers(content)
    print(f"Created {len(chunks)} chunks")

    store = get_vector_store()

    print("\nIngesting chunks into vector store...")
    for i, chunk in enumerate(chunks, 1):
        section = chunk['section'].lower().replace(' ', '-')
        subsection = chunk['subsection'].lower().replace(' ', '-')
        doc_id = f"policy-{section}-{subsection}"

        heading = f"{chunk['section']}: {chunk['subsection']}"
        full_text = f"{heading}\n\n{chunk['content']}"

        metadata = {
            'section': chunk['section'],
            'subsection': chunk['subsection'],
            'doc_type': 'policy'
        }

        store.add_document(doc_id, full_text, metadata)
        section = chunk['section']
        subsection = chunk['subsection']
        print(f"{i}. Added: {section} - {subsection}")

    print("\nPolicy ingestion complete!")


if __name__ == "__main__":
    ingest_policies()
