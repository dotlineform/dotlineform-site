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
          layoutStates: ["normal", "collapsed", "expanded"],
          toolbar: true,
          toolbarView: "index-graph-toolbar"
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
        id: "edit",
        label: "Edit",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document"],
        appKinds: ["manage"],
        features: ["management"],
        renderer: "manage-edit"
      },
      {
        id: "markdown-source",
        label: "Markdown source",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-toggle"
      },
      {
        id: "save-markdown-source",
        label: "Save Markdown source",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        appKinds: ["manage"],
        features: ["source-editing"],
        renderer: "markdown-source-save"
      }
    ]
  };
}
