import React, { FunctionComponent } from "react";
import { useTranslation } from "react-i18next";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { DisplayLanguages, Languages } from "@/lib/lang/i18n";
import { Theme, useTheme } from "@/hooks/useTheme";
import { ArrowLeft } from "lucide-react";
import { Footer } from "@/components/sections/sidebar/footer";
import { useDisclaimer } from "@/hooks/useDisclaimer";

interface Props {
    onClickBack: () => void;
}

export const Settings: FunctionComponent<Props> = (props: Props) => {
    const { onClickBack } = props;
    const { t, i18n } = useTranslation("app");
    const { theme, changeTheme, cssClass } = useTheme();
    const { setDisclaimerIsOpen } = useDisclaimer();
    const isDarkMode = theme === Theme.DARK;

    const currentLanguage = i18n.language;

    return (
        <div className="text-foreground flex flex-col justify-between h-full">
            <div className="px-6 pt-6">
                <div className="flex flex-row items-center">
                    <ArrowLeft onClick={onClickBack} className="cursor-pointer hover:opacity-70" />
                    <div className="pl-4 text-2xl font-bold">{t("settings")}</div>
                </div>
                <div className="flex flex-col pt-10">
                    <div className="flex flex-row align-middle items-center pb-10">
                        <label className="text-sm pr-2">{`${t("language")}:`}</label>
                        <Select value={currentLanguage} onValueChange={(language) => i18n.changeLanguage(language)}>
                            <SelectTrigger className="w-[180px] transition-all duration-300">
                                <SelectValue defaultValue={"en"} />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    {Object.values(Languages).map((language) => (
                                        <SelectItem key={language} value={language}>
                                            {DisplayLanguages[language]}
                                        </SelectItem>
                                    ))}
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="flex flex-row align-middle items-center pb-10">
                        <label className="text-sm pr-2">{`${t("darkMode")}:`}</label>
                        <Switch
                            checked={isDarkMode}
                            onClick={() => {
                                changeTheme(isDarkMode ? Theme.LIGHT : Theme.DARK);
                            }}
                        />
                    </div>
                    <div className="flex flex-row align-middle items-center pb-10">
                        <label className="text-sm pr-2 hover:cursor-pointer underline text-blue-500" onClick={() => setDisclaimerIsOpen(true)}>{`${t(
                            "about",
                        )}`}</label>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
};
