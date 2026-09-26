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
    views: [
      {
        id: "source-metadata",
        label: "Document metadata",
        panel: "info",
        appKinds: ["manage"],
        features: ["source-editing"],
        load: function () {
          return import("./source-editor/source-metadata-view.js").then(function (module) {
            return module.createSourceMetadataView();
          });
        }
      },
      {
        id: "catalogue-token-info",
        label: "Semantic token",
        panel: "info",
        appKinds: ["manage"],
        features: ["source-editing"],
        load: function () {
          return import("./source-editor/catalogue-token-info-view.js")
            .then(function (module) {
              return module.createCatalogueTokenInfoView();
            });
        }
      }
    ],
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
        id: "manage-import",
        actionId: DOCS_VIEWER_ACTION_IDS.IMPORT,
        label: "Import",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-toolbar-import"
      },
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
        id: "manage-rebuild",
        actionId: DOCS_VIEWER_ACTION_IDS.REBUILD_DOCS,
        label: "Rebuild docs and Search",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-toolbar-rebuild"
      },
      {
        id: "manage-deploy-repo",
        actionId: DOCS_VIEWER_ACTION_IDS.DEPLOY_REPO,
        label: "Publish",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-toolbar-deploy-repo"
      },
      {
        id: "manage-prepare-preview",
        actionId: DOCS_VIEWER_ACTION_IDS.PREPARE_PREVIEW,
        label: "Prepare Preview",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-toolbar-prepare-preview"
      },
      {
        id: "manage-stage",
        label: "Docs stage",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["workspace-configuration"],
        renderer: "manage-stage-select"
      },
      {
        id: "index-selection",
        label: "Index selection",
        ownerType: "view",
        ownerViewId: "index-tree",
        surfaceId: "index-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-index-selection"
      },
      {
        id: "index-actions",
        label: "Index actions",
        ownerType: "view",
        ownerViewId: "index-tree",
        surfaceId: "index-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-index-actions"
      },
      {
        id: "index-position",
        label: "Position",
        ownerType: "view",
        ownerViewId: "index-tree",
        surfaceId: "index-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-index-position"
      },
      {
        id: "draft",
        actionId: "set-draft",
        label: "Draft readiness",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-draft"
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
        id: "open-vscode",
        actionId: DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE,
        label: "Open in VS Code",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-open-vscode"
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
