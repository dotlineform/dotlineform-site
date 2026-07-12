export function applyDocsViewerManagementConfig(options) {
  var config = options.config || {};
  var context = options.context;
  var state = options.state;

  state.docNonViewableEmoji = String(context.getConfigValue(config, "docs_viewer.doc_non_viewable_emoji") || state.docNonViewableEmoji || "\uD83D\uDEAB");

  var metadataWorkflow = options.metadataWorkflow || null;
  if (metadataWorkflow && typeof metadataWorkflow.refreshEditingOptions === "function") {
    metadataWorkflow.refreshEditingOptions();
  }
}
