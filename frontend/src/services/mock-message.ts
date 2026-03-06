import { ApiService } from "./api";
import { randomSentencesGenerator } from "@/lib/lorem";
import { randomWait } from "@/services/mock-conversation";
import { Message, UserInput } from "@/services/message";

const cache = new Map<string, Message[]>();

const addMessageToCache = (conversation_id: string, message: Message) => {
    const messages = cache.get(conversation_id) || [];
    messages.push(message);
    cache.set(conversation_id, messages);
};

export const getMessagesFromCache = (conversation_id: string): Message[] => {
    const messages = cache.get(conversation_id);
    if (!messages || messages.length === 0) {
        const randomMessages = generateRandomNumberOfMessages();
        cache.set(conversation_id, randomMessages);
        return randomMessages;
    }
    return messages;
};

const generateRandomMessage = (role: "assistant" | "user" = "assistant"): Message => {
    const numberOfSources = role === "assistant" ? Math.floor(Math.random() * 5) : 0;
    return {
        id: Math.random().toString(36).substring(2),
        content: randomSentencesGenerator(),
        role,
        create_timestamp: Date.now(),
        conversation_id: Math.random().toString(36).substring(2),
        sources: Array.from({ length: numberOfSources }, (e, i) => ({
            id: Math.random().toString(36).substring(2),
            message_id: Math.random().toString(36).substring(2),
            content: randomSentencesGenerator(),
            metadata: {
                url: "https://www.google.com",
            },
        })),
    };
};

const generateRandomNumberOfMessages = (max: number = 10): Message[] => {
    const numberOfMessages = (Math.floor((Math.random() * max) / 2) + 1) * 2;
    return Array.from({ length: numberOfMessages }, (e, i) => generateRandomMessage(i % 2 === 0 ? "user" : "assistant"));
};

class MessageService extends ApiService {
    constructor(apiUrl: string) {
        super(apiUrl);
    }

    async create(message: UserInput): Promise<Message | null> {
        try {
            if (!message.conversation_id) {
                message.conversation_id = Math.random().toString(36).substring(2);
            }

            addMessageToCache(message.conversation_id, {
                id: Math.random().toString(36).substring(2),
                content: message.content,
                role: "user",
                create_timestamp: Date.now(),
                conversation_id: message.conversation_id,
            });

            await randomWait(3000);

            const mockResponse: Message = generateRandomMessage();

            addMessageToCache(message.conversation_id, mockResponse);

            return mockResponse;
        } catch {
            return null;
        }
    }

    async createStream(message: UserInput, onMessage: (streamedMessage: Message) => void, onError: () => void, onEnd: () => void) {
        const response = await this.create(message);
        if (!response) {
            onError();
            return;
        }
        onMessage(response);
        onEnd();
    }
}

export const messageService = new MessageService(process.env.SERVER_URL! + "/api/v1");
