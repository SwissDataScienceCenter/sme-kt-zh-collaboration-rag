import React, { FunctionComponent } from "react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { config } from "@/config";

export const Welcome: FunctionComponent = () => {
    const { t } = useTranslation("app");

    return (
        <div className="flex flex-1 flex-col items-center justify-center pointer-events-none bg-background">
            <div className="p-3 bg-white rounded-full border border-primary/10 flex items-center justify-center">
                <Avatar>
                    <AvatarImage src={config.app.logo} alt="Logo" loading="lazy" />
                </Avatar>
            </div>
            <label className="pt-4 mb-5 text-2xl font-medium text-foreground">{t("welcome")}</label>
        </div>
    );
};
