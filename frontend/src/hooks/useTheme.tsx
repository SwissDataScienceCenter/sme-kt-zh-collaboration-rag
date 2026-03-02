"use client";
import { createContext, FunctionComponent, useContext, useEffect, useState } from "react";

export enum Theme {
    SYSTEM = "system",
    LIGHT = "light",
    DARK = "dark",
}

const ThemeContext = createContext<{
    theme: Theme;
    cssClass: string;
    changeTheme: (theme: Theme) => void;
}>({
    theme: Theme.LIGHT,
    cssClass: "",
    changeTheme: (theme: Theme) => {},
});

interface Props {
    children: React.ReactNode;
}

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider: FunctionComponent<Props> = (props: Props) => {
    const { children } = props;

    const [theme, setTheme] = useState(() => {
        if (typeof window !== "undefined") {
            const savedTheme = window.localStorage.getItem("theme");
            return savedTheme ? (savedTheme as Theme) : Theme.LIGHT;
        }
        return Theme.LIGHT; // Default value when window is not available
    });

    const getCssClass = (theme: Theme) => {
        switch (theme) {
            case Theme.LIGHT:
                return "";
            case Theme.DARK:
                return "dark";
            case Theme.SYSTEM:
                const { matches } = window.matchMedia("(prefers-color-scheme: dark)");
                return matches ? "dark" : "";
            default:
                return "";
        }
    };

    const [cssClass, setCssClass] = useState(getCssClass(theme));

    const changeTheme = (theme: Theme) => {
        setTheme(() => theme);
        window.localStorage.setItem("theme", theme);
    };

    useEffect(() => {
        const listener = (event: MediaQueryListEvent) => {
            if (event.matches) {
                setCssClass(getCssClass(Theme.DARK));
            } else {
                setCssClass(getCssClass(Theme.LIGHT));
            }
        };
        if (theme === Theme.SYSTEM) {
            window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", listener);
            return () => window.matchMedia("(prefers-color-scheme: dark)").removeEventListener("change", listener);
        }
        setCssClass(getCssClass(theme));
    }, [theme, cssClass]);

    useEffect(() => {
        const body = document.querySelector("body");
        if (body) {
            body.className = cssClass;
        }
    }, [cssClass]);

    return (
        <ThemeContext.Provider
            value={{
                theme,
                cssClass,
                changeTheme,
            }}
        >
            {children}
        </ThemeContext.Provider>
    );
};
