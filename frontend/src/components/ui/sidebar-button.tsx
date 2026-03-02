import React, { FunctionComponent, useState } from "react";
import { MoreHorizontal, Pencil, Trash } from "lucide-react";
import { cn } from "@/lib/lorem";
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuTrigger } from "./dropdown-menu";
import { useTranslation } from "react-i18next";
import { RenameDialog } from "@/components/sections/dialogs/rename-dialog";
import { DeleteDialog } from "@/components/sections/dialogs/delete-dialog";

interface Props {
    conversationId: string;
    label: string;
    isSelected: boolean;
    onClick: () => void;
    className?: string;
}

export const SidebarButton: FunctionComponent<Props> = (props: Props) => {
    const { className, label, onClick, isSelected, conversationId } = props;
    const [isHover, setIsHover] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

    const { t } = useTranslation("app");

    const isActive = isHover || isSelected || isDropdownOpen;

    const handleClickDelete = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
        setIsDeleteDialogOpen(true);
    };
    const handleClickRename = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
        setIsRenameDialogOpen(true);
    };

    return (
        <div>
            <div
                className={cn("flex py-2 px-4 mx-2 cursor-pointer rounded-md", className, isSelected ? "bg-foreground/15" : isActive ? "bg-foreground/5" : "")}
                onClick={() => {
                    if (!isDropdownOpen) {
                        onClick();
                    }
                }}
                onMouseEnter={() => setIsHover(true)}
                onMouseLeave={() => setIsHover(false)}
            >
                <div className="flex flex-row justify-between w-full items-center ">
                    <div className="flex text-foreground text-sm text-ellipsis text-nowrap whitespace-nowrap overflow-hidden w-full">{label}</div>
                    <DropdownMenu onOpenChange={setIsDropdownOpen}>
                        <DropdownMenuTrigger asChild>{isActive && <MoreHorizontal className="h-4 w-7 rounded-md hover:opacity-55" />}</DropdownMenuTrigger>
                        <DropdownMenuContent className="w-48" side="bottom" align="start">
                            <DropdownMenuGroup>
                                <DropdownMenuItem onClick={handleClickRename} className="py-3">
                                    <Pencil className="h-4 w-4 mr-2" />
                                    <span>{t("rename")}</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={handleClickDelete} className="py-3">
                                    <Trash className="h-4 w-4 mr-2" />
                                    <span>{t("delete")}</span>
                                </DropdownMenuItem>
                            </DropdownMenuGroup>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
            <RenameDialog isRenameDialogOpen={isRenameDialogOpen} setIsRenameDialogOpen={setIsRenameDialogOpen} conversationId={conversationId} />
            <DeleteDialog isDeleteDialogOpen={isDeleteDialogOpen} setIsDeleteDialogOpen={setIsDeleteDialogOpen} conversationId={conversationId} />
        </div>
    );
};
