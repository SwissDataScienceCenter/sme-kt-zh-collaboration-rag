from collections.abc import AsyncGenerator
from typing import Any, Literal, cast

from loguru import logger
from openai import AsyncOpenAI, omit
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    completion_create_params,
)

from conversational_toolkit.llms.base import (
    LLM,
    LLMMessage,
    ToolCall,
    Roles,
    Function,
    MessageContent,
)
from conversational_toolkit.tools.base import Tool
from conversational_toolkit.utils.metadata_provider import MetadataProvider


def message_to_openai(msg: LLMMessage) -> ChatCompletionMessageParam:
    # TODO: Currently, assumes images are always base64
    # TODO: Currently, always interpreted as PNG, to change

    message: dict[str, Any] = {
        "role": msg.role.value,
    }
    message["content"] = []

    for content in msg.content:
        if "text" in content.type and content.text is not None:
            message["content"].append({"type": "text", "text": content.text})
        elif "image" in content.type and content.image_url is not None:
            message["content"].append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{content.image_url}"},
                }
            )

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
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]

    return cast(ChatCompletionMessageParam, message)


class OpenAILLM(LLM):
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.5,
        seed: int = 42,
        tools: list[Tool] | None = None,
        tool_choice: Literal["none", "auto", "required"] | None = None,
        response_format: completion_create_params.ResponseFormat | None = None,
        openai_api_key: str | None = None,
    ):
        # TODO: Currently only supports text output

        super().__init__()
        if response_format is None:
            response_format = {"type": "text"}

        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model_name
        self.temperature = temperature
        self.seed = seed
        self.tools = tools
        self.tool_choice: Literal["none", "auto", "required"] | None = tool_choice
        self.response_format: completion_create_params.ResponseFormat = response_format
        logger.debug(
            f"OpenAI LLM loaded: {model_name}; temperature: {temperature}; seed: {seed}; tools: {tools}; tool_choice: {tool_choice}; response_format: {response_format}"
        )

    async def generate(self, conversation: list[LLMMessage]) -> LLMMessage:
        """
        Generate a completion for the given conversation.
        Args:
            conversation:

        Returns:

        """

        messages_as_openai = [message_to_openai(msg) for msg in conversation]

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages_as_openai,
            temperature=self.temperature,
            seed=self.seed,
            tools=(
                cast(
                    list[ChatCompletionToolParam],
                    [tool.json_schema() for tool in self.tools],
                )
                if self.tools
                else omit
            ),
            tool_choice=self.tool_choice if self.tool_choice is not None else omit,
            response_format=self.response_format,
        )
        logger.debug(f"Completion: {completion}")
        logger.info(f"LLM Usage: {completion.usage}")

        MetadataProvider.add_metadata(
            {
                "model": completion.model,
                "usage": completion.usage.to_dict() if completion.usage else {},
            }
        )

        return LLMMessage(
            content=[
                MessageContent(
                    type="text",
                    text=completion.choices[0].message.content or "",
                )
            ],
            role=Roles(completion.choices[0].message.role),
            tool_calls=(
                [
                    ToolCall(
                        id=tc.id,
                        function=Function(name=tc.function.name, arguments=tc.function.arguments),  # type: ignore[union-attr]
                        type="function",
                    )
                    for tc in completion.choices[0].message.tool_calls
                ]
                if completion.choices[0].message.tool_calls
                else []
            ),
        )

    @staticmethod
    def _update_tool_call_from_chunk(tool_call: ToolCall, tool_call_chunk: Any) -> None:
        if tool_call_chunk.id:
            tool_call.id += tool_call_chunk.id
        if tool_call_chunk.function:
            if tool_call_chunk.function.name:
                tool_call.function.name += tool_call_chunk.function.name
            if tool_call_chunk.function.arguments:
                tool_call.function.arguments += tool_call_chunk.function.arguments

    async def generate_stream(
        self, conversation: list[LLMMessage]
    ) -> AsyncGenerator[LLMMessage, None]:

        messages_as_openai = [message_to_openai(msg) for msg in conversation]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages_as_openai,
            temperature=self.temperature,
            seed=self.seed,
            tools=(
                cast(
                    list[ChatCompletionToolParam],
                    [tool.json_schema() for tool in self.tools],
                )
                if self.tools
                else omit
            ),
            tool_choice=self.tool_choice if self.tool_choice is not None else omit,
            stream=True,
            response_format=self.response_format,
            stream_options={"include_usage": True},
        )

        parsed_tool_calls: list[ToolCall] = []
        last_chunk = None

        async for chunk in response:
            last_chunk = chunk
            if not chunk.choices:  # Last chunk has empty choices list
                continue
            if chunk.choices[0].delta.content:
                yield LLMMessage(
                    content=[
                        MessageContent(
                            type="text",
                            text=chunk.choices[0].delta.content,
                        )
                    ],
                )
            if chunk.choices[0].delta.tool_calls:
                tool_call_chunk_list = chunk.choices[0].delta.tool_calls
                for tool_call_chunk in tool_call_chunk_list:
                    if len(parsed_tool_calls) <= tool_call_chunk.index:
                        if len(parsed_tool_calls) > 0:
                            yield LLMMessage(
                                tool_calls=[parsed_tool_calls[-1]],
                            )
                        parsed_tool_calls.append(
                            ToolCall(
                                id="",
                                type="function",
                                function=Function(name="", arguments=""),
                            )
                        )
                    tool_call = parsed_tool_calls[tool_call_chunk.index]
                    self._update_tool_call_from_chunk(tool_call, tool_call_chunk)

        if last_chunk is not None:
            MetadataProvider.add_metadata(
                {
                    "model": last_chunk.model,
                    "usage": last_chunk.usage.to_dict() if last_chunk.usage else {},
                }
            )

        if parsed_tool_calls:
            yield LLMMessage(
                tool_calls=[parsed_tool_calls[-1]],
            )
