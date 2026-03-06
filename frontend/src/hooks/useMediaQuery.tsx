"use client"
import { createContext, useContext, useEffect, useState } from "react";
import { debounce, throttle } from "@/lib/throttle";

const MediaContext = createContext<{
    isMobile: boolean | null;
}>({
    isMobile: null,
});

interface Props {
    children: React.ReactNode;
}

export const useMediaQuery = () => useContext(MediaContext);

interface Props {
    children: React.ReactNode;
    waitMs: number;
}

export const MediaQueryProvider = (props: Props) => {
    const {children, waitMs} = props;

    const minPixels = 768;

    const [matches, setMatches] = useState(
        typeof window !== "undefined" && window.matchMedia(`(min-width: ${minPixels}px)`).matches,
    );

    useEffect(() => {
        const throttledMatch = throttle(() => {
            const media = window.matchMedia(`(min-width: ${minPixels}px)`);
            if (media.matches !== matches) {
                setMatches(media.matches)
            }

        }, waitMs)
        const debouncedMatch = debounce(() => {
            const media = window.matchMedia(`(min-width: ${minPixels}px)`);
            if (media.matches !== matches) {
                setMatches(media.matches)
            }
        }, waitMs)


        const listener = () => {
            throttledMatch()
            debouncedMatch()
        }
        window.addEventListener("resize", listener);
        return () => window.removeEventListener("resize", listener);
    }, [matches, minPixels, waitMs]);

    return <MediaContext.Provider
        value={{
            isMobile: !matches,
        }}
    >
        {children}
    </MediaContext.Provider>;
}
