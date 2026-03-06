# Conversational Toolkit

A modular Python library for building production-ready conversational AI applications. It provides pluggable abstractions for LLMs, embeddings, vector stores,
document chunkers, agents, and a REST API layer, all wired together through a central controller that manages conversation history, streaming, and persistence.

The toolkit pairs with [Conversational Toolkit Frontend](https://gitlab.datascience.ch/industry/common/conversational-toolkit-frontend) for a complete
out-of-the-box chat interface. It can also be used standalone or headlessly.

---

## Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules](#modules)
    - [Agents](#agents)
    - [LLMs](#llms)
    - [Embeddings](#embeddings)
    - [Chunkers](#chunkers)
    - [Vector Stores](#vector-stores)
    - [Evaluation](#evaluation)
    - [Retrievers](#retrievers)
    - [Tools](#tools)
    - [Conversation Database](#conversation-database)
    - [Authentication](#authentication)
    - [API Server](#api-server)
- [Extending the Toolkit](#extending-the-toolkit)
- [API Reference](#api-reference)
- [Contributing](#contributing)

---

## Architecture

```
Documents
    |
    v
[Chunker]  ──>  [EmbeddingsModel]  ──>  [VectorStore]
                                              |
                                         [Retriever]
                                              |
User Query  ──>  [Agent]  <──────────────────+
                    |
                [LLM]  <──  [Tools]
                    |
                [Controller]
                    |
              [FastAPI App]  ──>  Client
```

Every component in the diagram is an abstract base class with multiple concrete implementations. You pick the combination that fits your stack and wire them
together through `ConversationalToolkitController`.

### Component map

| Component         | ABC                    | Implementations                                                                                                 |
|-------------------|------------------------|-----------------------------------------------------------------------------------------------------------------|
| Language model    | `LLM`                  | `OpenAILLM`, `OllamaLLM`, `LocalLLM`                                                                            |
| Embeddings        | `EmbeddingsModel`      | `OpenAIEmbeddings`, `SentenceTransformerEmbeddings`                                                             |
| Vector store      | `VectorStore`          | `ChromaDBVectorStore`, `PGVectorStore`                                                                          |
| Retriever         | `Retriever[T]`         | `VectorStoreRetriever`, `BM25Retriever`, `HybridRetriever`, `RerankingRetriever`                                |
| Evaluation metric | `Metric`               | `HitRate`, `MRR`, `PrecisionAtK`, `RecallAtK`, `NDCGAtK`, `Faithfulness`, `AnswerRelevance`, `ContextRelevance` |
| Agent             | `Agent`                | `RAG`, `ToolAgent`, `Router`                                                                                    |
| Tool              | `Tool`                 | `RetrieverTool`, `EmbeddingsTool`                                                                               |
| Chunker           | `Chunker`              | `PDFChunker`, `ExcelChunker`, `JSONLinesChunker`                                                                |
| Auth              | `AuthProvider`         | `SessionCookieProvider`, `PasscodeProvider`                                                                     |
| Conversations     | `ConversationDatabase` | `InMemoryConversationDatabase`, `PostgreSQLConversationDatabase`                                                |
| Messages          | `MessageDatabase`      | `InMemoryMessageDatabase`, `PostgreSQLMessageDatabase`                                                          |
| Reactions         | `ReactionDatabase`     | `InMemoryReactionDatabase`, `PostgreSQLReactionDatabase`                                                        |
| Sources           | `SourceDatabase`       | `InMemorySourceDatabase`, `PostgreSQLSourceDatabase`                                                            |
| Users             | `UserDatabase`         | `InMemoryUserDatabase`, `PostgreSQLUserDatabase`                                                                |

---

## Installation

Install from the local path (recommended for development):

```sh
pip install -e ./conversational-toolkit
```

Or from a Git tag:

```sh
pip install git+ssh://git@gitlab.datascience.ch/industry/common/conversational-toolkit.git
```

All document processing, retrieval, and evaluation dependencies (`markitdown`, `openpyxl`, `rank-bm25`, `ragas`) are included in the standard install — no
extras are required.

---

## Quick Start

The following sets up a RAG application backed by ChromaDB and in-memory conversation storage, exposed as a FastAPI app.

```python
from conversational_toolkit.agents.rag import RAG
from conversational_toolkit.api.server import create_app
from conversational_toolkit.conversation_database.controller import ConversationalToolkitController
from conversational_toolkit.conversation_database.in_memory.conversation import InMemoryConversationDatabase
from conversational_toolkit.conversation_database.in_memory.message import InMemoryMessageDatabase
from conversational_toolkit.conversation_database.in_memory.reactions import InMemoryReactionDatabase
from conversational_toolkit.conversation_database.in_memory.source import InMemorySourceDatabase
from conversational_toolkit.conversation_database.in_memory.user import InMemoryUserDatabase
from conversational_toolkit.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from conversational_toolkit.llms.openai import OpenAILLM
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore

embedding_model = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = ChromaDBVectorStore("chunks.db")

agent = RAG(
    llm=OpenAILLM(),
    utility_llm=OpenAILLM(model_name="gpt-4o-mini"),
    system_prompt="You are a helpful assistant.",
    retrievers=[VectorStoreRetriever(embedding_model, vector_store, top_k=5)],
)

controller = ConversationalToolkitController(
    conversation_db=InMemoryConversationDatabase("conversations.json"),
    message_db=InMemoryMessageDatabase("messages.json"),
    reaction_db=InMemoryReactionDatabase("reactions.json"),
    source_db=InMemorySourceDatabase("sources.json"),
    user_db=InMemoryUserDatabase("users.json"),
    agent=agent,
)

app = create_app(controller)
```

Run with uvicorn:

```sh
uvicorn myapp:app --reload
```

See the `examples/` directory for more complete setups including tool-calling agents and passcode authentication.

---

## Modules

### Agents

Agents are the reasoning core. Every agent implements `answer_stream`, which yields `AgentAnswer` objects as the response is generated. Use `answer` for a
non-streaming version.

#### `RAG` — Retrieval-Augmented Generation

The standard choice for document Q&A. On each request it:

1. Rewrites the query to be history-independent (using `utility_llm`).
2. Optionally expands the query into multiple search queries.
3. Retrieves chunks from all configured retrievers.
4. Merges the results with Reciprocal Rank Fusion.
5. Injects the sources into the LLM prompt and streams the response.

```python
from conversational_toolkit.agents.rag import RAG

agent = RAG(
    llm=OpenAILLM(),
    utility_llm=OpenAILLM(model_name="gpt-4o-mini"),
    retrievers=[retriever],
    system_prompt="Answer based on the provided sources.",
    number_query_expansion=2,  # generate 2 additional search queries
)
```

#### `ToolAgent` — ReAct-style agentic loop

Lets the LLM call tools iteratively until it has enough information to answer. Tools are attached to the LLM instance.

```python
from conversational_toolkit.agents.tool_agent import ToolAgent

agent = ToolAgent(
    llm=OllamaLLM(tools=[retriever_tool]),
    system_prompt="Use the retriever tool to find relevant information.",
    max_steps=5,
)
```

#### `Router` — Multi-agent routing

Classifies the query with an LLM and delegates to one of several registered sub-agents based on their `description`.

```python
from conversational_toolkit.agents.router import Router

agent = Router(
    llm=OpenAILLM(),
    agents=[rag_agent, tool_agent],  # each agent must have a description set
)
```

---

### LLMs

All LLMs implement `generate` (returns a single `LLMMessage`) and `generate_stream` (async generator of partial `LLMMessage` chunks).

| Class       | Backend                        | Notes                                             |
|-------------|--------------------------------|---------------------------------------------------|
| `OpenAILLM` | OpenAI API                     | Supports tool calling, JSON mode, response format |
| `OllamaLLM` | Ollama (local)                 | Supports tool calling, JSON format                |
| `LocalLLM`  | Any OpenAI-compatible endpoint | Minimal streaming (wraps `generate`)              |

```python
from conversational_toolkit.llms.openai import OpenAILLM
from conversational_toolkit.llms.ollama import OllamaLLM

llm = OpenAILLM(model_name="gpt-4o", temperature=0.3, seed=42)
llm = OllamaLLM(model_name="llama3", base_url="http://localhost:11434")
```

---

### Embeddings

| Class                           | Backend                             |
|---------------------------------|-------------------------------------|
| `OpenAIEmbeddings`              | OpenAI Embeddings API               |
| `SentenceTransformerEmbeddings` | Local `sentence-transformers` model |

```python
from conversational_toolkit.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from conversational_toolkit.embeddings.openai import OpenAIEmbeddings

embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = OpenAIEmbeddings(model_name="text-embedding-3-small")
```

`get_embeddings` accepts a single string or a list and returns a `numpy` array of shape `(n, embedding_size)`.

---

### Chunkers

Chunkers convert raw files into `Chunk` objects ready for embedding and storage.

#### `PDFChunker`

Splits PDFs into chunks by Markdown header hierarchy. Supports two conversion engines:

```python
from conversational_toolkit.chunking.pdf_chunker import PDFChunker, MarkdownConverterEngine

chunker = PDFChunker()
chunks = chunker.make_chunks("document.pdf")
chunks = chunker.make_chunks("document.pdf", engine=MarkdownConverterEngine.MARKITDOWN)
chunks = chunker.make_chunks("document.pdf", write_images=True, image_path="./images")
```

#### `ExcelChunker`

Produces one chunk per non-empty sheet, formatted as a Markdown table.

```python
from conversational_toolkit.chunking.excel_chunker import ExcelChunker

chunks = ExcelChunker().make_chunks("data.xlsx")
```

#### `JSONLinesChunker`

Parses `.jsonl` files where each line is a JSON object.

```python
from conversational_toolkit.chunking.jsonlines_chunker import JSONLinesChunker

chunks = JSONLinesChunker().make_chunks("data.jsonl", title_key="title", content_key="body", source_key="url")
```

---

### Vector Stores

Vector stores persist chunks with their embeddings and support similarity search.

#### `ChromaDBVectorStore`

Uses a local persistent ChromaDB collection.

```python
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore

store = ChromaDBVectorStore(path="./chroma_db", collection_name="docs")
```

#### `PGVectorStore`

Uses PostgreSQL with the `pgvector` extension.

```python
from conversational_toolkit.vectorstores.postgres import PGVectorStore

store = PGVectorStore(
    connection_string="postgresql+asyncpg://user:pass@localhost/db",
    table_name="embeddings",
    embeddings_size=384,
)
await store.enable_vector_extension()
await store.create_table()
```

**Inserting chunks:**

```python
embeddings = await embedding_model.get_embeddings([c.content for c in chunks])
await store.insert_chunks(chunks, embeddings)
```

### Retrievers

Retrievers accept a natural-language query and return a ranked list of `ChunkMatch` objects. All four implementations are composable: a `BM25Retriever` and a
`VectorStoreRetriever` can be combined inside a `HybridRetriever`, whose output can in turn be wrapped in a `RerankingRetriever`.

#### `VectorStoreRetriever`

Embeds the query with an `EmbeddingsModel` and searches the vector store by cosine similarity.

```python
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever

retriever = VectorStoreRetriever(
    embedding_model=embedding_model,
    vector_store=store,
    top_k=5,
)
```

#### `BM25Retriever`

Keyword-based retrieval using the BM25 Okapi ranking function (via `rank-bm25`). The corpus is indexed in memory at construction time, so retrieval has no I/O
overhead. Takes a list of `ChunkRecord` objects (chunks that already have an ID from the vector store).

```python
from conversational_toolkit.retriever.bm25_retriever import BM25Retriever

# corpus = list of ChunkRecord from your vector store
retriever = BM25Retriever(corpus=corpus, top_k=10)
```

BM25 excels at exact keyword matches and rare terms that embedding models may generalise over. Its main limitation is vocabulary mismatch: it cannot handle
synonyms or paraphrases that share no words with the query.

#### `HybridRetriever`

Runs multiple sub-retrievers in parallel and merges their results with Reciprocal Rank Fusion (RRF). RRF is robust to score-scale differences between
retrievers (BM25 scores and cosine similarities are not comparable), making it the standard choice for combining lexical and semantic results.

```python
from conversational_toolkit.retriever.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(
    retrievers=[bm25_retriever, vectorstore_retriever],
    top_k=5,
    rrf_k=60,  # RRF damping constant, default 60 from the original paper
)
```

The `score` field on each returned `ChunkMatch` is the summed RRF score across all retrievers that returned that chunk. Chunks appearing in multiple retriever
result lists receive a higher score.

#### `RerankingRetriever`

Two-stage retriever: fetches a larger candidate pool from a base retriever, then uses an LLM to re-order the candidates by relevance and returns the final
`top_k`. Useful when the base retriever retrieves the right documents but ranks them suboptimally.

Configure the base retriever with a large `top_k` (the candidate pool) and set `RerankingRetriever.top_k` to the final number you want. These two values are
intentionally separate.

```python
from conversational_toolkit.retriever.reranking_retriever import RerankingRetriever

# candidate_retriever.top_k should equal the candidate pool size (e.g. 20)
candidate_retriever = VectorStoreRetriever(embedding_model, store, top_k=20)

retriever = RerankingRetriever(
    retriever=candidate_retriever,
    llm=OpenAILLM(model_name="gpt-4o-mini"),  # a fast, cheap model is sufficient
    top_k=5,
)
```

If the LLM call fails or returns invalid JSON, the retriever falls back to the original ranking from the base retriever — the pipeline never breaks.

#### Combining retrievers

A typical high-quality setup for production:

```python
from conversational_toolkit.retriever.bm25_retriever import BM25Retriever
from conversational_toolkit.retriever.hybrid_retriever import HybridRetriever
from conversational_toolkit.retriever.reranking_retriever import RerankingRetriever
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever

semantic = VectorStoreRetriever(embedding_model, store, top_k=15)
lexical = BM25Retriever(corpus, top_k=15)
hybrid = HybridRetriever([semantic, lexical], top_k=20)
final = RerankingRetriever(hybrid, llm=OpenAILLM(model_name="gpt-4o-mini"), top_k=5)
```

#### On graph-based retrievers

Graph-based retrieval traverses a knowledge graph of entities and relationships rather than a flat list of chunks. It is a good fit for domains with explicit,
structured relationships — legal case citations, org charts, technical documentation cross-references, or scientific literature networks.

For this general-purpose toolkit, graph retrieval is not included because it requires significant additional infrastructure: a graph database (e.g. Neo4j), an
entity-extraction pipeline during ingestion, and graph-traversal query logic at retrieval time. If your domain has structured entity relationships, a
`GraphRetriever` can be added by implementing the `Retriever` ABC and connecting it to your graph backend. The `HybridRetriever` then lets you combine it with
lexical and semantic retrievers without any changes to the rest of the pipeline.

---

### Tools

Tools are called by `ToolAgent` during its agentic loop. Each tool exposes a JSON schema to the LLM and an async `call` method.

#### `RetrieverTool`

Wraps a retriever as a callable tool. The query can optionally be expanded or reformulated before retrieval.

```python
from conversational_toolkit.tools.retriever import RetrieverTool

tool = RetrieverTool(
    name="document_search",
    description="Search company documents for relevant information.",
    retriever=retriever,
    llm=utility_llm,
    parameters={"type": "object", "properties": {}, "required": []},
    number_query_expansion=1,
)
```

Sources returned by a `RetrieverTool` are automatically surfaced in the `AgentAnswer`.

#### `EmbeddingsTool`

Exposes an embeddings model as a callable tool for custom retrieval logic.

---

### Conversation Database

The conversation database layer consists of five independent repositories (`ConversationDatabase`, `MessageDatabase`, `ReactionDatabase`, `SourceDatabase`,
`UserDatabase`), each available in two implementations.

#### In-memory (JSON files)

Good for local development and prototyping. Data is persisted to JSON files and reloaded on startup.

```python
from conversational_toolkit.conversation_database.in_memory.conversation import InMemoryConversationDatabase

db = InMemoryConversationDatabase("conversations.json")
```

#### PostgreSQL

Async SQLAlchemy with connection pooling.

```python
from conversational_toolkit.conversation_database.postgres.conversation import PostgreSQLConversationDatabase

db = PostgreSQLConversationDatabase(connection_string="postgresql+asyncpg://user:pass@localhost/db")
```

All five PostgreSQL implementations share a single `AsyncEngine` and the same `Base` declarative class, so a single `async_engine.begin()` call creates all
tables.

---

### Authentication

`AuthProvider` integrates with FastAPI to authenticate every request and resolve a user ID.

#### `SessionCookieProvider`

Issues JWT tokens stored in an `HttpOnly` cookie. Registers a `/auth/refresh` endpoint.

```python
from conversational_toolkit.api.auth.session_cookie_provider import SessionCookieProvider

auth = SessionCookieProvider(
    controller=controller,
    secret_key="your-secret-key",
    algorithm="HS256",
)
```

#### `PasscodeProvider`

Wraps another `AuthProvider` and adds a passcode gate via middleware. Users must first visit `/passcode` to set the passcode cookie before they can access the
app.

```python
from conversational_toolkit.api.auth.passcode_provider import PasscodeProvider

auth = PasscodeProvider(auth_provider=session_auth, passcode="secret123")
```

---

### API Server

`create_app` returns a configured `FastAPI` application with CORS, authentication, and all API routes registered.

```python
from conversational_toolkit.api.server import create_app

app = create_app(
    controller=controller,
    auth_provider=auth,  # optional, defaults to SessionCookieProvider
    frontend_dist_path="./dist",  # optional, serve a built frontend
    allowed_origins=["http://localhost:3000"],
)
```

#### REST endpoints

| Method   | Path                                                  | Description                                                      |
|----------|-------------------------------------------------------|------------------------------------------------------------------|
| `POST`   | `/api/v1/messages`                                    | Send a message, receive the final response                       |
| `POST`   | `/api/v1/messages/stream`                             | Send a message, receive a streaming response                     |
| `GET`    | `/api/v1/conversations`                               | List conversations for the current user                          |
| `GET`    | `/api/v1/conversations/{id}`                          | Get a conversation with all messages                             |
| `PUT`    | `/api/v1/conversations/{id}`                          | Update conversation title                                        |
| `DELETE` | `/api/v1/conversations/{id}`                          | Delete a conversation (cascades to messages, sources, reactions) |
| `GET`    | `/api/v1/conversations/{id}/messages`                 | Get messages with sources and reactions                          |
| `POST`   | `/api/v1/conversations/{id}/messages/{mid}/reactions` | Add or replace a reaction on a message                           |
| `GET`    | `/auth/refresh`                                       | Refresh auth token (registered by `AuthProvider`)                |

---

## Extending the Toolkit

Every major component is an ABC. To add a new implementation, subclass the relevant ABC and override the abstract methods.

### Custom LLM

```python
from collections.abc import AsyncGenerator
from conversational_toolkit.llms.base import LLM, LLMMessage


class MyLLM(LLM):
    async def generate(self, conversation: list[LLMMessage]) -> LLMMessage:
        ...

    async def generate_stream(self, conversation: list[LLMMessage]) -> AsyncGenerator[LLMMessage, None]:
        ...
        yield LLMMessage(content="partial response")
```

### Custom Agent

```python
from collections.abc import AsyncGenerator
from conversational_toolkit.agents.base import Agent, AgentAnswer, QueryWithContext


class MyAgent(Agent):
    async def answer_stream(self, query_with_context: QueryWithContext) -> AsyncGenerator[AgentAnswer, None]:
        ...
        yield AgentAnswer(content="my response", sources=[])
```

### Custom Tool

```python
from conversational_toolkit.tools.base import Tool


class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {"type": "object", "properties": {}, "required": []}

    async def call(self, args: dict) -> dict:
        return {"result": "done"}
```

### Custom Retriever

```python
from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkMatch


class MyRetriever(Retriever[ChunkMatch]):
    async def retrieve(self, query: str) -> list[ChunkMatch]:
        ...
```

Pass it directly to `RAG`, `HybridRetriever`, or `RerankingRetriever` — all accept any `Retriever` subclass.

### Custom Database Backend

Implement all five database ABCs and pass them to `ConversationalToolkitController`. See the `in_memory/` implementations for a minimal reference.

---

## Contributing

We use [Semantic Versioning](https://semver.org/). To bump the version, use the `Makefile` targets which invoke `bump2version`:

```sh
make major   # x.0.0
make minor   # 0.x.0
make patch   # 0.0.x
```

Code style is enforced with `ruff` and type-checked with `mypy`:

```sh
ruff check src/
mypy src/
```
