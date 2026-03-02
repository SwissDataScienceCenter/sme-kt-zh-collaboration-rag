import { ApiService } from "./api";

export interface Message {
    id: string;
    content: string;
    role: "user" | "assistant" | "system";
    create_timestamp: number;
    conversation_id: string;
    parent_id?: string;
    user_id?: string;
    sources?: Source[];
    reaction?: Reaction;
    follow_up_questions?: string[];
}

export interface Source {
    id: string;
    message_id: string;
    content: string;
    metadata: {
        title?: string;
        source?: string;
        origin?: string;
        url?: string;
        header?: string;
        mime_type?: string;
        [key: string]: string | number | boolean | null | undefined;
    };
}

export enum MessageTypes {
    NEXT = "next",
    REDO = "redo",
}

export interface UserInput {
    content: string;
    conversation_id?: string;
    parent_id?: string;
    type: MessageTypes;
}

export interface Reaction {
    id: string;
    message_id: string;
    content: string;
    note?: string;
}

export type ThumbsReaction = ":thumbsup:" | ":thumbsdown:";

class MessageService extends ApiService {
    constructor(apiUrl: string) {
        super(apiUrl);
    }

    async create(input: UserInput): Promise<Message | null> {
        try {
            const postUrl = `${this.apiUrl}/`;
            const response = await this.fetchApi(postUrl, {
                method: "POST",
                body: JSON.stringify(input),
            });

            return response.json();
        } catch (e) {
            console.log("error", e);
            return null;
        }
    }

    async createStream(input: UserInput, onMessage: (message: Message) => void, onError: () => void, onEnd: () => void) {
        try {
            const postUrl = `${this.apiUrl}/stream`;
            const response = await this.fetchApi(postUrl, {
                method: "POST",
                body: JSON.stringify(input),
            });

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            if (reader) {
                let doneReading = false;
                while (!doneReading) {
                    const { value, done } = await reader.read();
                    doneReading = done;
                    if (value) {
                        const chunk = decoder.decode(value, { stream: true });
                        buffer += chunk;

                        let boundaryIndex;
                        while ((boundaryIndex = buffer.lastIndexOf("}{")) !== -1) {
                            const completeMessage = buffer.substring(0, boundaryIndex + 1);
                            buffer = buffer.substring(boundaryIndex + 1);

                            try {
                                const parsedMessage: Message = JSON.parse(completeMessage);
                                onMessage(parsedMessage);
                            } catch (parseError) {}
                        }

                        // Try parsing any remaining buffer data if it's a complete JSON object
                        try {
                            const parsedMessage: Message = JSON.parse(buffer);
                            onMessage(parsedMessage);
                            buffer = ""; // Clear buffer after successful parsing
                        } catch (parseError) {
                            // Do nothing here; buffer might still be incomplete
                        }
                    }
                }
                onEnd();
            }
        } catch (e) {
            console.log("error", e);
            onError();
            return null;
        }
    }
}

export const messageService = new MessageService(process.env.SERVER_URL! + "/api/v1/messages");
