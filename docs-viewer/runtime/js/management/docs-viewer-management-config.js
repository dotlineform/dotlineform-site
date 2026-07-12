export function applyDocsViewerManagementConfig(options) {
  var config = options.config || {};
  var context = options.context;
  var scopeConfig = options.scopeConfig || {};

  scopeConfig.docNonViewableEmoji = String(context.getConfigValue(config, "docs_viewer.doc_non_viewable_emoji") || scopeConfig.docNonViewableEmoji || "\uD83D\uDEAB");

  var metadataWorkflow = options.metadataWorkflow || null;
  if (metadataWorkflow && typeof metadataWorkflow.refreshEditingOptions === "function") {
    metadataWorkflow.refreshEditingOptions();
  }
}
