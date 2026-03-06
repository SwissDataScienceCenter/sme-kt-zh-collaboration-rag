"use client";

import { passcodeService } from "@/services/passcode";
import React from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { config } from "@/config";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useTranslation } from "react-i18next";

export default function Passcode() {
    const { t } = useTranslation("app");
    const [passcode, setPasscode] = React.useState("");

    const handlePasscodeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setPasscode(event.target.value);
    };

    const handlePasscodeSubmit = async () => {
        if (passcode) {
            try {
                const response = await passcodeService.checkPasscode(passcode);
            } catch (error) {
                console.error("Error verifying passcode:", error);
            }
            window.location.href = process.env.SERVER_URL || "/";
        }
    };

    return (
        <div className="flex h-screen w-screen items-center justify-center">
            <Card className="w-[350px]">
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <Avatar>
                            <AvatarImage src={config.app.logo} alt="Logo" loading="lazy" />
                        </Avatar>
                        <div className="flex pl-2 font-bold text-foreground">{config.agent.name}</div>
                    </CardTitle>
                    <CardDescription>{t("enterPasscode")}</CardDescription>
                </CardHeader>
                <CardContent>
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            handlePasscodeSubmit();
                        }}
                    >
                        <div className="grid w-full items-center gap-4">
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="name">{t("passcode")}</Label>
                                <Input id="name" value={passcode} placeholder="***********" onChange={handlePasscodeChange} type={"password"} />
                            </div>
                        </div>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-end">
                    <button
                        type="submit"
                        className="p-3 min-w-[70px] rounded-lg bg-primary text-primary-foreground text-sm ripple hover:bg-primary/70"
                        onClick={handlePasscodeSubmit}
                    >
                        {t("send")}
                    </button>
                </CardFooter>
            </Card>
        </div>
    );
}
