export function applyDocsViewerManagementConfig(options) {
  var config = options.config || {};
  var context = options.context;
  var scopeConfig = options.scopeConfig || {};

  scopeConfig.docNonPublishableEmoji = String(context.getConfigValue(config, "docs_viewer.doc_non_publishable_emoji") || scopeConfig.docNonPublishableEmoji || "\uD83D\uDEAB");

  var metadataWorkflow = options.metadataWorkflow || null;
  if (metadataWorkflow && typeof metadataWorkflow.refreshEditingOptions === "function") {
    metadataWorkflow.refreshEditingOptions();
  }
}
