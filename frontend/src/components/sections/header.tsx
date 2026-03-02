import React, { FunctionComponent, useState } from "react";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { MenuIcon, SquarePen } from "lucide-react";
import { SidebarContent } from "@/components/sections/sidebar/sidebar-content";
import { cn } from "@/lib/lorem";
import { config } from "@/config";
import { useMessaging } from "@/hooks/useMessaging";

export const Header: FunctionComponent = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { createNewConversation, activeConversationId } = useMessaging();

    return (
        <div className="fixed left-0 top-0 right-0 flex items-center justify-between p-4 bg-background z-20">
            <div className="flex flex-row align-middle items-center text-foreground cursor-pointer">
                <MenuIcon onClick={() => setIsMenuOpen((prev) => !prev)} />
            </div>
            <div className="flex flex-row align-middle items-center">
                <Avatar className="h-10 w-10 p-1 bg-white rounded-full border border-primary/10 flex items-center justify-center f">
                    <AvatarImage src={config.app.logo} alt="Logo" loading="lazy" />
                </Avatar>
                <div className="text-xl flex pl-2 font-bold text-foreground cursor-default">{config.app.name}</div>
            </div>
            <div className={cn("flex flex-row align-middle items-center text-foreground cursor-pointer", activeConversationId ? "text-foreground" : "text-foreground/50")}>
                <SquarePen onClick={createNewConversation} />
            </div>
            <Sheet open={isMenuOpen} onOpenChange={(value) => setIsMenuOpen(value)}>
                <SheetContent
                    className="w-full h-full"
                    side={"left"}
                    autoFocus={false}
                    onOpenAutoFocus={(e) => {
                        e.preventDefault();
                    }}
                >
                    <SidebarContent
                        onChangeConversation={() => {
                            setIsMenuOpen(false);
                        }}
                    />
                </SheetContent>
            </Sheet>
        </div>
    );
};
