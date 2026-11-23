import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { renderDocsViewerEditMenu } from "./docs-viewer-management-edit-menu.js";
import { SOURCE_BOLD_CONTROL_ID } from "./source-editor/source-editor-bold.js";

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
    "recent-exclusions-open": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerRecentExclusionsOpenButton",
        artwork: "docsViewer__icon--file-code-corner"
      });
    },
    "manage-edit": renderDocsViewerEditMenu,
    "collection-open-source": function (context) {
      return renderDocumentActionButton(context, {
        artwork: "docsViewer__icon--square-code"
      });
    },
    "return-to-doc": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageReturnToDocButton",
        artwork: "docsViewer__icon--corner-down-left"
      });
    },
    "return-to-collection": function (context) {
      return renderDocumentActionButton(context, {
        artwork: "docsViewer__icon--list"
      });
    },
    "markdown-source-save": function (context) {
      return renderDocumentActionButton(context, {
        id: "docsViewerManageSourceSaveButton",
        artwork: "docsViewer__icon--download"
      });
    },
    [SOURCE_BOLD_CONTROL_ID]: function (context) {
      return renderDocumentActionButton(context, { artwork: "docsViewer__icon--bold" });
    },
    "source-add-date": function (context) {
      var button = renderDocumentActionButton(context, {
        artwork: "docsViewer__icon--calendar"
      });
      button.setAttribute("aria-haspopup", "dialog");
      return button;
    }
  };
}
