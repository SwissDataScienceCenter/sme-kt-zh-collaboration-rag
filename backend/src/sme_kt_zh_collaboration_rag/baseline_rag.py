from conversational_toolkit.agents.rag import RAG  # type: ignore[import-untyped]
from conversational_toolkit.agents.base import QueryWithContext  # type: ignore[import-untyped]
from conversational_toolkit.llms.ollama import OllamaLLM  # type: ignore[import-untyped]
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore  # type: ignore[import-untyped]
from conversational_toolkit.chunking.base import Chunk  # type: ignore[import-untyped]
from conversational_toolkit.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)  # type: ignore[import-untyped]
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever  # type: ignore[import-untyped]


def get_docs() -> list[str]:
    return [
        "The KT-ZH SDSC prototyping workshop will kick off on the 23rd of February.",
        "Skiing is the best part about winter.",
        "We will go skiing in Klosters, it will be a lot of fun.",
        "Viktoria is the youngest in the innovation team of SDSC in Zurich.",
    ]


def create_chunks(documents: list[str]) -> list[Chunk]:
    chunks: list[Chunk] = []

    for i, doc in enumerate(documents):
        chunk = Chunk(
            title=f"title{i}",
            content=doc,
            mime_type="text/markdown",
            metadata={},
        )
        chunks.append(chunk)

    return chunks


async def create_chromadb(
    chunks: list[Chunk], embedding_model: SentenceTransformerEmbeddings
) -> ChromaDBVectorStore:
    vector_store = ChromaDBVectorStore(db_path="data_vs.db")
    embeddings = await embedding_model.get_embeddings([c.content for c in chunks])
    await vector_store.insert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )
    return vector_store


async def test_vector_store(
    test_string: str,
    vector_store: ChromaDBVectorStore,
    embedding_model: SentenceTransformerEmbeddings,
    top_k: int = 1,
) -> None:
    vsr = VectorStoreRetriever(  # alternatively can use BM25Retriever (not implemented yet) or create another retriever # TODO which ones
        embedding_model=embedding_model,
        vector_store=vector_store,
        top_k=top_k,
    )
    results = await vsr.retrieve(test_string)
    print(f"Top {top_k} matches: ")
    for result in results:
        match = result.content
        print(match)


async def create_rag(
    embedding_model_name: str,
    top_k: int,
    temperature: float = 0.5,
    seed: int = 42,
):
    embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model_name)
    documents = get_docs()
    chunks = create_chunks(documents=documents)

    vector_store = await create_chromadb(
        chunks=chunks,
        embedding_model=embedding_model,
    )

    await test_vector_store(
        test_string="davos",
        vector_store=vector_store,
        embedding_model=embedding_model,
        top_k=top_k,
    )

    # Different LLM options
    # openai = OpenAILLM(
    #     model_name="gpt-40-mini",
    #     temperature=temperature,
    #     seed=seed,
    #     tools=None,
    #     tool_choice=None,
    #     response_format={"type": "text"},
    #     openai_api_key=os.environ["OPENAI_API_KEY"],
    # )
    ollama = OllamaLLM(
        model_name="mistral-nemo:12b",  # good options: llama3.1:8b, qwen2.5:7b-instruct, qwen3:8b (thinking), mistral-nemo:12b
        temperature=temperature,
        seed=seed,
        tools=None,
        tool_choice=None,
        response_format="",
        host=None,  # use ollama's default http://localhost:11434
    )

    agent = RAG(
        llm=ollama,
        utility_llm=ollama,
        system_prompt="You are a helpful AI assistant specialized in answering question.",
        description="",  # rag description, no functionality
        retrievers=[VectorStoreRetriever(embedding_model, vector_store, 1)],
        number_query_expansion=0,  # optionally expand query into this many queries related to the initial query (in english)
    )

    # preprocess query and rhen retriev
    response = await agent.answer(
        QueryWithContext(
            query="Who is the youngest at SDSC in Zurich?",
            history=[],  # optional, if len(history) > 0 then the query will be reformulated to be standalone/independent of history
        )
    )

    print("RAG response: ", response.content)
    print("RAG sources: ", response.sources)


if __name__ == "__main__":
    # asyncio.run(
    #     create_rag(
    #         embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    #         top_k=1,
    #     )
    # )
    print("hello docker!!!")
