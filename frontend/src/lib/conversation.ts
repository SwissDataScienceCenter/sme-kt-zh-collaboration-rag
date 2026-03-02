import { TFunction } from "i18next";
import { Conversation } from "@/services/conversation";
import { randomSentencesGenerator } from "@/lib/lorem";

export const randomConversationName = () => randomSentencesGenerator(3, 10);

/*
Generate a random number of conversations
 */
export const generateRandomConversations = (max = 40) => {
    const conversations: Conversation[] = [];
    const numberOfConversations = Math.floor(Math.random() * max) + 1;
    for (let i = 0; i < numberOfConversations; i++) {
        conversations.push({
            id: Math.random().toString(36).substring(2),
            title: randomConversationName(),
            // random date in the last 30 days
            update_timestamp: Date.now() - Math.floor(Math.random() * 30) * 24 * 60 * 60 * 1000,
        });
    }
    return conversations;
};

export const groupConversationsByDate = (conversations: Conversation[], translate: TFunction): { date: string; conversations: Conversation[] }[] => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);
    const twoWeeksAgo = new Date(today);
    twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

    return conversations
        .sort((a, b) => b.update_timestamp - a.update_timestamp)
        .reduce(
            (acc, conversation) => {
                const conversationDate = new Date(conversation.update_timestamp);
                if (conversationDate.toDateString() === today.toDateString()) {
                    acc[0].conversations.push(conversation);
                } else if (conversationDate.toDateString() === yesterday.toDateString()) {
                    acc[1].conversations.push(conversation);
                } else if (conversationDate > lastWeek) {
                    acc[2].conversations.push(conversation);
                } else if (conversationDate > twoWeeksAgo) {
                    acc[3].conversations.push(conversation);
                } else {
                    const year = conversationDate.getFullYear();
                    const yearGroup = acc.find((group) => group.date === year.toString());
                    if (yearGroup) {
                        yearGroup.conversations.push(conversation);
                    } else {
                        acc.push({ date: year.toString(), conversations: [conversation] });
                    }
                }
                return acc;
            },
            [
                { date: translate("dates.today"), conversations: [] },
                { date: translate("dates.yesterday"), conversations: [] },
                { date: translate("dates.lastWeek"), conversations: [] },
                { date: translate("dates.twoWeeksAgo"), conversations: [] },
            ] as { date: string; conversations: Conversation[] }[],
        );
};
