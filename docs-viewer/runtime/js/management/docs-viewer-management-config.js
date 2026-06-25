function setButtonLabel(button, label) {
  if (!button) return;
  button.textContent = label;
  button.setAttribute("aria-label", label);
  button.title = label;
}

function setActionMenuButtonLabel(button, label) {
  if (!button) return;
  var labelNode = button.querySelector(".docsViewer__actionMenuLabel");
  if (labelNode) {
    labelNode.textContent = label;
  } else {
    button.textContent = label;
  }
  button.setAttribute("aria-label", label);
  button.title = label;
}

export function applyDocsViewerManagementConfig(options) {
  var config = options.config || {};
  var context = options.context;
  var state = options.state;
  var refs = options.refs || {};
  var modalController = options.modalController || null;

  if (refs.draftLabel) {
    refs.draftLabel.textContent = "Show non-viewable";
  }
  if (refs.draftToggle) {
    refs.draftToggle.setAttribute("aria-label", "Show non-viewable docs");
  }
  if (refs.manageViewableButton) {
    setButtonLabel(refs.manageViewableButton, "Show");
  }
  if (refs.manageSettingsButton) {
    setActionMenuButtonLabel(refs.manageSettingsButton, "Settings");
  }
  if (refs.manageNewScopeButton) {
    setActionMenuButtonLabel(refs.manageNewScopeButton, state.managementText.scopeNewButton);
  }
  if (refs.manageDeleteScopeButton) {
    setActionMenuButtonLabel(refs.manageDeleteScopeButton, state.managementText.scopeDeleteMenuButton);
  }
  if (refs.manageNewSubScopeButton) {
    setActionMenuButtonLabel(refs.manageNewSubScopeButton, state.managementText.subScopeNewButton);
  }
  if (refs.manageDeleteSubScopeButton) {
    setActionMenuButtonLabel(refs.manageDeleteSubScopeButton, state.managementText.subScopeDeleteMenuButton);
  }
  if (refs.managePublishButton) {
    setActionMenuButtonLabel(refs.managePublishButton, state.managementText.publishConfirmButton);
  }
  if (refs.contextCopyLinkButton) {
    refs.contextCopyLinkButton.textContent = state.managementText.copyLinkLabel;
    refs.contextCopyLinkButton.setAttribute("aria-label", state.managementText.copyLinkLabel);
  }

  if (refs.settingsHeading) {
    refs.settingsHeading.textContent = "Settings";
  }

  state.managementText.docNonViewableEmoji = String(context.getConfigValue(config, "docs_viewer.doc_non_viewable_emoji") || state.managementText.docNonViewableEmoji);

  if (modalController) modalController.updateImportCancelLabel();
  if (refs.metadataStatusLabel) {
    refs.metadataStatusLabel.textContent = state.managementText.metadataStatusLabel;
  }
  if (refs.metadataNonViewableLabel) {
    refs.metadataNonViewableLabel.textContent = state.managementText.metadataNonViewableLabel;
  }
  if (state.metadataEditingDocId && refs.metadataStatusInput && modalController) {
    var metadataDoc = state.docsById.get(state.metadataEditingDocId);
    modalController.renderMetadataStatusOptions(metadataDoc);
    modalController.renderMetadataParentOptions(metadataDoc);
  }
}
