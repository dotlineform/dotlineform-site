export function createDocsViewerManagementHostedViews() {
  return [];
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
