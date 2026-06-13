export function createDocsViewerManagementHostedViews() {
  return [
    {
      id: "markdown-source",
      label: "Markdown source",
      panel: "main",
      access: "manage",
      availability: "available",
      module: "repo:markdown-source",
      load: function () {
        return import("./source-editor/source-editor.js")
          .then(function (module) {
            return module.createDocsViewerSourceEditorView();
          });
      }
    }
  ];
}
