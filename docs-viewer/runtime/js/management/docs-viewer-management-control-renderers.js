import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

function renderDocumentActionButton(context, options) {
  var settings = options || {};
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.id = settings.id || "";
    button.type = "button";
  }
  var artwork = typeof settings.artwork === "function"
    ? settings.artwork(context.control.state || {})
    : settings.artwork;
  button.className = "docsViewer__toolbarIconButton";
  button.replaceChildren();
  if (artwork) button.appendChild(createDocsViewerToolbarIcon(context.document, artwork));
  return button;
}

export function createDocsViewerManagementControlRenderers() {
  return {
    "manage-edit": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageEditButton",
        artwork: "docsViewer__icon--pen"
      });
    },
    "manage-draft": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageDraftButton",
        artwork: function (state) { return state.pressed === true ? "docsViewer__icon--circle-dashed-check" : "docsViewer__icon--circle-check"; }
      });
    },
    "manage-selected": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSelectedButton",
        artwork: function (state) { return state.pressed === true ? "docsViewer__icon--star-filled" : "docsViewer__icon--star"; }
      });
    },
    "manage-open-vscode": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageOpenVsCodeButton",
        artwork: "docsViewer__icon--file-code-corner"
      });
    },
    "return-to-doc": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageReturnToDocButton",
        artwork: "docsViewer__icon--corner-down-left"
      });
    },
    "markdown-source-save": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceSaveButton",
        artwork: "docsViewer__icon--download"
      });
    },
    "source-add-image": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddImageButton",
        artwork: "docsViewer__icon--image"
      });
    },
    "source-add-file": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceAddFileButton",
        artwork: "docsViewer__icon--paperclip"
      });
    }
  };
}
