import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  directiveActionsControlDefinition
} from "./source-editor/directive-actions.js";

export function createDocsViewerManagementViewDefinitions() {
  return {
    views: [],
    modes: [{
      id: "markdown-source",
      features: ["source-editing"],
      label: "Markdown source",
      ownerViewId: "rendered-document",
      appKinds: ["manage"],
      load: function () {
        return import("./source-editor/source-editor.js")
          .then(function (module) {
            return module.createDocsViewerSourceEditorMode();
          });
      }
    }],
    controls: [
      {
        id: "manage-actions",
        label: "Actions",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-actions-menu"
      },
      {
        id: "edit",
        label: "Edit document",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management", "source-editing"],
        renderer: "manage-edit"
      },
      {
        id: "return-to-doc",
        label: "Return to doc",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "return-to-doc"
      },
      {
        id: "save-markdown-source",
        actionId: DOCS_VIEWER_ACTION_IDS.MARKDOWN_SAVE,
        label: "Save Markdown source",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-save"
      },
      directiveActionsControlDefinition()
    ]
  };
}
