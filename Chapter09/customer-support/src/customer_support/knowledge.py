__all__ = ["Document", "KnowledgeRepository"]


from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult
from pydantic import BaseModel, TypeAdapter


class Document(BaseModel):
    """A piece of knowledge the chatbot can retrieve."""

    id: str
    text: str
    source: str


class KnowledgeRepository:
    """Stores documents in ChromaDB and searches them by meaning."""

    def __init__(
        self,
        client: ClientAPI,
        name: str = "knowledge",
    ) -> None:
        self._collection = client.get_or_create_collection(name)

    def add(self, documents: list[Document]) -> None:
        """Embed and store documents, replacing those with the same id."""
        if documents:
            self._collection.upsert(
                ids=[doc.id for doc in documents],
                documents=[doc.text for doc in documents],
                metadatas=[
                    {"source": doc.source} for doc in documents
                ],
            )

    def search(
        self, query: str, limit: int = 3
    ) -> list[Document]:
        """Return the documents closest in meaning to the query."""
        result: QueryResult = self._collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas"],
        )
        assert result["documents"] is not None, (
            "Missing documents."
        )
        assert result["metadatas"] is not None, (
            "Missing metadata."
        )
        return [
            Document(
                id=id_,
                text=text,
                source=TypeAdapter(str).validate_python(
                    meta["source"], strict=True
                ),
            )
            for id_, text, meta in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
            )
        ]
