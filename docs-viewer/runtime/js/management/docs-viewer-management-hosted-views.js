export function createDocsViewerManagementHostedViews() {
  return [
    {
      id: "semantic-token-picker",
      label: "Semantic ref",
      panel: "info",
      access: "manage",
      availability: "available",
      module: "repo:semantic-token-picker",
      load: function () {
        return import("./source-editor/semantic-token-picker-view.js")
          .then(function (module) {
            return module.createSemanticTokenPickerView();
          });
      }
    }
  ];
}

export function createDocsViewerManagementDocumentDisplayModes() {
  return [
    {
      id: "markdown-source",
      label: "Markdown source",
      access: "manage",
      availability: "available",
      module: "repo:markdown-source",
      load: function () {
        return import("./source-editor/source-editor.js")
          .then(function (module) {
            return module.createDocsViewerSourceEditorMode();
          });
      }
    }
  ];
}
