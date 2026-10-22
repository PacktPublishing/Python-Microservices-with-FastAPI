__all__ = ["Chunk", "KnowledgeBase", "SyncReport"]

from pathlib import Path

import chromadb
from llama_index.core import (
    Document,
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.core.ingestion import (
    DocstoreStrategy,
    IngestionPipeline,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from loguru import logger
from pydantic import BaseModel

from .config import KnowledgeSettings


class Chunk(BaseModel):
    """A piece of a source document returned by a search."""

    text: str
    source: str


class SyncReport(BaseModel):
    """Sources a sync added, updated, left unchanged or removed."""

    added: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    removed: list[str] = []

    @classmethod
    def compare(
        cls, stored: dict[str, str], documents: list[Document]
    ) -> "SyncReport":
        """Compare the stored hashes with the documents on disk.

        Args:
            stored (dict[str, str]): Hash of each stored source.
            documents (list[Document]): Documents read from disk.

        Returns:
            SyncReport: What changed, by source.
        """
        on_disk = {doc.id_ for doc in documents}
        report = cls(removed=sorted(stored.keys() - on_disk))
        for doc in documents:
            if doc.id_ not in stored:
                report.added.append(doc.id_)
            elif stored[doc.id_] != doc.hash:
                report.updated.append(doc.id_)
            else:
                report.unchanged.append(doc.id_)
        return report


class KnowledgeBase:
    """Documents of a folder, chunked, embedded and searchable.

    LlamaIndex reads, chunks and embeds the documents and tracks
    which ones changed. ChromaDB stores the vectors. Both live
    under `storage_path`.
    """

    def __init__(self, settings: KnowledgeSettings) -> None:
        self._settings = settings
        self._docstore_path = (
            settings.storage_path / "docstore.json"
        )
        client = chromadb.PersistentClient(
            path=str(settings.storage_path / "chroma")
        )
        self._vector_store = ChromaVectorStore(
            chroma_collection=client.get_or_create_collection(
                "knowledge"
            )
        )
        self._embed_model = FastEmbedEmbedding(
            model_name=settings.embedding_model
        )

    def load_documents(self) -> list[Document]:
        """Read every supported file under `source_dir`.

        Each file becomes one document, identified by its path
        relative to `source_dir`, with the pages of a PDF joined.
        The embedding model and chunk settings are part of the
        metadata, so changing them changes every document's hash,
        but they are kept out of the embedded text.

        Raises:
            ValueError: If the folder is missing or has no files.
            Exception: If a file cannot be parsed.

        Returns:
            list[Document]: The documents, sorted by source.
        """
        root = self._settings.source_dir.resolve()
        reader = SimpleDirectoryReader(
            input_dir=root,
            recursive=True,
            required_exts=self._settings.extensions,
            exclude_hidden=False,
            exclude=["**/.*", "**/.*/**"],
            raise_on_error=True,
        )
        indexing = (
            f"{self._settings.embedding_model}:"
            f"{self._settings.chunk_size}:"
            f"{self._settings.chunk_overlap}"
        )
        documents = []
        for pages in reader.iter_data():
            path = Path(pages[0].metadata["file_path"])
            source = path.relative_to(root).as_posix()
            text = "\n\n".join(page.text for page in pages)
            documents.append(
                Document(
                    id_=source,
                    text=text,
                    metadata={
                        "source": source,
                        "indexing": indexing,
                    },
                    excluded_embed_metadata_keys=["indexing"],
                    excluded_llm_metadata_keys=["indexing"],
                )
            )
        return sorted(documents, key=lambda doc: doc.id_)

    def _open_docstore(self) -> SimpleDocumentStore:
        """Load the hashes of the last sync, or start empty.

        Returns:
            SimpleDocumentStore: The document store.
        """
        if self._docstore_path.exists():
            return SimpleDocumentStore.from_persist_path(
                str(self._docstore_path)
            )
        return SimpleDocumentStore()

    def _pipeline(
        self, docstore: SimpleDocumentStore
    ) -> IngestionPipeline:
        """Chunk, embed and store, skipping unchanged documents.

        Args:
            docstore (SimpleDocumentStore): Hashes of the last sync.

        Returns:
            IngestionPipeline: The pipeline to run.
        """
        splitter = SentenceSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )
        strategy = DocstoreStrategy.UPSERTS_AND_DELETE
        return IngestionPipeline(
            transformations=[splitter, self._embed_model],
            vector_store=self._vector_store,
            docstore=docstore,
            docstore_strategy=strategy,
        )

    def sync(self) -> SyncReport:
        """Make the stored chunks match the source folder.

        New and changed documents are chunked, embedded and stored,
        replacing older chunks; unchanged ones are skipped; deleted
        ones are removed. Every file is read before anything is
        written, so a missing folder or an unreadable file leaves
        the store as it was.

        Returns:
            SyncReport: What changed, by source.
        """
        documents = self.load_documents()
        docstore = self._open_docstore()
        hashes = docstore.get_all_document_hashes()
        stored = {
            source: digest for digest, source in hashes.items()
        }
        self._pipeline(docstore).run(documents=documents)
        docstore.persist(str(self._docstore_path))
        report = SyncReport.compare(stored, documents)
        logger.info("Knowledge base synced: {}", report)
        return report

    def search(self, query: str, limit: int = 3) -> list[Chunk]:
        """Find the chunks closest in meaning to `query`.

        Args:
            query (str): Question or text to search for.
            limit (int): Maximum number of chunks to return.

        Returns:
            list[Chunk]: The chunks, closest first.
        """
        index = VectorStoreIndex.from_vector_store(
            self._vector_store, embed_model=self._embed_model
        )
        retriever = index.as_retriever(similarity_top_k=limit)
        return [
            Chunk(
                text=hit.node.get_content(),
                source=str(hit.node.metadata["source"]),
            )
            for hit in retriever.retrieve(query)
        ]
