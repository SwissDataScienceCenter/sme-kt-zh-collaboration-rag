import React, { FunctionComponent, useState } from "react";
import { cn } from "@/lib/lorem";
import { SidebarContent } from "@/components/sections/sidebar/sidebar-content";

const SIDEBAR_SIZE = 280;

enum SidebarTickState {
    OPEN = "open",
    CLOSE = "close",
    DEFAULT = "default",
}

export const Sidebar: FunctionComponent = (props) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [state, setState] = useState<SidebarTickState>(SidebarTickState.DEFAULT);

    const handleSidebarToggle = () => {
        setIsSidebarOpen((prev) => !prev);
    };

    const styles = {
        [SidebarTickState.DEFAULT]: {
            top: "translateY(0.14rem) rotate(0deg) translateZ(0px)",
            bottom: "translateY(-0.14rem) rotate(0deg) translateZ(0px)",
        },
        [SidebarTickState.OPEN]: {
            top: "translateY(0.14rem) rotate(-15deg) translateZ(0px)",
            bottom: "translateY(-0.14rem) rotate(15deg) translateZ(0px)",
        },
        [SidebarTickState.CLOSE]: {
            top: "translateY(0.14rem) rotate(15deg) translateZ(0px)",
            bottom: "translateY(-0.14rem) rotate(-15deg) translateZ(0px)",
        },
    };

    return (
        <>
            <div className={cn("bg-muted flex-shrink-0 overflow-x-hidden transition-all duration-300")} style={{ width: isSidebarOpen ? `${SIDEBAR_SIZE}px` : "0px" }}>
                <div className="h-full" style={{ minWidth: `${SIDEBAR_SIZE}px` }}>
                    <SidebarContent />
                </div>
            </div>
            <div
                className={cn("fixed top-1/2 z-[50] transition-all duration-300 hover:cursor-pointer bg-transparent")}
                style={{ left: isSidebarOpen ? `${SIDEBAR_SIZE}px` : "0px" }}
                onClick={handleSidebarToggle}
                onMouseEnter={() => setState(isSidebarOpen ? SidebarTickState.CLOSE : SidebarTickState.OPEN)}
                onMouseLeave={() => setState(isSidebarOpen ? SidebarTickState.DEFAULT : SidebarTickState.OPEN)}
            >
                <div className="flex h-[72px] w-6 items-center justify-center">
                    <div className="flex h-6 w-6 flex-col items-center">
                        <div className="h-3 w-1 rounded-full bg-muted-foreground transition-all duration-300" style={{ transform: styles[state].top }} />
                        <div className="h-3 w-1 rounded-full bg-muted-foreground transition-all duration-300" style={{ transform: styles[state].bottom }} />
                    </div>
                </div>
            </div>
        </>
    );
};
