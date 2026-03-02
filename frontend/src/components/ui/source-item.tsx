import React, { FunctionComponent, useState } from "react";
import { Source } from "@/services/message";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { QuoteItem } from "@/components/ui/quote-item";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Markdown } from "@/components/ui/markdown";

interface SourceItemProps {
    source: Source;
    index: number;
}

export const SourceItem: FunctionComponent<SourceItemProps> = (props: SourceItemProps) => {
    const { source, index } = props;
    const [isSourceOpen, setIsSourceOpen] = useState(false);
    const { isMobile } = useMediaQuery();

    const { metadata, content } = source;

    const origin = metadata?.url || metadata?.origin || metadata.source;
    const title = metadata?.title || metadata?.heading || origin || content;
    const mimeType = metadata.mime_type || "";

    const renderContent = () => {
        if (mimeType === "image/png") {
            return (
                <div className="flex flex-col py-3">
                    <img src={`data:image/png;base64,${content}`} alt={String(title)} className="max-w-full h-auto" />
                    {!!origin && (
                        <div className="pt-1 flex flex-row justify-end italic">
                            <Markdown content={`- (${origin})`} />
                        </div>
                    )}
                </div>
            );
        }

        if (mimeType === "text/markdown") {
            return <QuoteItem content={content} origin={origin} />;
        }

        return <QuoteItem content={content} origin={origin} />;
    };

    return (
        <div className="px-1 py-1">
            <HoverCard>
                <HoverCardTrigger asChild>
                    <div className="flex flex-row border rounded-md hover:bg-muted hover:cursor-pointer">
                        <div className="w-5 h-full py-1 bg-muted text-center rounded-l-md">{index + 1}</div>
                        <div
                            className="px-1.5 w-[155px] h-full py-1 opacity-100 overflow-hidden text-ellipsis whitespace-nowrap"
                            onClick={() => {
                                if (isMobile) {
                                    setIsSourceOpen(true);
                                }
                            }}
                        >
                            {title}
                        </div>
                    </div>
                </HoverCardTrigger>
                <HoverCardContent className="hidden md:block md:w-[600px] md:max-h-[400px] overflow-scroll " avoidCollisions={true}>
                    {renderContent()}
                </HoverCardContent>
            </HoverCard>
            <Sheet open={isSourceOpen} onOpenChange={(value) => setIsSourceOpen(value)}>
                <SheetContent className="w-full h-full overflow-scroll py-3 px-8" side={"bottom"}>
                    {renderContent()}
                </SheetContent>
            </Sheet>
        </div>
    );
};
