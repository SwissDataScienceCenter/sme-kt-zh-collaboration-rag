"use client";
import React, { createContext, FunctionComponent, useContext, useState } from "react";

const DisclaimerContext = createContext<{
    isOpen: boolean;
    setDisclaimerIsOpen: (active: boolean) => void;
}>({
    isOpen: false,
    setDisclaimerIsOpen: () => {},
});

export const useDisclaimer = () => useContext(DisclaimerContext);

interface Props {
    children: React.ReactNode;
}

export const DisclaimerProvider: FunctionComponent<Props> = (props: Props) => {
    const { children } = props;

    const [hasBeenOpened, setHasBeenOpened] = useState(() => {
        if (typeof window !== "undefined") {
            return Boolean(window.localStorage.getItem("hasBeenOpened"));
        }
        return false;
    });

    const [isOpen, setIsOpen] = useState(!hasBeenOpened);

    const setDisclaimerIsOpen = (active: boolean) => {
        setIsOpen(() => active);
        if (!hasBeenOpened) {
            setHasBeenOpened(() => true);
            window.localStorage.setItem("hasBeenOpened", "true");
        }
    };

    return (
        <DisclaimerContext.Provider
            value={{
                setDisclaimerIsOpen,
                isOpen,
            }}
        >
            {children}
        </DisclaimerContext.Provider>
    );
};
