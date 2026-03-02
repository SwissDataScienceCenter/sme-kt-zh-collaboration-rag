import * as i18nModule from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import * as en from "./en";
import * as fr from "./fr";
import * as it from "./it";
import * as de from "./de";

const i18n = i18nModule;

export enum Languages {
    EN = "en",
    FR = "fr",
    DE = "de",
    IT = "it",
}

export const DisplayLanguages = {
    [Languages.EN]: "English",
    [Languages.FR]: "Français",
    [Languages.DE]: "Deutsch",
    [Languages.IT]: "Italiano",
};

export const defaultNS = "app";

export const resources = {
    en,
    fr,
    it,
    de,
};

export namespace Translation {
    export const init = () => {
        i18n.use(LanguageDetector)
            .use(initReactI18next)
            .init({
                detection: {
                    caches: ["localStorage"],
                    cookieMinutes: 365 * 24 * 60 * 60 * 1000,
                    convertDetectedLanguage: (language) => {
                        if (language) {
                            const shortLanguage = language.split("-")[0];
                            if (Object.values(Languages).includes(shortLanguage as Languages)) {
                                return shortLanguage;
                            }
                        }
                        return Languages.FR;
                    },
                },
                defaultNS,
                resources,
                ns: ["app"],
                fallbackLng: "en",
                returnEmptyString: false,
                interpolation: {
                    escapeValue: false,
                },
                returnNull: false,
            });
    };
}

export const translate = i18n.t;
