import {
  setCatalogueEditorTextWithState
} from "./catalogue-editor-route-boot.js";

function normalizeText(value) {
  return value == null ? "" : String(value).trim();
}

function normalizeMessageTone(tone) {
  const normalized = normalizeText(tone).toLowerCase();
  if (normalized === "warning") return "warn";
  return normalized;
}

export function makeCatalogueEditorMessage(text, tone = "") {
  return {
    text: normalizeText(text),
    tone: normalizeMessageTone(tone)
  };
}

export function createCatalogueEditorMessageRoleNode(id, role) {
  return {
    id,
    catalogueEditorMessageRole: role,
    textContent: "",
    dataset: {}
  };
}

function setRoleNodeText(node, message) {
  if (!node || !node.catalogueEditorMessageRole) return;
  node.textContent = message.text;
  if (message.tone) node.dataset.state = message.tone;
  else delete node.dataset.state;
}

function messageRoleForNode(statusNode, node) {
  if (node === statusNode) return "status";
  if (node && node.catalogueEditorMessageRole) return node.catalogueEditorMessageRole;
  if (node && node.catalogueWorkMessageRole) return node.catalogueWorkMessageRole;
  return "";
}

export function firstCatalogueEditorMessage(messages) {
  return messages.find((message) => message && message.text) || null;
}

export function firstCatalogueValidationMessage(errors) {
  if (!errors || !errors.size) return "";
  const first = errors.values().next();
  return first.done ? "" : normalizeText(first.value);
}

export function clearCatalogueFieldStatusMessages(fieldStatusNodes, setTextWithState = setCatalogueEditorTextWithState) {
  if (!fieldStatusNodes || typeof fieldStatusNodes.forEach !== "function") return;
  fieldStatusNodes.forEach((node) => {
    setTextWithState(node, "");
    node.hidden = true;
  });
}

export function createCatalogueEditorMessageController(options) {
  const statusNode = options.statusNode;
  const setNodeTextWithState = options.setTextWithState || setCatalogueEditorTextWithState;
  let defaultMessage = makeCatalogueEditorMessage("");
  let actionStatusMessage = makeCatalogueEditorMessage("");
  let actionResultMessage = makeCatalogueEditorMessage("");

  function setVisibleMessage(message) {
    const next = message && message.text ? message : makeCatalogueEditorMessage("");
    setNodeTextWithState(statusNode, next.text, next.tone);
  }

  function clearActionMessages() {
    actionStatusMessage = makeCatalogueEditorMessage("");
    actionResultMessage = makeCatalogueEditorMessage("");
  }

  function setMessageForRole(node, message, options = {}) {
    const role = messageRoleForNode(statusNode, node);
    if (!role) {
      setNodeTextWithState(node, message.text, message.tone);
      return;
    }
    if (role === "status") {
      if (options.action) {
        actionStatusMessage = message;
      } else {
        defaultMessage = message;
        if (message.text) actionStatusMessage = makeCatalogueEditorMessage("");
      }
    } else if (role === "result") {
      actionResultMessage = message;
    } else if (role === "warning" && message.text) {
      actionStatusMessage = message;
    } else if (role === "context" && message.text && message.tone) {
      actionStatusMessage = message;
    }
    setRoleNodeText(node, message);
  }

  function setRouteTextWithState(node, text, tone = "") {
    setMessageForRole(node, makeCatalogueEditorMessage(text, tone), { action: false });
    render();
  }

  function setActionTextWithState(node, text, tone = "") {
    setMessageForRole(node, makeCatalogueEditorMessage(text, tone), { action: true });
    render();
  }

  function render(snapshot = {}) {
    const busy = Boolean(snapshot.busy);
    const pendingAction = busy && actionStatusMessage.text ? actionStatusMessage : null;
    const highPriorityAction = firstCatalogueEditorMessage([
      ["error", "warn"].includes(actionResultMessage.tone) ? actionResultMessage : null,
      ["error", "warn"].includes(actionStatusMessage.tone) ? actionStatusMessage : null
    ]);
    const validationMessage = snapshot.validationMessage
      ? makeCatalogueEditorMessage(snapshot.validationMessage, snapshot.validationTone || "error")
      : null;
    const mixedMessage = snapshot.mixedMessage
      ? makeCatalogueEditorMessage(snapshot.mixedMessage, snapshot.mixedTone || "warn")
      : null;
    const dirtyMessage = snapshot.dirtyMessage
      ? makeCatalogueEditorMessage(snapshot.dirtyMessage, snapshot.dirtyTone || "warn")
      : null;
    const lowPriorityAction = firstCatalogueEditorMessage([actionResultMessage, actionStatusMessage]);
    setVisibleMessage(firstCatalogueEditorMessage([
      pendingAction,
      highPriorityAction,
      validationMessage,
      mixedMessage,
      dirtyMessage,
      lowPriorityAction,
      defaultMessage
    ]));
  }

  return {
    clearActionMessages,
    render,
    setActionTextWithState,
    setRouteTextWithState,
    setDefaultMessage: (text, tone = "") => {
      defaultMessage = makeCatalogueEditorMessage(text, tone);
      render();
    },
    get defaultMessage() {
      return defaultMessage;
    },
    get actionStatusMessage() {
      return actionStatusMessage;
    },
    get actionResultMessage() {
      return actionResultMessage;
    },
    get hasActionMessages() {
      return Boolean(actionStatusMessage.text || actionResultMessage.text);
    }
  };
}

export function bindCatalogueEditorActionMessageClearer(root, messageController, options = {}) {
  if (!root || !messageController || typeof messageController.clearActionMessages !== "function") {
    return () => undefined;
  }

  const isBusy = typeof options.isBusy === "function" ? options.isBusy : () => false;
  const ignoreEvent = typeof options.ignoreEvent === "function" ? options.ignoreEvent : () => false;
  const renderMessages = typeof options.renderMessages === "function"
    ? options.renderMessages
    : () => messageController.render();

  function onRootClick(event) {
    if (ignoreEvent(event)) return;
    if (isBusy()) return;
    if (!messageController.hasActionMessages) return;
    messageController.clearActionMessages();
    renderMessages();
  }

  root.addEventListener("click", onRootClick, { capture: true });
  return () => root.removeEventListener("click", onRootClick, { capture: true });
}
