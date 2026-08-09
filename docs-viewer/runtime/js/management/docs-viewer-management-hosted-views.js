import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  catalogueImageControlDefinition
} from "./source-editor/catalogue-image-contribution.js";
import {
  catalogueTokenControlDefinition
} from "./source-editor/catalogue-token-contribution.js";
import {
  directiveActionsControlDefinition
} from "./source-editor/directive-actions.js";
import {
  subjectLinkControlDefinition
} from "./source-editor/subject-link-contribution.js";

export function createDocsViewerManagementViewDefinitions() {
  return {
    views: [
      {
        id: "index-graph",
        label: "Index graph",
        panel: "index",
        appKinds: ["manage"],
        renderer: "index-placeholder",
        placeholderText: "Graph index placeholder",
        capabilities: {
          layoutStates: ["normal", "collapsed", "expanded"]
        }
      },
      {
        id: "catalogue-token-info",
        label: "Catalogue token",
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
        id: "manage-publish",
        actionId: DOCS_VIEWER_ACTION_IDS.PUBLISH_DOCS,
        label: "Publish",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-toolbar-publish"
      },
      {
        id: "manage-scope",
        label: "Docs scope",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["scope-selection"],
        renderer: "manage-scope-select"
      },
      {
        id: "manage-theme",
        label: "Switch to dark mode",
        ownerType: "app",
        surfaceId: "app-management",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-theme-toggle"
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
        id: "edit",
        actionId: "edit-metadata",
        label: "Edit",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["management"],
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
      catalogueTokenControlDefinition(),
      subjectLinkControlDefinition(),
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
        id: "markdown-source",
        actionId: "markdown-source",
        label: "Source",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-entry"
      },
      {
        id: "subdoc-source",
        actionId: "markdown-source",
        label: "Subdoc Source",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "subdoc-source-entry"
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
