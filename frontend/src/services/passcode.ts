import { ApiService } from "./api";

class PasscodeService extends ApiService {
    constructor(apiUrl: string) {
        super(apiUrl);
    }

    async checkPasscode(passcode: string): Promise<null> {
        try {
            const postUrl = `${this.apiUrl}/passcode-check`;
            const response = await this.fetchApi(postUrl, {
                method: "POST",
                body: JSON.stringify({ passcode }),
            });

            return response.json();
        } catch (e) {
            console.log("error", e);
            return null;
        }
    }
}

export const passcodeService = new PasscodeService(process.env.SERVER_URL!);
