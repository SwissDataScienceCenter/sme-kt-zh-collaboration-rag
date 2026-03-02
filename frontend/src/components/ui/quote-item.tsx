import React, { FunctionComponent } from "react";
import { Markdown } from "@/components/ui/markdown";

interface Props {
    content: string;
    origin?: string;
}

export const QuoteItem: FunctionComponent<Props> = (props: Props) => {
    const { content, origin } = props;

    const hasOrigin = origin !== undefined;

    return (
        <div className="quote">
            <div className="flex flex-col py-3">
                <Markdown content={content} />
                {hasOrigin && (
                    <div className="pt-1 flex flex-row justify-end italic">
                        <Markdown content={`- (${origin})`} />
                    </div>
                )}
            </div>
        </div>
    );
};
