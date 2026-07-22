import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";

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
        id: "semantic-token-picker",
        features: ["source-editing"],
        label: "Semantic ref",
        panel: "info",
        appKinds: ["manage"],
        load: function () {
          return import("./source-editor/semantic-token-picker-view.js")
            .then(function (module) {
              return module.createSemanticTokenPickerView();
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
        label: "Select documents",
        ownerType: "view",
        ownerViewId: "index-tree",
        surfaceId: "index-view",
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-index-selection"
      },
      {
        id: "copy-subtree",
        actionId: DOCS_VIEWER_ACTION_IDS.COPY_SUBTREE,
        label: "Copy subtree to scope…",
        ownerType: "view",
        ownerViewId: "index-tree",
        surfaceId: "index-view",
        appKinds: ["manage"],
        features: ["management"],
        requiredCapabilities: ["copy_subtree.preview", "copy_subtree.apply"],
        renderer: "manage-copy-subtree"
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
        label: "Markdown source",
        ownerType: "view",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        surfaceId: "main-view",
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-toggle"
      }
    ]
  };
}
