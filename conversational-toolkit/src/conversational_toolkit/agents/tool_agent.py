"""
ReAct-style tool-calling agent.

'ToolAgent' implements an agentic loop where the LLM may call any of the tools attached to 'self.llm.tools'. After each LLM response the agent executes all requested tool calls, appends the results to the conversation, and feeds everything back to the LLM. The loop continues until the model produces a response without tool calls or 'max_steps' is exceeded. Tool results that contain a '_sources' key are automatically collected and surfaced in the final 'AgentAnswer'.
"""

import json
from typing import AsyncGenerator

from loguru import logger

from conversational_toolkit.agents.base import Agent, QueryWithContext, AgentAnswer
from conversational_toolkit.chunking.base import Chunk
from conversational_toolkit.llms.base import Roles, LLMMessage, ToolCall, MessageContent


class ToolAgent(Agent):
    """
    Agent that drives an iterative tool-calling loop (ReAct pattern).

    Tools are registered on 'self.llm' rather than on the agent directly, which keeps the LLM and its callable functions together. Any tool whose response dict contains a '_sources' key will have those sources merged into the streamed 'AgentAnswer', making retrieval tools work transparently within the agentic loop.
    """

    async def answer_stream(self, query_with_context: QueryWithContext) -> AsyncGenerator[AgentAnswer, None]:
        steps = []
        sources: list[Chunk] = []
        messages = [
            LLMMessage(role=Roles.SYSTEM, content=[MessageContent(type="text", text=self.system_prompt)]),
            *query_with_context.history,
            LLMMessage(role=Roles.USER, content=[MessageContent(type="text", text=query_with_context.query)]),
        ]

        while True:
            tool_calls: list[ToolCall] = []
            content = ""
            response_stream = self.llm.generate_stream(messages)
            async for response_chunk in response_stream:
                if response_chunk.content:
                    content += response_chunk.content[0].text or ""
                    answer = await self._answer_post_processing(
                        AgentAnswer(
                            content=[MessageContent(type="text", text=content)],
                            role=Roles.ASSISTANT,
                            sources=sources.copy(),
                        )
                    )
                    if answer:
                        yield answer
                if response_chunk.tool_calls:
                    tool_calls += response_chunk.tool_calls

            steps.append(
                {
                    "content": content,
                    "tool_calls": tool_calls,
                    "role": Roles.ASSISTANT,
                    "function_name": "llm",
                }
            )
            messages.append(
                LLMMessage(
                    role=Roles.ASSISTANT,
                    content=[MessageContent(type="text", text=content)],
                    tool_calls=tool_calls,
                )
            )

            if not tool_calls:
                break

            available_functions = {tool.name: tool.call for tool in self.llm.tools} if self.llm.tools else {}

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = {
                    "_query": query_with_context.query,
                    "_history": query_with_context.history,
                    **json.loads(tool_call.function.arguments),
                }
                function_response = await function_to_call(function_args)
                if "_sources" in function_response:
                    sources += [
                        Chunk(
                            title=chunk.get("title") or "",
                            content=chunk.get("content") or "",
                            mime_type=chunk.get("mime_type") or "",
                            metadata=chunk.get("metadata") or {},
                        )
                        for chunk in function_response.get("_sources", [])
                    ]
                messages.append(self.build_tool_answer(tool_call.id, function_name, function_response))
                steps.append({**function_response, "role": "tool", "function_name": function_name})

            if len(steps) > self.max_steps:
                # TODO: Maybe throw an exception here?
                yield AgentAnswer(
                    content=[MessageContent(type="text", text="Request is too complex to execute")],
                    role=Roles.ASSISTANT,
                )
                break

        logger.debug(steps)
