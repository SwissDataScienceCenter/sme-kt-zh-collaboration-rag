"""
LLM-based query router that delegates to specialised agents.

'Router' uses the LLM to classify an incoming query against the descriptions of all registered agents and then forwards the query to the best-matching one. The routing decision is made in a single LLM call that returns JSON with a chain-of-thought explanation and a category index.
"""

import json
from typing import AsyncGenerator

from conversational_toolkit.agents.base import Agent, QueryWithContext, AgentAnswer
from conversational_toolkit.llms.base import LLM, LLMMessage, Roles, MessageContent


class Router(Agent):
    """
    Agent that routes queries to the most appropriate sub-agent.

    The system prompt is built automatically from each registered agent's 'description' field. The LLM returns a JSON object with a 'category' index that maps directly to the 'agents' list. Routing happens once per request; after that the selected agent handles the full conversation turn.
    """

    def __init__(self, llm: LLM, agents: list[Agent], description: str = "") -> None:
        self.agents = agents
        self.agent_mapping = {i: agent for i, agent in enumerate(agents)}
        system_prompt = self.construct_system_prompt()
        super().__init__(system_prompt, llm, description)

    def construct_system_prompt(self) -> str:
        prompt = """
            Objective: Classify user queries to route them to the most appropriate agent based on each agent's specialization.
            The agents available and their respective categories are:

        """
        for idx, agent in enumerate(self.agents, start=1):
            prompt += f"\n    Category {idx}: {agent.description}\n"

        prompt += """
            Instructions for Classification:
            Read the user's query and history carefully.
            Match it with the best-suited category.
            Output the classification as JSON in the following format:
            {{"step_by_step_thinking": your reasoning, "category": X}}, where X is the category number (1-n).
        """
        return prompt

    async def _get_agent(self, query_with_context: QueryWithContext) -> Agent:
        routing = await self.llm.generate(
            [
                LLMMessage(role=Roles.SYSTEM, content=[MessageContent(text=self.system_prompt, type="text")]),
                *query_with_context.history,
                LLMMessage(role=Roles.USER, content=[MessageContent(text=query_with_context.query, type="text")]),
            ]
        )
        category = json.loads(routing.content[0].text)["category"]
        return self.agent_mapping[category]

    async def answer_stream(self, query_with_context: QueryWithContext) -> AsyncGenerator[AgentAnswer, None]:
        agent = await self._get_agent(query_with_context)
        stream = agent.answer_stream(query_with_context)
        async for response in stream:
            yield response

    async def answer(self, query_with_context: QueryWithContext) -> AgentAnswer:
        agent = await self._get_agent(query_with_context)
        return await agent.answer(query_with_context)
