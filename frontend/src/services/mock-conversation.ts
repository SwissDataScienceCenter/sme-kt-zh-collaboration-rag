import { ApiService } from "./api";
import { wait } from "next/dist/lib/wait";
import { randomSentencesGenerator } from "@/lib/lorem";
import { generateRandomConversations } from "@/lib/conversation";
import { Conversation } from "@/services/conversation";
import { Message, Reaction } from "@/services/message";
import { getMessagesFromCache } from "@/services/mock-message";

const cache = [] as Conversation[];

const addConversationsToCache = (conversations: Conversation[]) => {
    conversations.map((conversation) => {
        cache.find((s) => s.id === conversation.id) || cache.push(conversation);
    });
};

const getConversationsFromCache = (): Conversation[] => {
    const hasConversations = cache.length > 0;
    if (!hasConversations) {
        addConversationsToCache(generateRandomConversations());
    }
    return JSON.parse(JSON.stringify(cache));
};

export const randomWait = (max: number) => wait(Math.floor(Math.random() * max));

class ConversationService extends ApiService {
    constructor(apiUrl: string) {
        super(apiUrl);
    }

    async getAll(): Promise<Conversation[]> {
        try {
            await randomWait(500);
            return getConversationsFromCache();
        } catch {
            return [];
        }
    }

    async get(conversationId: Conversation["id"]): Promise<Conversation | null> {
        try {
            await randomWait(500);
            return {
                id: conversationId,
                title: randomSentencesGenerator(3, 10),
                update_timestamp: Date.now(),
            };
        } catch {
            return null;
        }
    }

    async getMessages(conversation_id: string): Promise<Message[]> {
        try {
            if (!conversation_id) {
                return [];
            }

            await randomWait(200);

            return getMessagesFromCache(conversation_id);
        } catch (e) {
            console.log("error", e);
            return [];
        }
    }

    async delete(conversationId: Conversation["id"]): Promise<boolean | null> {
        try {
            if (!conversationId) {
                return null;
            }
            const index = cache.findIndex((s) => s.id === conversationId);
            if (index !== -1) {
                cache.splice(index, 1);
            }
            return true;
        } catch {
            return null;
        }
    }

    async rename(conversationId: Conversation["id"], conversationName: string): Promise<Conversation | null> {
        try {
            if (!conversationId) {
                return null;
            }
            const conversation = cache.findIndex((conversation) => conversation.id === conversationId);
            if (conversation !== -1) {
                cache[conversation].title = conversationName;
                cache[conversation].update_timestamp = Date.now();
            }
            return { ...cache[conversation] };
        } catch {
            return null;
        }
    }

    async react(messageId: Message["id"], reactionContent: Reaction["content"]): Promise<Message | null> {
        try {
            return null;
        } catch (e) {
            console.log("error", e);
            return null;
        }
    }
}

export const conversationService = new ConversationService(process.env.SERVER_URL! + "/api/v1/conversations");
