import * as React from "react";
import { useEffect, useRef } from "react";

import { cn } from "@/lib/lorem";
import { useTranslation } from "react-i18next";
import { Avatar } from "@/components/ui/avatar";
import { User2Icon } from "lucide-react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    onPressEnter?: (value: string) => void;
    onCancel?: () => void;
}

const MessageEdit = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, onPressEnter, onCancel, value = "", ...props }, ref) => {
    const { t } = useTranslation("app");
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const inputValue = String(value);

    const handleKeyPress = (event: { key: string; shiftKey?: boolean; preventDefault: () => void }) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (onPressEnter) {
                onPressEnter(inputValue);
            }
        }
    };

    const resizeTextarea = () => {
        const textArea = textareaRef.current;
        if (!textArea) return;

        textArea.style.height = "auto"; // Reset the height
        textArea.style.height = textArea.scrollHeight + "px"; // Set to scroll height

        if (textArea.scrollHeight >= 208) {
            textArea.style.overflowY = "scroll";
        } else {
            textArea.style.overflowY = "hidden";
        }
    };

    useEffect(() => {
        resizeTextarea();
    }, [inputValue]);

    return (
        <>
            <div className="pl-1 flex flex-row align-middle items-center">
                <Avatar className="h-7 w-7 p-1 bg-white text-black rounded-full border border-primary/10 flex items-center justify-center">
                    <User2Icon />
                </Avatar>
                <div className="flex pl-2 font-bold text-foreground">{t("you")}</div>
            </div>
            <div className="bg-input p-4 border border-border rounded-lg">
                <textarea
                    className={cn(
                        className,
                        "w-full max-h-48 resize-none bg-input overflow-hidden text-foreground placeholder:text-foreground/50 placeholder:text-ellipsis placeholder:text-nowrap placeholder:overflow-hidden focus:outline-none",
                    )}
                    onKeyDown={(e) => handleKeyPress(e)}
                    ref={textareaRef}
                    value={inputValue}
                    {...props}
                />
                <div className="flex justify-end gap-2">
                    <button type="submit" className="p-3 rounded-lg border-0 bg-transparent text-primary text-sm ripple" onClick={() => onCancel && onCancel()}>
                        {t("cancel")}
                    </button>
                    <button
                        type="submit"
                        className="p-3 rounded-lg bg-primary text-primary-foreground text-sm ripple hover:bg-primary/70"
                        onClick={() => onPressEnter && onPressEnter(inputValue)}
                    >
                        {t("confirm")}
                    </button>
                </div>
            </div>
        </>
    );
});
MessageEdit.displayName = "MessageEdit";

export { MessageEdit };
