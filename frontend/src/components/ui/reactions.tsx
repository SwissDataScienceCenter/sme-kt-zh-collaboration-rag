import React, { FunctionComponent, useState } from "react";
import { cn } from "@/lib/lorem";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { Reaction } from "@/services/message";
import { useMessaging } from "@/hooks/useMessaging";

interface Props {
    messageId: string;
    isVisible: boolean;
    reaction?: Reaction;
    className?: string;
}

export const Reactions: FunctionComponent<Props> = (props: Props) => {
    const { className, isVisible, reaction, messageId } = props;
    const { reactToMessage, cursor, messages, changeThread } = useMessaging();

    const [localReaction, setLocalReaction] = useState<Reaction["content"] | null>(null);

    const hasLocalReaction = localReaction != undefined;
    const hasReaction = reaction != undefined || hasLocalReaction;
    const isDisabled = hasReaction || localReaction || !isVisible;

    const isShown = hasReaction || localReaction || isVisible;
    const finalReaction = hasLocalReaction ? localReaction : reaction;

    const handleReaction = (reactionContent: Reaction["content"]) => {
        if (isDisabled) {
            return;
        }
        reactToMessage(messageId, reactionContent);
        setLocalReaction(reactionContent);
    };

    return (
        <div className={cn("py-2 flex justify-start transition-all duration-300", className, isShown ? "opacity-100" : "opacity-0")}>
            <div className="pl-2 flex flex-row text-foreground/40 ">
                <div className={cn("p-1 rounded-md hover:bg-primary/10", isDisabled ? "" : "hover:text-primary hover:cursor-pointer")}>
                    <ThumbsUp
                        onClick={() => handleReaction(":thumbsup:")}
                        className={cn("h-3.5 w-3.5", hasReaction && finalReaction == ":thumbsup:" ? "fill-primary" : "")}
                    />
                </div>
                <div className={cn("p-1 hover:bg-primary/10 ml-1 rounded-md", isDisabled ? "" : "hover:text-primary hover:cursor-pointer")}>
                    <ThumbsDown
                        onClick={() => handleReaction(":thumbsdown:")}
                        className={cn("h-3.5 w-3.5", hasReaction && finalReaction == ":thumbsdown:" ? "fill-primary" : "")}
                    />
                </div>
            </div>
        </div>
    );
};
