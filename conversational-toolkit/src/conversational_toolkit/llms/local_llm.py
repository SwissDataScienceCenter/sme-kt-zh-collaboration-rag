from typing import AsyncGenerator

from loguru import logger
from conversational_toolkit.llms.base import LLM, LLMMessage, Roles
from openai import AsyncOpenAI


class LocalLLM(LLM):
    def __init__(
        self,
        model_name: str = "bartowski/gemma-2-9b-it-GGUF",
        temperature: float = 0.5,
        seed: int = 42,
        base_url: str = "",
        api_key: str = "",
    ):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model_name
        self.temperature = temperature
        self.seed = seed
        logger.debug(f"Local LLM loaded: {model_name}; temperature: {temperature}; seed: {seed}")

    async def generate(self, conversation: list[LLMMessage]) -> LLMMessage:
        """Generate a completion for the given conversation."""
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=conversation,  # type: ignore
            temperature=self.temperature,
            seed=self.seed,
        )
        logger.debug(f"Completion: {completion}")

        return LLMMessage(
            content=completion.choices[0].message.content or "",
            role=Roles(completion.choices[0].message.role),
            tool_calls=completion.choices[0].message.tool_calls,  # type: ignore
        )

    async def generate_stream(self, conversation: list[LLMMessage]) -> AsyncGenerator[LLMMessage, None]:
        msg = await self.generate(conversation)
        yield msg
