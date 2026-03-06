import React, { FunctionComponent, useState } from "react";
import { History } from "@/components/sections/sidebar/history";
import { Settings } from "@/components/sections/sidebar/settings";

interface Props {
    onChangeConversation?: (conversationId: string) => void;
}

enum States {
    HISTORY,
    SETTINGS,
}

export const SidebarContent: FunctionComponent<Props> = (props) => {
    const { onChangeConversation } = props;
    const [state, setState] = useState(States.HISTORY);

    const onClickSettings = () => {
        setState(States.SETTINGS);
    };

    const onClickBack = () => {
        setState(States.HISTORY);
    };

    if (state === States.HISTORY) {
        return <History onClickSettings={onClickSettings} onChangeConversation={onChangeConversation} />;
    }

    if (state === States.SETTINGS) {
        return <Settings onClickBack={onClickBack} />;
    }
};
