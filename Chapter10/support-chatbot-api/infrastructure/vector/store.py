import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from ..config.settings import settings


class VectorStore:
    """Vector store for semantic search using ChromaDB."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.collection_name = "support_policies"

    def get_collection(self):
        """Get or create the support policies collection."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text using OpenAI."""
        response = self.openai_client.embeddings.create(
            input=text,
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict | None = None
    ):
        """Add a document to the vector store."""
        collection = self.get_collection()
        embedding = self.generate_embedding(text)

        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )

    def search(
        self,
        query: str,
        n_results: int = 3
    ) -> list[dict]:
        """Search for similar documents."""
        collection = self.get_collection()
        query_embedding = self.generate_embedding(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

        return documents


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Dependency that provides the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
