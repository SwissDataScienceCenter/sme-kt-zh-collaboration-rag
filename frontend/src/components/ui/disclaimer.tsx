import React, { FunctionComponent } from "react";
import { useTranslation } from "react-i18next";
import { config } from "@/config";

export const Disclaimer: FunctionComponent = () => {
    const { t } = useTranslation("app");

    return <label className="text-center text-xs opacity-50 text-foreground pt-2">{t("disclaimer", { name: config.agent.name })}</label>;
};
