import "i18next";
import { defaultNS, resources } from "@/lib/lang/i18n";

declare module "i18next" {
    interface CustomTypeOptions {
        defaultNS: typeof defaultNS;
        resources: typeof resources["en"];
    }
}
