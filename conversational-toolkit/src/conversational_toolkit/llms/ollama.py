import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Literal

from loguru import logger
from ollama import AsyncClient, ChatResponse

from conversational_toolkit.llms.base import LLM, LLMMessage, ToolCall, Roles, Function, MessageContent
from conversational_toolkit.tools.base import Tool
from conversational_toolkit.utils.metadata_provider import MetadataProvider


def message_to_ollama(msg: LLMMessage) -> dict[str, Any]:
    message: dict[str, Any] = {
        "role": msg.role,
    }

    # Convert MessageContent list to Ollama format
    if len(msg.content) == 1 and msg.content[0].type == "text":
        message["content"] = msg.content[0].text or ""
    else:
        message["content"] = [
            {"type": c.type, "text": c.text} if c.type == "text" else {"type": "image_url", "image_url": c.image_url}
            for c in msg.content
        ]

    if msg.name:
        message["name"] = msg.name

    if msg.role == Roles.TOOL and msg.tool_call_id:
        message["tool_call_id"] = msg.tool_call_id

    if msg.role == Roles.ASSISTANT and msg.tool_calls:
        message["tool_calls"] = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                },
            }
            for tc in msg.tool_calls
        ]

    return message


class OllamaLLM(LLM):
    def __init__(
        self,
        temperature: float = 0.5,
        seed: int = 42,
        tools: list[Tool] | None = None,
        tool_choice: str | None = None,
        model_name: str = "llama3.1",
        response_format: Literal["json"] | None = None,
        host: str | None = None,
    ):
        super().__init__()
        self.client = AsyncClient(host=host)
        self.model = model_name
        self.temperature = temperature
        self.seed = seed
        self.tools = tools
        self.tool_choice = tool_choice
        self.response_format: Literal["json"] | None = response_format
        logger.debug(
            f"Ollama LLM loaded: {model_name}; temperature: {temperature}; seed: {seed}; tools: {tools}; response_format: {response_format}"
        )

    async def generate(self, conversation: list[LLMMessage]) -> LLMMessage:
        completion: ChatResponse = await self.client.chat(
            model=self.model,
            messages=[message_to_ollama(msg) for msg in conversation],
            format=self.response_format,
            tools=[tool.json_schema() for tool in self.tools] if self.tools else None,
            stream=False,
        )
        logger.debug(f"Completion: {completion}")
        return LLMMessage(
            content=[MessageContent(type="text", text=completion.message.content or "")],
            role=Roles(completion.message.role),
            tool_calls=[
                ToolCall(
                    id=str(i),
                    function=Function(
                        name=tc.function.name,
                        arguments=json.dumps(tc.function.arguments),
                    ),
                    type="function",
                )
                for i, tc in enumerate(completion.message.tool_calls)
            ]
            if completion.message.tool_calls
            else [],
        )

    async def generate_stream(self, conversation: list[LLMMessage]) -> AsyncGenerator[LLMMessage, None]:
        response: AsyncIterator[ChatResponse] = await self.client.chat(
            model=self.model,
            messages=[message_to_ollama(msg) for msg in conversation],
            format=self.response_format,
            tools=[tool.json_schema() for tool in self.tools] if self.tools else None,
            stream=True,
        )

        last_tool_call_sent = -1
        last_chunk: ChatResponse | None = None
        async for chunk in response:
            logger.trace(chunk)
            last_chunk = chunk
            if chunk.message.content:
                yield LLMMessage(content=[MessageContent(type="text", text=chunk.message.content)])
            if chunk.message.tool_calls:
                for index, tool_call in enumerate(chunk.message.tool_calls):
                    if index > last_tool_call_sent:
                        yield LLMMessage(
                            content=[],
                            tool_calls=[
                                ToolCall(
                                    id=str(index),
                                    function=Function(
                                        name=tool_call.function.name,
                                        arguments=json.dumps(tool_call.function.arguments),
                                    ),
                                    type="function",
                                )
                            ],
                        )
                        last_tool_call_sent = index

        if last_chunk is not None:
            MetadataProvider.add_metadata({"model": last_chunk.model})
