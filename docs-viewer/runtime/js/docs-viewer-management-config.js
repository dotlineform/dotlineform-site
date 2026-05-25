var MANAGEMENT_TEXT_KEYS = [
  ["archiveUnavailableNote", "docs_viewer.manage_archive_unavailable_note"],
  ["archiveUnavailableTitle", "docs_viewer.archive_unavailable_title"],
  ["archiveScopeMissingPrompt", "docs_viewer.archive_scope_missing_prompt"],
  ["checkingNote", "docs_viewer.manage_checking_note"],
  ["clearSearchNote", "docs_viewer.manage_clear_search_note"],
  ["serverNotConfiguredError", "docs_viewer.manage_server_not_configured_error"],
  ["unavailableNote", "docs_viewer.manage_unavailable_note"],
  ["cancelButton", "docs_viewer.modal_cancel_button"],
  ["confirmContinueButton", "docs_viewer.modal_continue_button"],
  ["viewableAncestorPrompt", "docs_viewer.viewable_ancestor_prompt"],
  ["viewableAncestorTitle", "docs_viewer.viewable_ancestor_title"],
  ["viewableDescendantPrompt", "docs_viewer.viewable_descendant_prompt"],
  ["viewableDescendantTitle", "docs_viewer.viewable_descendant_title"],
  ["viewableDescendantSelectedLabel", "docs_viewer.viewable_descendant_selected_label"],
  ["viewableDescendantAllLabel", "docs_viewer.viewable_descendant_all_label"],
  ["viewableInvalidChoice", "docs_viewer.viewable_invalid_choice"],
  ["createDocTitle", "docs_viewer.create_doc_title"],
  ["createChildDocTitle", "docs_viewer.create_child_doc_title"],
  ["createSiblingDocTitle", "docs_viewer.create_sibling_doc_title"],
  ["createDocLabel", "docs_viewer.create_doc_label"],
  ["createDocDefaultTitle", "docs_viewer.create_doc_default_title"],
  ["createDocButton", "docs_viewer.create_doc_button"],
  ["archiveConfirmTitle", "docs_viewer.archive_confirm_title"],
  ["archiveConfirmBody", "docs_viewer.archive_confirm_body"],
  ["archiveConfirmButton", "docs_viewer.archive_confirm_button"],
  ["deleteConfirmTitle", "docs_viewer.delete_confirm_title"],
  ["deleteConfirmButton", "docs_viewer.delete_confirm_button"],
  ["metadataStatusLabel", "docs_viewer.metadata_status_label"],
  ["metadataStatusNoneOption", "docs_viewer.metadata_status_none_option"],
  ["metadataStatusSelectedSuffix", "docs_viewer.metadata_status_selected_suffix"],
  ["metadataParentRootOption", "docs_viewer.metadata_parent_root_option"],
  ["metadataParentInvalid", "docs_viewer.metadata_parent_invalid"],
  ["metadataParentNoMatches", "docs_viewer.metadata_parent_no_matches"],
  ["statusMenuLabel", "docs_viewer.status_menu_label"],
  ["statusPillSetLabel", "docs_viewer.status_pill_set_label"],
  ["statusPillClearLabel", "docs_viewer.status_pill_clear_label"],
  ["statusPillReadonlyLabel", "docs_viewer.status_pill_readonly_label"],
  ["statusPillSaving", "docs_viewer.status_pill_saving"],
  ["statusPillSaved", "docs_viewer.status_pill_saved"],
  ["statusPillFailed", "docs_viewer.status_pill_failed"],
  ["settingsLoading", "docs_viewer.settings_loading"],
  ["settingsEmpty", "docs_viewer.settings_empty"],
  ["settingsSaving", "docs_viewer.settings_saving"],
  ["settingsSaved", "docs_viewer.settings_saved"],
  ["settingsLoadFailed", "docs_viewer.settings_load_failed"],
  ["settingsSaveFailed", "docs_viewer.settings_save_failed"],
  ["normalizeOrderTitle", "docs_viewer.normalize_order_title"],
  ["normalizeOrderPrompt", "docs_viewer.normalize_order_prompt"],
  ["normalizeOrderButton", "docs_viewer.normalize_order_button"],
  ["normalizeOrderRunning", "docs_viewer.normalize_order_running"],
  ["normalizeOrderDone", "docs_viewer.normalize_order_done"],
  ["normalizeOrderFailed", "docs_viewer.normalize_order_failed"],
  ["normalizeOrderRequired", "docs_viewer.normalize_order_required"],
  ["normalizeOrderRootLabel", "docs_viewer.normalize_order_root_label"],
  ["normalizeOrderRootChoiceLabel", "docs_viewer.normalize_order_root_choice_label"],
  ["normalizeOrderCurrentSiblingsLabel", "docs_viewer.normalize_order_current_siblings_label"],
  ["normalizeOrderSelectedChildrenLabel", "docs_viewer.normalize_order_selected_children_label"],
  ["normalizeOrderWholeScopeLabel", "docs_viewer.normalize_order_whole_scope_label"],
  ["scopeCreateTitle", "docs_viewer.scope_create_title"],
  ["scopeCreateIntro", "docs_viewer.scope_create_intro"],
  ["scopeIdLabel", "docs_viewer.scope_id_label"],
  ["scopeTitleLabel", "docs_viewer.scope_title_label"],
  ["scopePublishingModeLabel", "docs_viewer.scope_publishing_mode_label"],
  ["scopePublicReadonlyMode", "docs_viewer.scope_public_readonly_mode"],
  ["scopeLocalCommittedMode", "docs_viewer.scope_local_committed_mode"],
  ["scopeLocalUncommittedMode", "docs_viewer.scope_local_uncommitted_mode"],
  ["scopePublicReadonlyModeNote", "docs_viewer.scope_public_readonly_mode_note"],
  ["scopeLocalCommittedModeNote", "docs_viewer.scope_local_committed_mode_note"],
  ["scopeLocalUncommittedModeNote", "docs_viewer.scope_local_uncommitted_mode_note"],
  ["scopeSourceRootLabel", "docs_viewer.scope_source_root_label"],
  ["scopeDefaultDocIdLabel", "docs_viewer.scope_default_doc_id_label"],
  ["scopePublicRoutePathLabel", "docs_viewer.scope_public_route_path_label"],
  ["scopeWriteGeneratedLabel", "docs_viewer.scope_write_generated_label"],
  ["scopeBuildSearchLabel", "docs_viewer.scope_build_search_label"],
  ["scopePreviewButton", "docs_viewer.scope_preview_button"],
  ["scopeSaveButton", "docs_viewer.scope_save_button"],
  ["scopeDeleteButton", "docs_viewer.scope_delete_button"],
  ["scopeResultOkButton", "docs_viewer.scope_result_ok_button"],
  ["scopeCreateRequiredMessage", "docs_viewer.scope_create_required_message"],
  ["scopeCreateRouteRequiredMessage", "docs_viewer.scope_create_route_required_message"],
  ["scopeCreatePreviewing", "docs_viewer.scope_create_previewing"],
  ["scopeCreatePreviewTitle", "docs_viewer.scope_create_preview_title"],
  ["scopeCreateSaving", "docs_viewer.scope_create_saving"],
  ["scopeCreateFailed", "docs_viewer.scope_create_failed"],
  ["scopeCreateResultTitle", "docs_viewer.scope_create_result_title"],
  ["scopeDeleteTitle", "docs_viewer.scope_delete_title"],
  ["scopeDeleteIntro", "docs_viewer.scope_delete_intro"],
  ["scopeDeleteTargetLabel", "docs_viewer.scope_delete_target_label"],
  ["scopeDeleteRequiredMessage", "docs_viewer.scope_delete_required_message"],
  ["scopeDeleteNoTargets", "docs_viewer.scope_delete_no_targets"],
  ["scopeDeletePreviewing", "docs_viewer.scope_delete_previewing"],
  ["scopeDeletePreviewTitle", "docs_viewer.scope_delete_preview_title"],
  ["scopeDeleteDeleting", "docs_viewer.scope_delete_deleting"],
  ["scopeDeleteFailed", "docs_viewer.scope_delete_failed"],
  ["scopeDeleteBlocked", "docs_viewer.scope_delete_blocked"],
  ["scopeDeleteBlockedTitle", "docs_viewer.scope_delete_blocked_title"],
  ["scopeDeleteResultTitle", "docs_viewer.scope_delete_result_title"],
  ["importCancelButton", "docs_viewer.import_cancel_button"],
  ["copyLinkStatus", "docs_viewer.copy_link_status"],
  ["copyLinkFailed", "docs_viewer.copy_link_failed"]
];

function applyManagementText(config, state, context) {
  MANAGEMENT_TEXT_KEYS.forEach(function (entry) {
    state.managementText[entry[0]] = context.getConfigText(config, entry[1], state.managementText[entry[0]]);
  });
  state.managementText.metadataHiddenLabel = context.getConfigText(
    config,
    "docs_viewer.metadata_hidden_label",
    context.getConfigText(config, "docs_viewer.metadata_viewable_label", state.managementText.metadataHiddenLabel)
  );
  state.managementText.docHiddenEmoji = String(context.getConfigValue(config, "docs_viewer.doc_hidden_emoji") || state.managementText.docHiddenEmoji);
}

function setButtonLabel(button, label) {
  if (!button) return;
  button.textContent = label;
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
    refs.draftLabel.textContent = context.getConfigText(
      config,
      "docs_viewer.hidden_toggle_label",
      context.getConfigText(config, "docs_viewer.draft_toggle_label", "show hidden")
    );
  }
  if (refs.draftToggle) {
    refs.draftToggle.setAttribute(
      "aria-label",
      context.getConfigText(
        config,
        "docs_viewer.hidden_toggle_aria_label",
        context.getConfigText(config, "docs_viewer.draft_toggle_aria_label", "Show hidden docs")
      )
    );
  }
  if (refs.manageViewableButton) {
    setButtonLabel(refs.manageViewableButton, context.getConfigText(config, "docs_viewer.make_viewable_button", "Show"));
  }
  if (refs.manageSettingsButton) {
    refs.manageSettingsButton.textContent = context.getConfigText(config, "docs_viewer.settings_button", "Settings");
  }
  if (refs.manageNormalizeOrderButton) {
    refs.manageNormalizeOrderButton.textContent = context.getConfigText(config, "docs_viewer.normalize_order_menu_button", "Normalize order");
  }

  state.managementText.scopeNewButton = context.getConfigText(config, "docs_viewer.scope_new_button", state.managementText.scopeNewButton);
  if (refs.manageNewScopeButton) {
    refs.manageNewScopeButton.textContent = state.managementText.scopeNewButton;
  }
  state.managementText.scopeDeleteMenuButton = context.getConfigText(config, "docs_viewer.scope_delete_menu_button", state.managementText.scopeDeleteMenuButton);
  if (refs.manageDeleteScopeButton) {
    refs.manageDeleteScopeButton.textContent = state.managementText.scopeDeleteMenuButton;
  }
  state.managementText.copyLinkLabel = context.getConfigText(config, "docs_viewer.copy_link_label", state.managementText.copyLinkLabel);
  if (refs.contextCopyLinkButton) {
    refs.contextCopyLinkButton.textContent = state.managementText.copyLinkLabel;
    refs.contextCopyLinkButton.setAttribute("aria-label", state.managementText.copyLinkLabel);
  }

  if (refs.settingsHeading) {
    refs.settingsHeading.textContent = context.getConfigText(config, "docs_viewer.settings_title", "Settings");
  }
  if (refs.settingsUpdatedLabel) {
    refs.settingsUpdatedLabel.textContent = context.getConfigText(config, "docs_viewer.settings_show_updated_date_label", "show updated dates");
  }

  applyManagementText(config, state, context);

  if (modalController) modalController.updateImportCancelLabel();
  if (refs.metadataStatusLabel) {
    refs.metadataStatusLabel.textContent = state.managementText.metadataStatusLabel;
  }
  if (refs.metadataHiddenLabel) {
    refs.metadataHiddenLabel.textContent = state.managementText.metadataHiddenLabel;
  }
  if (state.metadataEditingDocId && refs.metadataStatusInput && modalController) {
    var metadataDoc = state.docsById.get(state.metadataEditingDocId);
    modalController.renderMetadataStatusOptions(metadataDoc);
    modalController.renderMetadataParentOptions(metadataDoc);
  }
}
