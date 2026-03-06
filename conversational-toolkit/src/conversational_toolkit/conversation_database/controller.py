"""
Conversational toolkit controller (Facade).

'ConversationalToolkitController' is the single entry point for all application logic. It coordinates five pluggable database repositories and an agent to handle the full lifecycle of a conversation turn: user registration, conversation and thread management, agent invocation, streaming, and persistence of messages, sources, and reactions.

The two public entry points for message processing are:

    'process_new_message'        - non-streaming, returns the final 'ClientMessage'.
    'process_new_message_stream' - async generator that yields partial content chunks during generation, then the final persisted message with sources.

'ClientMessage' extends 'Message' with the API-response fields ('sources', 'reaction', 'follow_up_questions') that the frontend needs but that are not stored directly on the message record.
"""

import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any

from pydantic import BaseModel

from conversational_toolkit.agents.base import Agent, QueryWithContext
from conversational_toolkit.conversation_database.data_models.conversation import Conversation, ConversationDatabase
from conversational_toolkit.conversation_database.data_models.message import Message, MessageDatabase
from conversational_toolkit.conversation_database.data_models.reaction import Reaction, ReactionDatabase
from conversational_toolkit.conversation_database.data_models.source import Source, SourceDatabase
from conversational_toolkit.conversation_database.data_models.user import User, UserDatabase
from conversational_toolkit.llms.base import LLMMessage, Roles, MessageContent
from conversational_toolkit.utils.database import generate_uid
from conversational_toolkit.utils.metadata_provider import MetadataProvider
from conversational_toolkit.utils.time import get_current_timestamp


class MessageInput(BaseModel):
    content: str
    parent_id: str | None = None
    conversation_id: str | None = None
    type: str | None = None


class ConversationInput(BaseModel):
    title: str


class ReactionInput(BaseModel):
    content: str = ""
    note: str | None = None


class ClientMessage(Message):
    sources: Sequence[Source]
    reaction: str | None
    follow_up_questions: Sequence[str] | None

    def encode(self, charset: str = "utf-8") -> bytes:
        return json.dumps(self.model_dump()).encode(charset)


class ClientConversation(Conversation):
    messages: list[ClientMessage]


DEFAULT_CONVERSATION_TITLE = "New Conversation"


class ConversationalToolkitController:
    def __init__(
        self,
        conversation_db: ConversationDatabase,
        message_db: MessageDatabase,
        reaction_db: ReactionDatabase,
        source_db: SourceDatabase,
        user_db: UserDatabase,
        agent: Agent,
    ):
        self.conversation_db = conversation_db
        self.message_db = message_db
        self.reaction_db = reaction_db
        self.source_db = source_db
        self.user_db = user_db
        self.agent = agent

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.user_db.get_user_by_id(user_id)

    async def register_user(self, user_id: str) -> User:
        return await self.user_db.create_user(User(id=user_id))

    async def process_new_message(self, user_input: MessageInput, user_id: str) -> ClientMessage:
        last_message = None
        async for message in self.process_new_message_stream(user_input, user_id):
            last_message = message
        if last_message is None:
            raise Exception("No message was generated from the stream")
        return last_message

    async def _setup_conversation(self, user_input: MessageInput, user_id: str) -> tuple[Conversation, list[Message]]:
        if user_input.conversation_id is None:
            create_time = get_current_timestamp()
            conversation = await self.conversation_db.create_conversation(
                Conversation(
                    id=generate_uid(),
                    user_id=user_id,
                    create_timestamp=create_time,
                    update_timestamp=create_time,
                    title=DEFAULT_CONVERSATION_TITLE,
                )
            )
            return conversation, []

        conversation = await self.conversation_db.get_conversation_by_id(user_input.conversation_id)
        conversation_history = await self.message_db.get_messages_by_conversation_id(conversation.id)
        parent_message = await self.message_db.get_message_by_id(user_input.parent_id) if user_input.parent_id else None
        if not parent_message:
            return conversation, []

        current_message = parent_message
        thread: list[Message] = [current_message]
        while current_message.parent_id:
            current_message = next(
                message for message in conversation_history if message.id == current_message.parent_id
            )
            thread.append(current_message)
        return conversation, thread

    async def process_new_message_stream(
        self, user_input: MessageInput, user_id: str
    ) -> AsyncGenerator[ClientMessage, Any]:
        with MetadataProvider.get_manager():
            user = await self.user_db.get_user_by_id(user_id)

            if not user:
                await self.user_db.create_user(User(id=user_id))

            conversation, thread = await self._setup_conversation(user_input, user_id)

            if user_input.type == "redo":
                if user_input.parent_id is None:
                    raise ValueError("Parent id must be provided for redo type")
                input_message = await self.message_db.get_message_by_id(user_input.parent_id)
            else:
                input_message = await self.message_db.create_message(
                    Message(
                        id=generate_uid(),
                        user_id=user_id,
                        conversation_id=conversation.id,
                        content=user_input.content,
                        role=Roles.USER,
                        create_timestamp=get_current_timestamp(),
                        metadata=None,
                        parent_id=user_input.parent_id,
                    )
                )

            stream = self.agent.answer_stream(
                QueryWithContext(
                    query=input_message.content,
                    history=[
                        LLMMessage(role=message.role, content=[MessageContent(type="text", text=message.content)])
                        for message in sorted(thread, key=lambda m: m.create_timestamp)
                    ],
                )
            )

            last_chunk = None
            async for chunk in stream:
                last_chunk = chunk
                if chunk.content:
                    yield ClientMessage(
                        id="",
                        user_id="",
                        conversation_id=conversation.id,
                        content=chunk.content[0].text if chunk.content else "",
                        role=Roles.ASSISTANT,
                        sources=[],
                        reaction=None,
                        follow_up_questions=chunk.follow_up_questions,
                        parent_id=input_message.id,
                        create_timestamp=get_current_timestamp(),
                    )

            if last_chunk is None:
                return

            final_message = await self.message_db.create_message(
                Message(
                    id=generate_uid(),
                    user_id=None,
                    conversation_id=conversation.id,
                    content=chunk.content[0].text if chunk.content else "",
                    role=Roles.ASSISTANT,
                    create_timestamp=get_current_timestamp(),
                    metadata=MetadataProvider.get_metadata(),
                    parent_id=input_message.id,
                )
            )

            sources = [
                await self.source_db.create_source(
                    Source(
                        id=generate_uid(), message_id=final_message.id, content=source.content, metadata=source.metadata
                    )
                )
                for source in last_chunk.sources
            ]

            if user_input.conversation_id is None:
                await self.conversation_db.update_conversation(
                    conversation=Conversation(
                        id=conversation.id,
                        user_id=user_id,
                        create_timestamp=conversation.create_timestamp,
                        update_timestamp=get_current_timestamp(),
                        title=final_message.content[:40],
                    )
                )

            yield ClientMessage(
                id=final_message.id,
                user_id=final_message.user_id,
                conversation_id=final_message.conversation_id,
                content=final_message.content,
                role=final_message.role,
                sources=sources,
                reaction=None,
                follow_up_questions=last_chunk.follow_up_questions,
                parent_id=input_message.id,
                create_timestamp=final_message.create_timestamp,
            )

    async def get_conversations_data_by_user_id(self, user_id: str) -> list[Conversation]:
        return await self.conversation_db.get_conversations_by_user_id(user_id)

    async def get_conversation_by_id(self, conversation_id: str) -> ClientConversation:
        conversation = await self.conversation_db.get_conversation_by_id(conversation_id)
        messages = await self.message_db.get_messages_by_conversation_id(conversation_id)
        api_messages = [
            ClientMessage(
                id=message.id,
                user_id=message.user_id,
                conversation_id=message.conversation_id,
                content=message.content,
                role=message.role,
                sources=await self.source_db.get_sources_by_message_id(message.id),
                reaction=None,
                follow_up_questions=[],
                parent_id=message.parent_id,
                create_timestamp=message.create_timestamp,
            )
            for message in sorted(messages, key=lambda m: m.create_timestamp)
        ]

        return ClientConversation(
            id=conversation.id,
            create_timestamp=conversation.create_timestamp,
            update_timestamp=conversation.update_timestamp,
            title=conversation.title,
            user_id=conversation.user_id,
            messages=api_messages,
        )

    async def update_conversation(self, conversation_id: str, conversation_updates: ConversationInput) -> Conversation:
        conversation = await self.conversation_db.get_conversation_by_id(conversation_id)

        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")

        return await self.conversation_db.update_conversation(
            conversation=Conversation(
                id=conversation.id,
                user_id=conversation.user_id,
                create_timestamp=conversation.create_timestamp,
                update_timestamp=get_current_timestamp(),
                title=conversation_updates.title,
            )
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        messages = await self.message_db.get_messages_by_conversation_id(conversation_id)
        for message in messages:
            sources = await self.source_db.get_sources_by_message_id(message_id=message.id)
            await self.source_db.delete_sources([source.id for source in sources])

            reactions = await self.reaction_db.get_reactions_by_message_id(message_id=message.id)
            await self.reaction_db.delete_reactions([reaction.id for reaction in reactions])

            await self.message_db.delete_message(message.id)

        return await self.conversation_db.delete_conversation(conversation_id)

    async def get_messages_by_conversation_id(self, conversation_id: str) -> list[ClientMessage]:
        messages = await self.message_db.get_messages_by_conversation_id(conversation_id)
        api_messages = []
        for message in messages:
            reactions = await self.reaction_db.get_reactions_by_message_id(message.id)
            api_reaction = reactions[0].content if reactions else None
            sources = await self.source_db.get_sources_by_message_id(message.id)
            api_message = ClientMessage(
                id=message.id,
                user_id=message.user_id,
                conversation_id=message.conversation_id,
                content=message.content,
                role=message.role,
                sources=sources,
                reaction=api_reaction,
                follow_up_questions=[],
                parent_id=message.parent_id,
                create_timestamp=message.create_timestamp,
            )

            api_messages.append(api_message)

        return api_messages

    async def add_reaction(self, reaction_input: ReactionInput, message_id: str, user_id: str) -> Reaction:
        message = await self.message_db.get_message_by_id(message_id)
        if not message:
            raise ValueError(f"Message with id {message_id} not found")
        conversation = await self.conversation_db.get_conversation_by_id(message.conversation_id)
        if conversation.user_id != user_id:
            raise ValueError(f"User {user_id} does not have access to conversation {conversation.id}")
        reactions = await self.reaction_db.get_reactions_by_message_id(message_id)
        user_reactions = [reaction for reaction in reactions if reaction.user_id == user_id]
        if user_reactions:
            await self.reaction_db.delete_reactions([reaction.id for reaction in user_reactions])

        return await self.reaction_db.create_reaction(
            Reaction(
                id=generate_uid(),
                user_id=user_id,
                message_id=message_id,
                content=reaction_input.content,
                note=reaction_input.note,
            )
        )
