import * as React from "react";
import { ChangeEvent, useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/lorem";
import { Input } from "@/components/ui/input";
import { debounce } from "@/lib/throttle";

export type Props = {
    onChange?: (value: string) => void;
    defaultValue?: string;
    className?: string;
};

export const SearchBar = (props: Props) => {
    const { onChange = () => {}, className, defaultValue = "" } = props;
    const { t } = useTranslation("app");
    const [value, setValue] = useState<string>(defaultValue);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const debouncedSearch = useCallback(
        debounce(onChange, 200),
        [onChange], // Add onEnter to the dependency array if it might change; otherwise, it can be omitted
    );

    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setValue(value);
        debouncedSearch(value);
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") {
            onChange(value);
        }
        debouncedSearch(value);
    };

    return (
        <div className={cn("relative w-full mt-3", className)}>
            <Input
                type="text"
                name="search"
                placeholder={t("search")}
                value={value}
                className="bg-input h-8 py-5 sm:py-0 px-5 pr-14 w-full rounded-full text-base sm:text-sm"
                onChange={handleChange}
                onKeyDown={handleKeyDown}
            />
            <div className="absolute content-center top-0 bottom-0 right-6">
                {value && (
                    <button
                        type="submit"
                        className="p-1 rounded-full ripple h-full"
                        onClick={() => {
                            setValue("");
                        }}
                    >
                        <X className="h-4 w-4" />
                    </button>
                )}
                <button type="submit" className="p-1 rounded-full ripple h-full">
                    <Search className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
};
