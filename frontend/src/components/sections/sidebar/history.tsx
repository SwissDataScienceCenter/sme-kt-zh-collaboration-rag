import React, { FunctionComponent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Settings, SquarePen } from "lucide-react";
import { SidebarButton } from "@/components/ui/sidebar-button";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { groupConversationsByDate } from "@/lib/conversation";
import { Footer } from "@/components/sections/sidebar/footer";
import { config } from "@/config";
import { useMessaging } from "@/hooks/useMessaging";
import { cn } from "@/lib/lorem";
import { SearchBar } from "@/components/ui/search-bar";
import { Conversation } from "@/services/conversation";

interface Props {
    onClickSettings: () => void;
    onChangeConversation?: (conversationId: string) => void;
}

export const History: FunctionComponent<Props> = (props: Props) => {
    const { onClickSettings, onChangeConversation } = props;
    const { conversations, changeConversation, createNewConversation, activeConversationId } = useMessaging();
    const { t, i18n } = useTranslation("app");
    const { isMobile } = useMediaQuery();
    const [filter, setFilter] = useState<string>("");
    const [filteredConversations, setFilteredConversations] = useState<Conversation[]>(conversations);

    const handleChangeConversation = (conversationId: string) => {
        if (onChangeConversation) {
            onChangeConversation(conversationId);
        }
        changeConversation(conversationId);
    };

    const handleNewConversation = () => {
        if (onChangeConversation) {
            onChangeConversation("");
        }
        createNewConversation();
    };

    const handleFilterConversations = (value: string) => {
        setFilteredConversations(conversations.filter((conversation) => conversation.title.toLowerCase().includes(value.toLowerCase())));
    };

    useEffect(() => {
        setFilteredConversations(conversations);
    }, [conversations]);

    const groupedConversations = groupConversationsByDate(filteredConversations, t);

    return (
        <div className="text-foreground h-full">
            <div className="flex flex-col h-full content-between">
                <div
                    className={cn("flex flex-row justify-between mt-4 mx-2 p-2", isMobile ? "" : "ripple rounded-md")}
                    onClick={() => {
                        if (!isMobile) {
                            handleNewConversation();
                        }
                    }}
                >
                    <div className="flex flex-row align-middle items-center">
                        <Avatar className="h-10 w-10 p-1 bg-white rounded-full border border-primary/10 flex items-center justify-center">
                            <AvatarImage src={config.app.logo} alt="Logo" loading="lazy" />
                        </Avatar>
                        <div className="text-xl flex pl-2 font-bold text-foreground cursor-default">{config.app.name}</div>
                    </div>
                    {!isMobile && (
                        <div className="flex flex-row align-middle items-center">
                            <SquarePen onClick={createNewConversation} className="w-5 h-5 mr-2" />
                        </div>
                    )}
                </div>
                <SearchBar
                    onChange={(value: string) => {
                        handleFilterConversations(value);
                    }}
                    className="px-4"
                />
                <div className="flex flex-1 flex-col pt-3 overflow-scroll scrollbar-hide">
                    {groupedConversations.map(
                        ({ date, conversations }) =>
                            conversations.length !== 0 && (
                                <div key={date} className="flex flex-col">
                                    <label className="text-xs text-foreground opacity-50 px-4 py-2">{date}</label>
                                    {conversations.map((conversation, index) => (
                                        <SidebarButton
                                            conversationId={conversation.id}
                                            label={conversation.title}
                                            key={conversation.id}
                                            onClick={() => handleChangeConversation(conversation.id)}
                                            isSelected={conversation.id === activeConversationId}
                                        />
                                    ))}
                                </div>
                            ),
                    )}
                </div>
                <div className="pt-2">
                    <div
                        className="flex my-4 py-2 px-4 mx-2 cursor-pointer bg-primary text-primary-foreground rounded-md content-center hover:bg-primary/80 shadow-md"
                        onClick={onClickSettings}
                    >
                        <div className="flex flex-row w-full content-center justify-center">
                            <div className="flex text-sm font-bold items-center">
                                {t("settings")} <Settings className="h-4" />
                            </div>
                        </div>
                    </div>
                </div>
                <Footer />
            </div>
        </div>
    );
};
