export function applyDocsViewerManagementConfig(options) {
  var config = options.config || {};
  var context = options.context;
  var state = options.state;

  state.docNonViewableEmoji = String(context.getConfigValue(config, "docs_viewer.doc_non_viewable_emoji") || state.docNonViewableEmoji || "\uD83D\uDEAB");

  var refs = options.refs || {};
  var modalController = options.modalController || null;
  if (state.metadataEditingDocId && refs.metadataStatusInput && modalController) {
    var metadataDoc = state.docsById.get(state.metadataEditingDocId);
    modalController.renderMetadataStatusOptions(metadataDoc);
    modalController.renderMetadataParentOptions(metadataDoc);
  }
}
