import React, { FunctionComponent } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useTranslation } from "react-i18next";
import { useMessaging } from "@/hooks/useMessaging";

interface Props {
    isDeleteDialogOpen: boolean;
    setIsDeleteDialogOpen: (open: boolean) => void;
    conversationId: string;
}
export const DeleteDialog: FunctionComponent<Props> = (props: Props) => {
    const { isDeleteDialogOpen, setIsDeleteDialogOpen, conversationId } = props;
    const { t } = useTranslation("app");
    const { deleteConversation } = useMessaging();

    const handleDelete = () => {
        deleteConversation(conversationId);
        setIsDeleteDialogOpen(false);
    };

    const handleCancel = () => {
        setIsDeleteDialogOpen(false);
    };

    return (
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{t("delete")}</DialogTitle>
                    <DialogDescription>{t("deleteDescription")}</DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <button type="submit" className="p-3 rounded-lg border-0 bg-transparent text-primary text-sm ripple" onClick={handleCancel}>
                        {t("cancel")}
                    </button>
                    <button type="submit" className="p-3 rounded-lg bg-primary text-primary-foreground text-sm ripple hover:bg-primary/70" onClick={handleDelete}>
                        {t("confirm")}
                    </button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};
