import React, { FunctionComponent } from "react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { cn } from "@/lib/lorem";

export interface Suggestion {
    text: string;
    subtext?: string;
}

interface Props {
    suggestions: Suggestion[];
    onClick: (input: string) => void;
    columns?: number;
}

export const Suggestions: FunctionComponent<Props> = (props: Props) => {
    const { suggestions, onClick, columns = 2 } = props;
    const { isMobile } = useMediaQuery();

    const hasOddNumberOfElements = suggestions.length % 2 !== 0;

    const firstSuggestions = hasOddNumberOfElements ? suggestions.slice(0, -1) : suggestions;
    const lastSuggestion = suggestions[suggestions.length - 1];
    if (isMobile) {
        return (
            <div className="flex w-max">
                {suggestions.map((suggestion) => (
                    <div className="pl-2 first:pl-0 w-[320px]" key={suggestion.text}>
                        <SuggestionElement key={suggestion.text} {...suggestion} onClick={onClick} />
                    </div>
                ))}
            </div>
        );
    }
    return (
        <div className="flex flex-col w-full">
            <div className="grid grid-cols-2 gap-2">
                {firstSuggestions.map((suggestion, index) => (
                    <SuggestionElement key={suggestion.text} {...suggestion} onClick={onClick} />
                ))}
            </div>
            {hasOddNumberOfElements && (
                <div className="grid grid-cols-1 gap-2 pt-2">
                    <SuggestionElement key={lastSuggestion.text} {...lastSuggestion} onClick={onClick} />
                </div>
            )}
        </div>
    );
};

interface SuggestionElement extends Suggestion {
    onClick?: (input: string) => void;
    className?: string;
}

export const SuggestionElement: FunctionComponent<SuggestionElement> = (props: SuggestionElement) => {
    const { text, subtext, onClick, className } = props;
    return (
        <div className={cn("p-4 border border-border bg-card rounded-lg ripple hover:cursor-pointer", className)} onClick={() => onClick && onClick(`${text} ${subtext}`)}>
            <div className="text-sm text-ellipsis text-foreground">{text}</div>
            <div className="opacity-50 text-xs text-ellipsis text-nowrap whitespace-nowrap overflow-hidden text-foreground">{subtext}</div>
        </div>
    );
};
