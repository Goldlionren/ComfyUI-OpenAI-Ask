import { app } from "/scripts/app.js";

const NODE_TYPE = "JRStringToList";
const INPUT_NAME = /^text_([1-9]\d*)$/;

function textInputs(node) {
    return (node.inputs || []).filter((input) => INPUT_NAME.test(input.name));
}

function resize(node) {
    if (typeof node.computeSize === "function" && typeof node.setSize === "function") {
        node.setSize(node.computeSize());
    }
    node.setDirtyCanvas?.(true, true);
}

function addTextInput(node) {
    const next = Math.max(0, ...textInputs(node).map((input) => Number(INPUT_NAME.exec(input.name)[1]))) + 1;
    node.addInput(`text_${next}`, "STRING");
    resize(node);
}

function removeLastUnusedInput(node) {
    const inputs = textInputs(node);
    if (inputs.length <= 1 || inputs[inputs.length - 1].link != null) return;
    node.removeInput(node.inputs.indexOf(inputs[inputs.length - 1]));
    resize(node);
}

app.registerExtension({
    name: "JR.OpenAIAsk.DynamicStringToList",
    nodeCreated(node) {
        if (![node.comfyClass, node.type, node.constructor?.type].includes(NODE_TYPE)) return;
        if (node.__jrStringListInitialized) return;
        node.__jrStringListInitialized = true;

        node.addWidget("button", "+ Add STRING", null, () => addTextInput(node));
        node.addWidget("button", "- Remove last unused", null, () => removeLastUnusedInput(node));

        const previousOnConnectionsChange = node.onConnectionsChange;
        node.onConnectionsChange = function (kind, slot, connected, linkInfo, ioSlot) {
            const result = previousOnConnectionsChange?.apply(this, arguments);
            // LiteGraph INPUT=1. Keep one spare port when every STRING port is connected.
            if (kind === 1 && connected === true) {
                const inputs = textInputs(this);
                if (inputs.length > 0 && inputs.every((input) => input.link != null)) {
                    addTextInput(this);
                }
            }
            return result;
        };
    },
});
