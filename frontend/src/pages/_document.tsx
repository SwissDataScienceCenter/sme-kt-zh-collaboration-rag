import { Head, Html, Main, NextScript } from "next/document";
import { config } from "@/config";

export default function Document() {
    return (
        <Html lang="en" suppressHydrationWarning={true}>
            <title>{config.app.name}</title>
            <meta name="description" content={config.app.description} />
            <meta name="robots" content={config.app.robots} />
            <link rel="icon" href={config.app.favicon} />
            <Head />
            <body>
                <Main />
                <NextScript />
            </body>
        </Html>
    );
}
