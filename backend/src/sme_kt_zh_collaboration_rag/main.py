import os
import pathlib
from pathlib import Path
from textwrap import dedent

import uvicorn

from conversational_toolkit.agents.base import AgentAnswer
from conversational_toolkit.agents.rag import RAG
from conversational_toolkit.api.server import create_app
from conversational_toolkit.conversation_database.controller import (
    ConversationalToolkitController,
)
from conversational_toolkit.conversation_database.in_memory.conversation import (
    InMemoryConversationDatabase,
)
from conversational_toolkit.conversation_database.in_memory.message import (
    InMemoryMessageDatabase,
)
from conversational_toolkit.conversation_database.in_memory.reactions import (
    InMemoryReactionDatabase,
)
from conversational_toolkit.conversation_database.in_memory.source import (
    InMemorySourceDatabase,
)
from conversational_toolkit.conversation_database.in_memory.user import (
    InMemoryUserDatabase,
)
from conversational_toolkit.embeddings.openai import OpenAIEmbeddings
from conversational_toolkit.embeddings.qwen_vl import Qwen3VLEmbeddings
from conversational_toolkit.llms.base import MessageContent
from conversational_toolkit.retriever.bm25_retriever import BM25Retriever
from conversational_toolkit.retriever.hybrid_retriever import HybridRetriever
from conversational_toolkit.retriever.vectorstore_retriever import VectorStoreRetriever
from conversational_toolkit.vectorstores.chromadb import ChromaDBVectorStore

from sme_kt_zh_collaboration_rag.feature0_baseline_rag import (
    EMBEDDING_MODEL,
    RETRIEVER_TOP_K,
    build_llm,
)
from sme_kt_zh_collaboration_rag.utils.json import parse_llm_json_stream

BACKEND = os.getenv("BACKEND", "openai")
_secret = pathlib.Path("/secrets/OPENAI_API_KEY")
if "OPENAI_API_KEY" not in os.environ and _secret.exists():
    os.environ["OPENAI_API_KEY"] = _secret.read_text().strip()

_DB_DIR = Path(__file__).parent / "db"
_DB_DIR.mkdir(exist_ok=True)

IMAGE_VS_PATH = _DB_DIR / "vs_image"
TEXT_VS_PATH = _DB_DIR / "vs_text"

SYSTEM_PROMPT = dedent("""
    You are a sustainability compliance assistant for PrimePack AG.
    Answer questions using ONLY the provided sources. If no sources are relevant, say you don't know.
    NEVER use general knowledge unless the user explicitly asks for it.

    RULES (apply in order):
    1. Identify the key entity in the question (product name, supplier, product ID).
    2. Check that this exact entity appears in the retrieved sources.
       If it does NOT appear, respond: "The sources do not contain information about
       [entity]. I cannot answer this question." Do not substitute other products.
    3. Distinguish clearly between:
       VERIFIED — backed by a third-party EPD or independent audit
       CLAIMED  — supplier self-declaration, not independently verified
       MISSING  — not found in sources
    4. Label forward-looking targets (e.g. "carbon neutral by 2025") as targets,
       not as current verified status.
    5. Always cite the source document for each claim.
""").strip()


class CustomRAG(RAG):
    async def _answer_post_processing(self, answer: AgentAnswer) -> AgentAnswer:
        json_answer = parse_llm_json_stream(
            answer.content[0].text if answer.content else ""
        )

        content = json_answer.get("answer", "")
        relevant_source_ids = json_answer.get("used_sources_id", [])
        follow_up_questions = json_answer.get("follow_up_questions", [])
        unique_sources = list({s.id: s for s in answer.sources}.values())
        return AgentAnswer(
            content=[MessageContent(type="text", text=content)],
            sources=[
                source for source in unique_sources if source.id in relevant_source_ids
            ],
            follow_up_questions=follow_up_questions,
        )


json_schema = {
    "type": "object",
    "name": "AnswerSchema",
    "description": "The structured output for the user's answer. This should contain, the answer we will send to the user and all the ids of the relevant sources used.",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the user's question in markdown format. When referencing a supplier or material source, provide a clickable link to the relevant compliance documentation or evidence page.",
        },
        "used_sources_id": {
            "type": "array",
            "description": "List of source IDs used to generate the answer. Do not invent them and give the exact id of the source which was used.",
            "items": {
                "type": "string",
            },
        },
        "follow_up_questions": {
            "type": "array",
            "description": "These are follow-up questions that the USER might want to ask based on the current answer. ONLY add those if there were sources used to generate the answer. Use the sources to identify potential follow-up questions that are directly relevant to the current answer and can help the user dive deeper into the topic if they choose to. If there are no sources used, this should be an empty list.",
            "items": {
                "type": "string",
            },
        },
    },
    "required": ["answer", "used_sources_id", "follow_up_questions"],
    "additionalProperties": False,
}


def build_server():
    text_embedding_model = OpenAIEmbeddings(model_name=EMBEDDING_MODEL)
    image_embedding_model = Qwen3VLEmbeddings()

    text_vs = ChromaDBVectorStore(db_path=str(TEXT_VS_PATH))
    image_vs = ChromaDBVectorStore(db_path=str(IMAGE_VS_PATH))

    hybrid_retriever = HybridRetriever(
        retrievers=[
            VectorStoreRetriever(text_embedding_model, text_vs, top_k=RETRIEVER_TOP_K),
            BM25Retriever(text_vs, top_k=RETRIEVER_TOP_K),
        ],
        top_k=RETRIEVER_TOP_K,
    )

    image_retriever = VectorStoreRetriever(
        image_embedding_model, image_vs, top_k=RETRIEVER_TOP_K
    )

    llm = build_llm(
        backend=BACKEND,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": json_schema,
                "name": "AnswerSchema",
            },
        },
    )
    agent = CustomRAG(
        llm=llm,
        utility_llm=llm,
        system_prompt=SYSTEM_PROMPT,
        retrievers=[hybrid_retriever, image_retriever],
        number_query_expansion=0,
    )

    controller = ConversationalToolkitController(
        conversation_db=InMemoryConversationDatabase(
            str(_DB_DIR / "conversations.json")
        ),
        message_db=InMemoryMessageDatabase(str(_DB_DIR / "messages.json")),
        reaction_db=InMemoryReactionDatabase(str(_DB_DIR / "reactions.json")),
        source_db=InMemorySourceDatabase(str(_DB_DIR / "sources.json")),
        user_db=InMemoryUserDatabase(str(_DB_DIR / "users.json")),
        agent=agent,
    )

    return create_app(controller=controller)


app = build_server()

if __name__ == "__main__":
    uvicorn.run(
        "sme_kt_zh_collaboration_rag.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
    )
