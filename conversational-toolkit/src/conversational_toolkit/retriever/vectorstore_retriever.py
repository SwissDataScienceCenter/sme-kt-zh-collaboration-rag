from conversational_toolkit.embeddings.base import EmbeddingsModel
from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import VectorStore, ChunkMatch


class VectorStoreRetriever(Retriever[ChunkMatch]):
    def __init__(
        self, embedding_model: EmbeddingsModel, vector_store: VectorStore, top_k: int
    ):
        super().__init__(top_k)
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        embeddings = await self.embedding_model.get_embeddings(query)
        results = await self.vector_store.get_chunks_by_embedding(
            embeddings[0], self.top_k
        )
        return results


class CompositeVectorStoreRetriever(Retriever[ChunkMatch]):
    # TODO: Should allow in main class to have list as well for top_k

    def __init__(
        self,
        embedding_models: list[EmbeddingsModel],
        vector_stores: list[VectorStore],
        top_k: list[int],
    ):
        super().__init__(top_k=sum(top_k))
        self.embedding_models = embedding_models
        self.vector_stores = vector_stores
        self.top_k_per_retriever = top_k

    async def retrieve(self, query: str) -> list[ChunkMatch]:
        all_results = []
        for embedding_model, vector_store, top_k_tmp in zip(
            self.embedding_models, self.vector_stores, self.top_k_per_retriever
        ):
            embeddings = await embedding_model.get_embeddings(query)
            results = await vector_store.get_chunks_by_embedding(
                embeddings[0], top_k_tmp
            )
            all_results.extend(results)

        return all_results[: self.top_k]
