import { Message } from "@/services/message";

export const getMessageThread = (messages: Message[], messageId?: Message["id"]): Message[] => {
    const message = messages.find((msg) => msg.id === messageId);

    if (!message) {
        return [];
    }

    if (!message.parent_id) {
        return [message];
    }

    const parentMessage = getMessageThread(messages, message.parent_id);
    return [message, ...parentMessage].sort((a, b) => a.create_timestamp - b.create_timestamp);
};

export const getBrothers = (messages: Message[], messageId?: Message["id"]): Message[] => {
    const message = messages.find((msg) => msg.id === messageId);

    if (!message) {
        return [];
    }

    return messages.filter((m) => m.parent_id === message.parent_id).sort((a, b) => a.create_timestamp - b.create_timestamp);
};

export const getLastChild = (messages: Message[], messageId?: Message["id"]): Message | null => {
    const message = messages.find((msg) => msg.id === messageId);

    if (!message) {
        return null;
    }

    const childMessageId = message.id;

    const child = messages.sort((a, b) => b.create_timestamp - a.create_timestamp).find((msg) => msg.parent_id === childMessageId);

    if (!child) {
        return message;
    }

    return getLastChild(messages, child.id);
};
