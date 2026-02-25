import loguru
from textwrap import dedent
from typing import Sequence

from conversational_toolkit.llms.base import LLM, LLMMessage, Roles
from conversational_toolkit.vectorstores.base import ChunkRecord


async def make_query_standalone(llm: LLM, history: list[LLMMessage], query: str) -> str:
    template_query_standalone = dedent(
        """
        Objective: Your task is to analyze the input query and the provided conversation history. When the user mentions something that was mentioned in the conversation, but not clearly said in the current query, rewrite it.

        Example:

            User Query: How much does it cost?
            Conversation History:
                - User: Can you tell me about the price of the new iPhone?
                - Assistant: The new iPhone costs around $999.
            Reformulated Query: How much does the new iPhone cost?


        Input:

            User Query: {query}
            Conversation History:
                {chat_history}

        Reformulated Query (ONLY the reformulated query, without any explanation):
    """
    )
    chat_history = "\n".join([f"{message.role}: {message.content}" for message in history])

    conversation = [
        LLMMessage(
            role=Roles.SYSTEM,
            content="You are a helpful assistant that transforms a message from a user to be independent from the conversation history given.",
        ),
        LLMMessage(
            role=Roles.USER,
            content=template_query_standalone.format(query=query, chat_history=chat_history),
        ),
    ]
    reformulated_query = (await llm.generate(conversation)).content

    loguru.logger.debug(f"Original query: {query}")
    loguru.logger.debug(f"Reformulated query: {reformulated_query}")

    return reformulated_query


async def query_expansion(query: str, llm: LLM, expansion_number: int = 2) -> list[str]:
    template_query_expansion = """
        Generate multiple search queries related to: {query}, and translate them in english if they are not already in english. Only output {expansion_number} queries in english.
        OUTPUT ({expansion_number} queries):
    """
    conversation = [
        LLMMessage(
            role=Roles.SYSTEM,
            content="You are a focused assistant designed to generate multiple, relevant search queries based solely on a single input query. Your task is to produce a list of these queries in English, without adding any further explanations or information.",
        ),
        LLMMessage(
            role=Roles.USER,
            content=template_query_expansion.format(query=query, expansion_number=expansion_number),
        ),
    ]

    generated_queries = (await llm.generate(conversation)).content.strip().split("\n")

    loguru.logger.debug(f"Original query for expansion: {query}")
    for i, generated_query in enumerate(generated_queries, start=1):
        loguru.logger.debug(f"Generated query {i}: {generated_query}")

    return generated_queries


async def hyde_expansion(query: str, llm: LLM) -> str:
    conversation = [
        LLMMessage(
            role=Roles.SYSTEM,
            content="You are a helpful assistant. Provide an example of answer to the provided query. Only output an hypothetical explanation to the query. Concise, only a few sentences, without any introduction or conclusion.",
        ),
        LLMMessage(role=Roles.USER, content=query),
    ]
    hyde_expansion_message = (await llm.generate(conversation)).content

    loguru.logger.debug(f"Original query for HyDE expansion: {query}")
    loguru.logger.debug(f"HyDE expansion: {hyde_expansion_message}")

    return hyde_expansion_message


def reciprocal_rank_fusion(search_results: Sequence[Sequence[ChunkRecord]], k: int = 60) -> list[ChunkRecord]:
    """
    Applies Reciprocal Rank Fusion (RRF) to a list of search results from different sources.

    Parameters:
    - search_results: A list of tuples where each tuple contains a source name and a ranked list of ChunkRecord objects.
    - k: A constant that dampens the rank influence, default is 60.

    Returns:
    - A list of tuples, each containing a source name and a Chunk object, sorted by the fused score.
    """
    fused_scores = {}
    chunk_map = {}

    for chunks in search_results:
        for rank, chunk in enumerate(chunks, start=1):
            score = float(1 / (k + rank))
            if chunk.id not in fused_scores:
                fused_scores[chunk.id] = score
            else:
                fused_scores[chunk.id] += score
            chunk_map[chunk.id] = chunk

    sorted_results = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)

    return [chunk_map[chunk_id] for chunk_id, _ in sorted_results]


def build_query_with_chunks(user_query: str = "", chunks: list[ChunkRecord] | None = None) -> str:
    """
    Constructs a query string for an LLM, embedding relevant chunk content inside XML tags.

    Parameters:
    - user_query: The original user query string (optional).
    - chunks: List of Chunk objects containing source information and content.

    Returns:
    - A formatted string with the user query (if provided) and relevant sources in XML format.
    """
    if not chunks:
        sources_xml = "No sources found."
    else:
        sources_xml = "\n".join(f'<source id="{chunk.id}">\n{chunk.content}\n</source>' for chunk in chunks)

    return dedent(
        f"""
        User Query: {user_query}\n
        Here are the sources I found for you:
        {sources_xml}
        """
    )
