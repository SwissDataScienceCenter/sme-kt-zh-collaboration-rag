import React, { FunctionComponent } from "react";
import { cn } from "@/lib/lorem";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMessaging } from "@/hooks/useMessaging";
import { getBrothers } from "@/lib/thread";

interface Props {
    messageId: string;
    className?: string;
}

export const ThreadNavigation: FunctionComponent<Props> = (props: Props) => {
    const { className, messageId } = props;
    const { messages, changeThread, thread } = useMessaging();

    const brotherIds = getBrothers(messages, messageId).map((m) => m.id);
    const hasBrothers = brotherIds.length > 1;

    const brotherhoodIndex = brotherIds.findIndex((brotherId) => brotherId === messageId);
    const isLeftIconGrayed = brotherhoodIndex === 0;
    const isRightIconGrayed = brotherhoodIndex === brotherIds.length - 1;

    return hasBrothers ? (
        <div className={cn("flex items-center justify-center rounded-lg text-token-text-secondary", className)}>
            <div
                className={cn("p-0.5 rounded-md", isLeftIconGrayed ? "opacity-50" : "hover:bg-primary/10 hover:text-primary hover:cursor-pointer")}
                onClick={() => changeThread(brotherIds[brotherhoodIndex - 1])}
            >
                <ChevronLeft className={cn("h-4 w-4 ")} />
            </div>
            <span className="px-2 text-xs">
                {brotherhoodIndex + 1}/{brotherIds.length}
            </span>
            <div
                className={cn("p-0.5 rounded-md", isRightIconGrayed ? "opacity-50" : "hover:bg-primary/10 hover:text-primary hover:cursor-pointer")}
                onClick={() => changeThread(brotherIds[brotherhoodIndex + 1])}
            >
                <ChevronRight className={cn("h-4 w-4 ")} />
            </div>
        </div>
    ) : null;
};
