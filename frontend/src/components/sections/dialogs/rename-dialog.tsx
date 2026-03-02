import React, { FunctionComponent, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useTranslation } from "react-i18next";
import { useMessaging } from "@/hooks/useMessaging";

interface Props {
    isRenameDialogOpen: boolean;
    setIsRenameDialogOpen: (open: boolean) => void;
    conversationId: string;
}
export const RenameDialog: FunctionComponent<Props> = (props: Props) => {
    const { isRenameDialogOpen, setIsRenameDialogOpen, conversationId } = props;
    const { t } = useTranslation("app");
    const [value, setValue] = useState<string>("");
    const { renameConversation } = useMessaging();

    const handleSendRename = () => {
        renameConversation(conversationId, value);
        setIsRenameDialogOpen(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
            handleSendRename();
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setValue(e.target.value);
    };

    return (
        <Dialog open={isRenameDialogOpen} onOpenChange={setIsRenameDialogOpen}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{t("rename")}</DialogTitle>
                    <DialogDescription>{t("renameDescription")}</DialogDescription>
                    <div className="w-full pt-4">
                        <Input
                            placeholder={t("newName")}
                            onKeyDown={handleKeyDown}
                            onChange={(e) => {
                                handleInputChange(e);
                            }}
                            value={value}
                        />
                    </div>
                </DialogHeader>
                <DialogFooter>
                    <button type="submit" className="p-3 rounded-lg bg-primary text-primary-foreground text-sm ripple hover:bg-primary/70" onClick={handleSendRename}>
                        {t("confirm")}
                    </button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};
