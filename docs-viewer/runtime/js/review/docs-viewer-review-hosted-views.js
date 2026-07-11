export function createDocsViewerReviewViewDefinitions() {
  return {
    modes: [{
      id: "markdown-source",
      features: ["source-editing"],
      label: "Markdown source",
      ownerViewId: "rendered-document",
      appKinds: ["review"],
      load: function () {
        return import("../management/source-editor/source-editor.js")
          .then(function (module) { return module.createDocsViewerSourceEditorMode(); });
      }
    }],
    controls: [
      {
        id: "markdown-source",
        label: "Markdown source",
        ownerViewId: "rendered-document",
        modeIds: ["rendered-document", "markdown-source"],
        appKinds: ["review"],
        features: ["source-editing"],
        renderer: "markdown-source-toggle"
      },
      {
        id: "save-markdown-source",
        label: "Save Markdown source",
        ownerViewId: "rendered-document",
        modeIds: ["markdown-source"],
        appKinds: ["review"],
        features: ["source-editing"],
        renderer: "markdown-source-save"
      }
    ]
  };
}
