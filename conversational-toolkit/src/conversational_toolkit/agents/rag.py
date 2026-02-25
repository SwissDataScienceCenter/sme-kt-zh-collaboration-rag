"""
Retrieval-Augmented Generation (RAG) agent.

'RAG' combines document retrieval with language model generation. Before calling
the LLM it rewrites the query to be history-independent, optionally expands it
into multiple search queries, retrieves relevant chunks from all configured
retrievers, merges the ranked results via Reciprocal Rank Fusion, and injects
the sources into the LLM prompt using XML tags.
"""

from typing import Any, AsyncGenerator

from conversational_toolkit.agents.base import Agent, AgentAnswer, QueryWithContext
from conversational_toolkit.llms.base import LLM, LLMMessage, Roles
from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.utils.retriever import (
    build_query_with_chunks,
    make_query_standalone,
    query_expansion,
    reciprocal_rank_fusion,
)
from conversational_toolkit.vectorstores.base import ChunkRecord


class RAG(Agent):
    """
    RAG agent that retrieves document chunks before generating an answer.

    Attributes:
        utility_llm: A (typically cheaper) LLM used for query rewriting and
            expansion. Kept separate so a fast model can handle preprocessing
            while a more capable model handles generation.
        retrievers: One or more retrievers queried in parallel. Their results are
            merged with Reciprocal Rank Fusion before being passed to the LLM.
        number_query_expansion: Number of additional search queries to generate
            from the original query. Set to 0 to disable expansion.
    """

    def __init__(
        self,
        llm: LLM,
        utility_llm: LLM,
        retrievers: list[Retriever[Any]],
        system_prompt: str,
        description: str = "",
        number_query_expansion: int = 0,
    ):
        super().__init__(system_prompt, llm, description)
        self.description = description
        self.llm = llm
        self.utility_llm = utility_llm
        self.retrievers = retrievers
        self.number_query_expansion = number_query_expansion

    async def answer_stream(self, query_with_context: QueryWithContext) -> AsyncGenerator[AgentAnswer, None]:
        query = query_with_context.query
        history = query_with_context.history

        if len(history) > 0:
            query = await make_query_standalone(self.utility_llm, history, query)
        if self.number_query_expansion > 0:
            queries = await query_expansion(query, self.utility_llm, self.number_query_expansion)
        else:
            queries = [query]

        sources: list[ChunkRecord] = []
        for retriever in self.retrievers:
            retrieved = [await retriever.retrieve(q) for q in queries]
            if retrieved:
                sources += reciprocal_rank_fusion(retrieved)[: retriever.top_k]

        response_stream = self.llm.generate_stream(
            [
                LLMMessage(role=Roles.SYSTEM, content=self.system_prompt),
                *history,
                LLMMessage(role=Roles.USER, content=build_query_with_chunks(query, sources)),
            ]
        )

        content = ""
        async for response_chunk in response_stream:
            if response_chunk.content:
                content += response_chunk.content
                answer = await self._answer_post_processing(
                    AgentAnswer(content=content, role=Roles.ASSISTANT, sources=sources)
                )
                if answer:
                    yield answer
