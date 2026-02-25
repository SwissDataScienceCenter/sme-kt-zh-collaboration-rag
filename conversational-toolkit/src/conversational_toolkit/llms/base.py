"""
Core LLM abstractions and message data models.

All concrete LLM backends ('OpenAILLM', 'OllamaLLM', 'LocalLLM') implement the
'LLM' ABC. The shared message format ('LLMMessage') is deliberately backend-agnostic
so agents and the controller never need to know which LLM is in use.

'LLMMessage' doubles as the base class for 'AgentAnswer': this lets the streaming
infrastructure pass partial content chunks and fully assembled agent answers
through the same async-generator pipeline without additional wrappers.
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from collections.abc import AsyncGenerator

from pydantic import BaseModel

from conversational_toolkit.tools.base import Tool


class Roles(StrEnum):
    """Conversation roles as used by the OpenAI chat completions API."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    DEVELOPER = "developer"


class Function(BaseModel):
    """The function name and JSON-encoded arguments inside a tool call."""

    name: str
    arguments: str


class ToolCall(BaseModel):
    """A single tool invocation requested by the LLM."""

    id: str
    function: Function
    type: str


class MessageContent(BaseModel):

    type: str
    text: str | None = None
    image_url: str | None = None


class LLMMessage(BaseModel):
    """
    A single message in a conversation sent to or received from an LLM.

    'tool_calls' is populated when the assistant requests one or more tool
    invocations. 'tool_call_id' and 'name' are set on the follow-up TOOL role
    message that carries the tool result back to the model.
    """

    content: list[MessageContent]
    role: Roles = Roles.ASSISTANT
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class LLM(ABC):
    """
    Abstract base class for language model backends.

    Concrete implementations adapt a specific API client (OpenAI, Ollama, a
    local OpenAI-compatible server) to a common interface. Tools are stored on
    the LLM instance so that 'ToolAgent' can discover available functions from
    the same object it uses for generation.
    """

    def __init__(self) -> None:
        self.tools: list[Tool] | None = []

    @abstractmethod
    async def generate(self, conversation: list[LLMMessage]) -> LLMMessage:
        """Return a single complete response for the given conversation."""
        pass

    @abstractmethod
    def generate_stream(
        self, conversation: list[LLMMessage]
    ) -> AsyncGenerator[LLMMessage, None]:
        """Yield response chunks as they arrive from the model."""
        pass
