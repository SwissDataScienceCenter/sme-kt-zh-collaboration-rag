import json
import chromadb
from typing import Any
import numpy as np
from numpy.typing import NDArray

from conversational_toolkit.chunking.base import Chunk
from conversational_toolkit.utils.database import generate_uid
from conversational_toolkit.vectorstores.base import VectorStore, ChunkMatch, ChunkRecord


class ChromaDBVectorStore(VectorStore):
    def __init__(self, db_path: str, collection_name: str = "default_collection"):
        """
        Initialize the ChromaDB vector store.

        :param db_path: Path to store the ChromaDB database.
        :param collection_name: Name of the collection within the database.
        """
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    async def insert_chunks(self, chunks: list[Chunk], embedding: NDArray[np.float64]) -> None:
        """
        Insert chunks into ChromaDB.

        :param chunks: List of document chunks
        :param embedding: Corresponding embedding vectors
        """
        documents = []
        metadatas = []
        ids = []

        for chunk, _ in zip(chunks, embedding):
            doc_id = str(generate_uid())
            documents.append(chunk.content)
            raw_meta = {"title": chunk.title, "mime_type": chunk.mime_type, **chunk.metadata}
            # ChromaDB only accepts str/int/float/bool — serialize anything else to JSON
            safe_meta = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in raw_meta.items()}
            metadatas.append(safe_meta)
            ids.append(doc_id)

        self.collection.add(
            ids=ids,
            embeddings=embedding.tolist(),  # type: ignore
            metadatas=metadatas,  # type: ignore
            documents=documents,
        )

    async def get_chunks_by_embedding(
        self, embedding: NDArray[np.float64], top_k: int, filters: dict[str, Any] | None = None
    ) -> list[ChunkMatch]:
        """
        Retrieve chunks most similar to the given embedding.

        :param embedding: Query embedding
        :param top_k: Number of results to return
        :param filters: Optional filters for metadata
        """
        results = self.collection.query(query_embeddings=embedding.tolist(), n_results=top_k, where=filters)  # type: ignore

        chunk_matches = []
        if results and results["ids"]:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                chunk_matches.append(
                    ChunkMatch(
                        id=results["ids"][0][i],
                        title=str(metadata.get("title", "")),
                        mime_type=str(metadata.get("mime_type", "")),
                        metadata=metadata,  # type: ignore
                        content=results["documents"][0][i] if results["documents"] else "",
                        embedding=[],
                        score=results["distances"][0][i] if results["distances"] else 0.0,
                    )
                )

        return chunk_matches

    async def get_chunks_by_filter(self, filters: dict[str, Any]) -> list[ChunkRecord]:
        """
        Return all chunks matching the given metadata filters (no embedding needed).

        Uses ChromaDB's 'collection.get(where=filters)'. Supports ChromaDB filter
        operators: '$eq', '$ne', '$gt', '$lt', '$gte', '$lte', '$and', '$or'.

        Example — fetch all chunks from a specific file at a given index:
            filters = {
                "$and": [
                    {"source_file": {"$eq": "report.pdf"}},
                    {"chunk_index": {"$eq": 3}},
                ]
            }
        """
        results = self.collection.get(where=filters)  # type: ignore[arg-type]

        chunk_records = []
        if results and results["ids"]:
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                chunk_records.append(
                    ChunkRecord(
                        id=results["ids"][i],
                        title=str(metadata.get("title", "")),
                        mime_type=str(metadata.get("mime_type", "")),
                        content=results["documents"][i] if results["documents"] else "",
                        metadata=metadata,  # type: ignore
                        embedding=[],
                    )
                )
        return chunk_records

    async def get_chunks_by_ids(self, chunk_ids: int | list[int]) -> list[Chunk]:
        """
        Retrieve chunks by their IDs.

        :param chunk_ids: A single ID or a list of IDs
        :return: List of retrieved chunks
        """
        if isinstance(chunk_ids, int):
            chunk_ids = [str(chunk_ids)]  # type: ignore
        else:
            chunk_ids = [str(cid) for cid in chunk_ids]  # type: ignore

        results = self.collection.get(ids=chunk_ids)  # type: ignore

        chunks = []
        if results and results["ids"]:
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                chunks.append(
                    Chunk(
                        title=str(metadata.get("title", "")),
                        mime_type=str(metadata.get("mime_type", "")),
                        content=results["documents"][i] if results["documents"] else "",
                        metadata=metadata,  # type: ignore
                    )
                )

        return chunks
