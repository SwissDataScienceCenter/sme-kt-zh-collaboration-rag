import React, { FunctionComponent } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Trans, useTranslation } from "react-i18next";
import { useDisclaimer } from "@/hooks/useDisclaimer";
import { config } from "@/config";
import { cn } from "@/lib/lorem";
import { Theme, useTheme } from "@/hooks/useTheme";
import { Languages } from "@/lib/lang/i18n";

export const DisclaimerDialog: FunctionComponent = () => {
    const { t, i18n } = useTranslation("app");
    const { theme } = useTheme();
    const isDarkMode = theme === Theme.DARK;
    const currentLanguage = i18n.language as Languages;

    const { isOpen, setDisclaimerIsOpen } = useDisclaimer();

    return (
        <Dialog open={isOpen} onOpenChange={setDisclaimerIsOpen}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{t("informationDialog.title")}</DialogTitle>
                </DialogHeader>
                <DialogDescription>
                    <Trans
                        i18nKey="informationDialog.goal"
                        values={{ name: config.agent.name }}
                        components={{
                            1: <a className="font-bold" />,
                        }}
                    />
                    <br />
                    <br />
                    <Trans i18nKey="informationDialog.document" />
                    <br />
                    <br />
                    {t("informationDialog.languages")}
                    <br />
                    <br />
                    {t("informationDialog.beta")}
                    <br />
                    <br />
                    {t("informationDialog.logging")}
                </DialogDescription>

                <div className="text-xs opacity-50 text-center">
                    <Trans
                        i18nKey="credits"
                        values={{ name: config.agent.name, sdsc: "SDSC" }}
                        components={{
                            1: (
                                <a
                                    className={cn("cursor-pointer pl-[4px]", isDarkMode ? "text-green-600" : "text-green-600")}
                                    href="https://www.datascience.ch/"
                                    rel="noreferrer"
                                />
                            ),
                        }}
                    />
                </div>
            </DialogContent>
        </Dialog>
    );
};
