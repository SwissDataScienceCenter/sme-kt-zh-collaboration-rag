from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from conversational_toolkit.chunking.base import Chunk
from conversational_toolkit.utils.database import generate_uid
from conversational_toolkit.vectorstores.base import VectorStore, ChunkMatch

from sqlalchemy import text, and_
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, String, JSON
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from numpy.typing import NDArray

from sqlalchemy import insert, select


class PGVectorStore(VectorStore):
    def __init__(
        self,
        engine: AsyncEngine,
        table_name: str,
        embeddings_size: int,
    ):
        """
        Initialize the PGVectorStore with database credentials and table details.

        :param db_name: Database name
        :param db_user: Database user
        :param db_password: Database password
        :param db_host: Database host
        :param db_port: Database port
        :param table_name: Name of the table to store vectors
        :param embeddings_size: Size of the embedding vectors
        """
        self.table_name = table_name
        self.engine = engine
        self.SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.embeddings_size = embeddings_size

        self.metadata = MetaData()
        self.table = Table(
            table_name,
            self.metadata,
            Column("id", String, primary_key=True, index=True),
            Column("title", String, index=False),
            Column("content", String, index=False),
            Column("mime_type", String, index=False),
            Column("embedding", Vector(self.embeddings_size)),
            Column("chunk_metadata", JSON, nullable=True),
        )

    async def enable_vector_extension(self) -> None:
        """
        Enable the vector extension if it does not exist.
        """
        async with self.engine.begin() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async def create_table(self) -> None:
        """
        Create the table to store documents and their embeddings.

        :param table_name: Name of the table to be created
        """
        async with self.engine.begin() as session:
            await session.run_sync(self.metadata.create_all)

    async def insert_chunks(self, chunks: list[Chunk], embedding: NDArray[np.float64]) -> None:
        """
        Inserts a document and its embedding into the table.

        :param chunks: List of document chunks, each containing a title, content, and metadata
        :param embedding: Array of embedding vectors corresponding to the document chunks
        """
        data_to_insert = [
            {
                "id": generate_uid(),
                "title": chunk.title,
                "content": chunk.content,
                "embedding": emb,
                "mime_type": chunk.mime_type,
                "chunk_metadata": chunk.metadata,
            }
            for chunk, emb in zip(chunks, embedding)
        ]

        async with self.SessionLocal() as session:
            async with session.begin():
                stmt = insert(self.table)
                await session.execute(stmt, data_to_insert)

    async def get_chunks_by_embedding(
        self,
        embedding: NDArray[np.float64],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[ChunkMatch]:
        """
        Search for the top K most similar documents based on the embedding.

        :param embedding: Embedding vector to search for
        :param top_k: Number of top results to return
        :param filters: Dict of metadata to filter on (optional)
        :return: List of ChunkMatch objects
        """
        async with self.SessionLocal() as session:
            query = select(self.table, (1 - self.table.columns.embedding.cosine_distance(embedding)).label("score"))

            # Apply filters if provided
            if filters:
                conditions = [getattr(self.table.c, key) == value for key, value in filters.items()]
                query = query.where(and_(*conditions))

            query = query.order_by(text("score DESC")).limit(top_k)

            chunks = await session.execute(query)
            results = [
                ChunkMatch(
                    id=chunk.id,
                    title=chunk.title,  # type: ignore[reportCallIssue]
                    content=chunk.content,  # type: ignore[reportCallIssue]
                    embedding=chunk.embedding,
                    mime_type=chunk.mime_type,  # type: ignore[reportCallIssue]
                    score=chunk.score,
                )
                for chunk in chunks
            ]
        return results

    async def get_chunks_by_ids(self, chunk_ids: int | list[int]) -> list[Chunk]:
        """
        Search for document chunks based on a single chunk ID or a list of chunk IDs.

        :param chunk_ids: A single ID or a list of IDs of the chunks to search for
        :return: List of document chunks matching the given IDs
        """
        if isinstance(chunk_ids, int):
            chunk_ids = [chunk_ids]

        if not chunk_ids:
            return []

        async with self.SessionLocal() as session:
            results = await session.execute(select(self.table).where(self.table.columns.id.in_(chunk_ids)))

            chunks = [
                Chunk(
                    title=result.title,
                    content=result.content,
                    mime_type="text/plain",
                    metadata=result.chunk_metadata,
                )
                for result in results
            ]
        return chunks
