import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  catalogueImageControlDefinition
} from "./source-editor/catalogue-image-contribution.js";
import { catalogueMediaLinkControlDefinition } from "./source-editor/catalogue-media-link.js";
import { documentLinkControlDefinition } from "./source-editor/document-link-contribution.js";
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
        actionId: DOCS_VIEWER_ACTION_IDS.EDIT_DOCUMENT,
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
        id: "source-add-image",
        actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_IMAGE,
        label: "Add image",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "source-add-image"
      },
      catalogueImageControlDefinition(),
      {
        id: "source-add-file",
        actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_ADD_FILE,
        label: "Add file",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "source-add-file"
      },
      catalogueMediaLinkControlDefinition(),
      documentLinkControlDefinition(),
      directiveActionsControlDefinition(),
      {
        id: "save-markdown-source",
        actionId: "markdown-save",
        label: "Save Markdown source",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-save"
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
      }
    ]
  };
}
