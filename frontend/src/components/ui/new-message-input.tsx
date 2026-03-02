import * as React from "react";
import { useEffect, useRef } from "react";

import { cn } from "@/lib/lorem";
import { useMediaQuery } from "@/hooks/useMediaQuery";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    onPressEnter?: (str: string) => void;
}

const NewMessageInput = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, onPressEnter, value = "", ...props }, ref) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const { isMobile } = useMediaQuery();
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

        textArea.style.height = "auto";
        textArea.style.height = textArea.scrollHeight - 20 + "px";

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
        <div className="w-full border border-border rounded-lg bg-input text-foreground pb-2 focus:shadow-sm focus:drop-shadow-sm">
            <textarea
                className={cn(
                    "w-full max-h-52 px-4 pt-4 resize-none overflow-hidden bg-input rounded-lg text-foreground placeholder:text-foreground/50 placeholder:text-ellipsis placeholder:text-nowrap placeholder:overflow-hidden  focus:outline-none transition duration-300 ease-in-out",
                    className,
                )}
                onKeyDown={(e) => handleKeyPress(e)}
                ref={textareaRef}
                value={inputValue}
                {...props}
            />
        </div>
    );
});
NewMessageInput.displayName = "NewMessageInput";

export { NewMessageInput };
