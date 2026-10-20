__all__ = ["Document", "KnowledgeRepository"]


from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult
from pydantic import BaseModel


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

    def replace_source(
        self,
        source: str,
        documents: list[Document],
        fingerprint: str,
    ) -> None:
        """Swap every stored chunk of `source` for `documents`.

        Args:
            source (str): Path of the document the chunks belong to.
            documents (list[Document]): New chunks of that document.
            fingerprint (str): Hash identifying this version.
        """
        self.delete_source(source)
        if documents:
            self._collection.upsert(
                ids=[doc.id for doc in documents],
                documents=[doc.text for doc in documents],
                metadatas=[
                    {
                        "source": source,
                        "fingerprint": fingerprint,
                    }
                    for _ in documents
                ],
            )

    def delete_source(self, source: str) -> None:
        """Delete every stored chunk of `source`.

        Args:
            source (str): Path of the document to remove.
        """
        self._collection.delete(where={"source": source})

    def sources(self) -> set[str]:
        """Return the paths of all documents currently stored.

        Returns:
            set[str]: One entry per stored document.
        """
        result = self._collection.get(include=["metadatas"])
        assert result["metadatas"] is not None, (
            "Missing metadata."
        )
        return {
            str(meta["source"]) for meta in result["metadatas"]
        }

    def stored_fingerprint(self, source: str) -> str | None:
        """Return the fingerprint stored for `source`, if any.

        Args:
            source (str): Path of the document to look up.

        Returns:
            str | None: The stored hash, or None if not stored.
        """
        result = self._collection.get(
            where={"source": source},
            limit=1,
            include=["metadatas"],
        )
        assert result["metadatas"] is not None, (
            "Missing metadata."
        )
        if not result["metadatas"]:
            return None
        return str(result["metadatas"][0]["fingerprint"])

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
                source=str(meta["source"]),
            )
            for id_, text, meta in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
            )
        ]
