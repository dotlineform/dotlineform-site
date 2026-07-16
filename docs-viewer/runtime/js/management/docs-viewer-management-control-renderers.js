function renderDocumentActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = settings.id || "";
    button.type = "button";
  }
  button.textContent = typeof settings.emoji === "function"
    ? settings.emoji(context.control.state || {})
    : settings.emoji || "";
  return button;
}

export function createDocsViewerManagementControlRenderers() {
  return {
    "manage-copy-subtree": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageCopySubtreeButton",
        emoji: "⧉"
      });
    },
    "manage-edit": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageEditButton",
        emoji: "✏️"
      });
    },
    "manage-open-vscode": function (context) {
      var button = renderDocumentActionButton(context, {
        id: "docsViewerManageOpenVsCodeButton",
        emoji: ""
      });
      var icon = context.document.createElement("img");
      icon.src = new URL("./icons/vscode.svg", import.meta.url).href;
      icon.alt = "";
      icon.width = 20;
      icon.height = 20;
      icon.setAttribute("aria-hidden", "true");
      button.replaceChildren(icon);
      return button;
    },
    "markdown-source-toggle": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceButton",
        emoji: function (state) { return state.pressed ? "📄" : "☰"; }
      });
    },
    "markdown-source-save": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceSaveButton",
        emoji: "💾"
      });
    }
  };
}
