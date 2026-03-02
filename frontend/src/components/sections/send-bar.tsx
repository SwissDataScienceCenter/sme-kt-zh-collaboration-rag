import React, { FunctionComponent } from "react";
import { NewMessageInput } from "@/components/ui/new-message-input";
import { useTranslation } from "react-i18next";
import { Suggestion, Suggestions } from "@/components/ui/suggestion";
import { Disclaimer } from "@/components/ui/disclaimer";
import { SendHorizonal } from "lucide-react";
import { cn } from "@/lib/lorem";
import { useMessaging } from "@/hooks/useMessaging";
import { MessageTypes } from "@/services/message";

export const SendBar: FunctionComponent = () => {
    const { thread, sendMessage, sending, loading, cursor } = useMessaging();
    const [message, setMessage] = React.useState<string>("");
    const { t } = useTranslation("app");

    const showSuggestions = !loading && !thread.length;

    const handleSendMessage = (message: string) => {
        if (!sending) {
            sendMessage(message, MessageTypes.NEXT, cursor);
            setMessage("");
        }
    };

    const suggestions: Suggestion[] = t("suggestions", { returnObjects: true });

    const disabled = message.length === 0 || sending;

    return (
        <div className="w-full flex justify-center">
            <div className="w-full m-2 md:w-3/4 max-w-[700px]">
                <div className="flex justify-center w-full flex-col px-2 sm:px-0">
                    {showSuggestions ? (
                        <div className="px:0 pb-2 sm:p-2 overflow-scroll scrollbar-hide">
                            <Suggestions suggestions={suggestions} onClick={handleSendMessage} />
                        </div>
                    ) : null}
                    <div className="relative flex items-center">
                        <NewMessageInput
                            className="pr-12 w-full text-base"
                            value={message}
                            onChange={(e) => {
                                setMessage(e.target.value);
                            }}
                            placeholder={t("messagePlaceholder")}
                            onPressEnter={() => handleSendMessage(message)}
                        />
                        <SendHorizonal
                            className={cn(
                                "absolute right-0 bottom-0 mb-3 mr-3 p-2 h-9 w-9 border text-white rounded transition ease-in-out duration-300",
                                disabled ? "bg-gray-400 cursor-default" : "cursor-pointer bg-secondary hover:bg-secondary/85 border-secondary/20",
                            )}
                            onClick={() => !disabled && handleSendMessage(message)}
                        />
                    </div>
                    <Disclaimer />
                </div>
            </div>
        </div>
    );
};
