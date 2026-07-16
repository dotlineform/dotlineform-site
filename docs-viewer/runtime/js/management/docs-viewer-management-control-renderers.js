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
    "manage-edit": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageEditButton",
        emoji: "✏️"
      });
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
