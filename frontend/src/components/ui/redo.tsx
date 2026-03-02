import React, { FunctionComponent } from "react";
import { cn } from "@/lib/lorem";
import { RefreshCcw } from "lucide-react";
import { useMessaging } from "@/hooks/useMessaging";
import { MessageTypes } from "@/services/message";

interface Props {
    parentId: string;
    isVisible: boolean;
    className?: string;
}

export const Redo: FunctionComponent<Props> = (props: Props) => {
    const { className, isVisible, parentId } = props;
    const { sendMessage } = useMessaging();

    const handleRedo = () => {
        sendMessage(parentId, MessageTypes.REDO, parentId);
    };

    return (
        <div className={cn("py-2 flex justify-start transition-all duration-300", className, isVisible ? "opacity-100 hover:cursor-pointer" : "opacity-0")}>
            <div className="pl-2 flex flex-row text-foreground/40 ">
                <div className={cn("p-1 rounded-md hover:bg-primary/10 hover:text-primary")}>
                    <RefreshCcw onClick={() => handleRedo()} className={cn("h-3.5 w-3.5")} />
                </div>
            </div>
        </div>
    );
};
