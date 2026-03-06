import React, { FunctionComponent, memo, useCallback, useEffect, useState } from "react";
import { Message, MessageTypes } from "@/services/message";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Edit3, User2Icon } from "lucide-react";
import { ERROR_ID, LOADING_ID, useMessaging } from "@/hooks/useMessaging";
import { config } from "@/config";
import { useTranslation } from "react-i18next";
import { SourceItem } from "@/components/ui/source-item";
import { Reactions } from "@/components/ui/reactions";
import { Markdown } from "@/components/ui/markdown";
import { ThreadNavigation } from "@/components/ui/thread-navigation";
import { Redo } from "@/components/ui/redo";
import { MessageEdit } from "@/components/ui/message-edit";
import { cn } from "@/lib/lorem";

interface MessageItemProps extends Message {
    onClick?: (input: string) => void;
    className?: string;
    isLastMessage: boolean;
}

export const MessageItem: FunctionComponent<MessageItemProps> = (props: MessageItemProps) => {
    const { id, content, role, sources, className, reaction, isLastMessage, follow_up_questions, parent_id } = props;
    const isUser = role === "user";
    const { t } = useTranslation("app");
    const [isHover, setIsHover] = useState(false);
    const [followUp, setFollowUp] = useState(follow_up_questions);
    const [isEdit, setIsEdit] = useState(false);
    const [editableContent, setEditableContent] = useState(content);

    const { sendMessage } = useMessaging();

    const isLoading = id === LOADING_ID;
    const isError = id === ERROR_ID;

    const hasSources = sources && sources.length > 0;
    const hasFollowUp = followUp && followUp.length > 0;

    const isActionable = (isHover || isLastMessage) && !isLoading && !isError;

    useEffect(() => {
        if (follow_up_questions && follow_up_questions.length) {
            setFollowUp(follow_up_questions);
        }
    }, [follow_up_questions]);

    const handleMouseEnter = useCallback(() => setIsHover(true), []);
    const handleMouseLeave = useCallback(() => setIsHover(false), []);

    if (isEdit) {
        return (
            <MessageEdit
                onPressEnter={() => {
                    setIsEdit(false);
                    sendMessage(editableContent, MessageTypes.NEXT, parent_id);
                }}
                onCancel={() => setIsEdit(false)}
                onChange={(e) => setEditableContent(e.target.value)}
                value={editableContent}
            />
        );
    }

    return (
        <div className="pl-1 pr-4" onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
            <div className="flex flex-row align-middle items-center">
                <Avatar className="h-7 w-7 p-1 bg-white text-black rounded-full border border-primary/10 flex items-center justify-center">
                    {isUser ? <User2Icon /> : <AvatarImage src={config.app.logo} alt="Logo" loading="lazy" />}
                </Avatar>
                <div className="flex pl-2 font-bold text-foreground">{isUser ? t("you") : config.agent.name}</div>
            </div>
            {isLoading ? (
                <div className="flex flex-row pl-9 text-foreground items-center">
                    {content}
                    <div className="rounded-full w-3 h-3 bg-foreground blink"></div>
                </div>
            ) : isError ? (
                <div className="pl-9 text-foreground border border-destructive mt-2 p-4 pr-6 rounded-lg bg-destructive/15">{content}</div>
            ) : (
                <MessageContent content={content} />
            )}
            {hasSources && (
                <div className="pl-9 pt-2 text-foreground text-xs flex flex-col">
                    <div className="text-foreground opacity-50">{t("sources")}:</div>
                    <div className="flex flex-row md:flex-wrap overflow-auto scrollbar-hide">
                        {sources?.map((source, index) => <SourceItem key={index} source={source} index={index} />)}
                    </div>
                </div>
            )}
            <div className="flex items-center justify-start p-1 pl-8">
                <ThreadNavigation messageId={id} />
                {isUser ? (
                    <div
                        className={cn(
                            "p-1 flex flex-row text-foreground/40 rounded-md hover:bg-primary/10 hover:text-primary hover:cursor-pointer",
                            isActionable ? "opacity-100" : "opacity-0",
                        )}
                    >
                        <Edit3 onClick={() => setIsEdit(true)} className={cn("h-3.5 w-3.5")} />
                    </div>
                ) : (
                    <>
                        <Reactions isVisible={isActionable} reaction={reaction} messageId={id} />
                        <Redo isVisible={isActionable} parentId={parent_id!} />
                    </>
                )}
            </div>
            {hasFollowUp && (
                <div className="pl-9 pt-2 text-foreground text-xs flex flex-col">
                    <div className="opacity-50">{t("suggestedFollowUp")}:</div>
                    <div className="flex flex-row md:flex-wrap overflow-auto scrollbar-hide ">
                        {followUp?.map((question, index) => (
                            <div
                                key={index}
                                className="mt-1 py-1 px-2 mr-2 border border-dashed rounded-md hover:cursor-pointer hover:bg-muted/50 "
                                onClick={() => {
                                    setFollowUp([]);
                                    sendMessage(question, MessageTypes.NEXT, id);
                                }}
                            >
                                {question}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// eslint-disable-next-line react/display-name
const MessageContent = memo(({ content }: { content: string }) => (
    <div className="pl-9 text-foreground text-justify">
        <Markdown content={content} />
    </div>
));
