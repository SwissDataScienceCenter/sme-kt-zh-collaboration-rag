import React, { FunctionComponent } from "react";
import { Theme, useTheme } from "@/hooks/useTheme";
import { config } from "@/config";
import { Trans, useTranslation } from "react-i18next";
import { cn } from "@/lib/lorem";

export const Footer: FunctionComponent = () => {
    const { theme } = useTheme();
    const { t } = useTranslation("app");

    const isDarkMode = theme === Theme.DARK;
    return (
        <div className="flex justify-center w-full py-2 px-2">
            <div className="flex flex-col items-center">
                <label className="text-xs opacity-50">{t("version", { version: config.app.version })}</label>
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
            </div>
        </div>
    );
};
