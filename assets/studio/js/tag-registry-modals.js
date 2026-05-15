import { getStudioText } from "./studio-config.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import { tagRegistryUi } from "./studio-ui.js";

const UI = tagRegistryUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

export function renderTagRegistryModals(state) {
  return [
    renderImportModal(state),
    renderPatchModal(state),
    renderEditModal(state),
    renderNewModal(state),
    renderDemoteModal(state),
    renderDeleteModal(state)
  ].join("");
}

export function collectTagRegistryModalRefs(root) {
  return {
    importModal: root.querySelector(UI_SELECTOR.importModal),
    importFileLabel: root.querySelector(UI_SELECTOR.importFileLabel),
    chooseFile: root.querySelector(UI_SELECTOR.chooseFile),
    importFile: root.querySelector(UI_SELECTOR.importFile),
    importModeLabel: root.querySelector(UI_SELECTOR.importModeLabel),
    importMode: root.querySelector(UI_SELECTOR.importMode),
    importButton: root.querySelector(UI_SELECTOR.importButton),
    selectedFile: root.querySelector(UI_SELECTOR.selectedFile),
    importResult: root.querySelector(UI_SELECTOR.importResult),
    patchModal: root.querySelector(UI_SELECTOR.patchModal),
    patchSnippet: root.querySelector(UI_SELECTOR.patchSnippet),
    copyPatch: root.querySelector(UI_SELECTOR.copyPatch),
    editModal: root.querySelector(UI_SELECTOR.editModal),
    editTagId: root.querySelector(UI_SELECTOR.editTagId),
    editTagName: root.querySelector(UI_SELECTOR.editTagName),
    editDescription: root.querySelector(UI_SELECTOR.editDescription),
    editStatus: root.querySelector(UI_SELECTOR.editStatus),
    saveEdit: root.querySelector(UI_SELECTOR.saveEdit),
    newModal: root.querySelector(UI_SELECTOR.newModal),
    newGroupKey: root.querySelector(UI_SELECTOR.newGroupKey),
    newTagSlug: root.querySelector(UI_SELECTOR.newTagSlug),
    newTagWarning: root.querySelector(UI_SELECTOR.newTagWarning),
    newTagDescription: root.querySelector(UI_SELECTOR.newTagDescription),
    newTagStatus: root.querySelector(UI_SELECTOR.newTagStatus),
    createTag: root.querySelector(UI_SELECTOR.createTag),
    demoteModal: root.querySelector(UI_SELECTOR.demoteModal),
    demoteTagMeta: root.querySelector(UI_SELECTOR.demoteTagMeta),
    demoteTagSearch: root.querySelector(UI_SELECTOR.demoteTagSearch),
    demoteTagPopupWrap: root.querySelector(UI_SELECTOR.demoteTagPopupWrap),
    demoteTagPopup: root.querySelector(UI_SELECTOR.demoteTagPopup),
    demoteGroupKey: root.querySelector(UI_SELECTOR.demoteGroupKey),
    demoteTagList: root.querySelector(UI_SELECTOR.demoteTagList),
    demoteStatus: root.querySelector(UI_SELECTOR.demoteStatus),
    confirmDemote: root.querySelector(UI_SELECTOR.confirmDemote),
    deleteModal: root.querySelector(UI_SELECTOR.deleteModal),
    deleteTagMeta: root.querySelector(UI_SELECTOR.deleteTagMeta),
    deleteImpact: root.querySelector(UI_SELECTOR.deleteImpact),
    deleteStatus: root.querySelector(UI_SELECTOR.deleteStatus),
    confirmDeleteTag: root.querySelector(UI_SELECTOR.confirmDeleteTag)
  };
}

export function wireTagRegistryModalEvents(state, callbacks = {}) {
  state.refs.openImportModal.addEventListener("click", () => {
    if (!state.importAvailable) return;
    clearTagRegistryImportResult(state);
    showTagRegistryImportModal(state);
    callbacks.onModalStateChange?.();
  });

  state.refs.chooseFile.addEventListener("click", () => {
    state.refs.importFile.click();
  });

  state.refs.importFile.addEventListener("change", () => {
    const files = state.refs.importFile.files;
    setTagRegistrySelectedImportFile(state, files && files.length ? files[0] : null);
  });

  state.refs.importMode.addEventListener("change", () => {
    callbacks.onImportModeChange?.();
  });

  state.refs.importButton.addEventListener("click", () => {
    callbacks.onImportSubmit?.();
  });

  state.refs.importModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.importModalClose)) return;
    hideTagRegistryImportModal(state);
    callbacks.onModalStateChange?.();
  });

  state.refs.patchModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.patchModalClose)) return;
    hideTagRegistryPatchModal(state);
  });

  state.refs.copyPatch.addEventListener("click", () => {
    callbacks.onPatchCopy?.();
  });

  state.refs.editModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.editModalClose)) return;
    closeTagRegistryEditModal(state);
    callbacks.onModalStateChange?.();
  });

  state.refs.saveEdit.addEventListener("click", () => {
    callbacks.onEditSave?.();
  });

  state.refs.editDescription.addEventListener("input", () => {
    callbacks.onEditDescriptionInput?.();
  });

  state.refs.newModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.newModalClose)) {
      closeTagRegistryNewModal(state);
      callbacks.onModalStateChange?.();
      return;
    }
    const groupButton = event.target.closest("button[data-new-group]");
    if (!groupButton || !state.newTagState) return;
    const group = normalizeModalValue(groupButton.getAttribute("data-new-group"));
    if (!getStudioGroups(state).includes(group)) return;
    state.newTagState.group = group;
    callbacks.onNewTagInput?.();
  });

  state.refs.newTagSlug.addEventListener("input", () => {
    callbacks.onNewTagInput?.();
  });

  state.refs.newTagDescription.addEventListener("input", () => {
    callbacks.onNewTagInput?.();
  });

  state.refs.createTag.addEventListener("click", () => {
    callbacks.onCreateTag?.();
  });

  state.refs.demoteModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.demoteModalClose)) {
      closeTagRegistryDemoteModal(state);
      callbacks.onModalStateChange?.();
      return;
    }
    if (state.refs.demoteTagPopupWrap.hidden) return;
    if (!event.target.closest(UI_SELECTOR.demoteTagPopupWrap) && !event.target.closest(UI_SELECTOR.demoteTagSearch)) {
      hideTagRegistryDemoteTagPopup(state);
    }
  });

  state.refs.demoteTagSearch.addEventListener("input", () => {
    callbacks.onDemoteSearch?.();
  });

  state.refs.demoteTagSearch.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideTagRegistryDemoteTagPopup(state);
      state.refs.demoteTagSearch.blur();
    }
  });

  state.refs.demoteTagPopup.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-popup-demote-tag-id]");
    if (!button) return;
    const tagId = button.getAttribute("data-popup-demote-tag-id");
    if (!tagId) return;
    callbacks.onDemoteTagSelect?.(tagId);
    state.refs.demoteTagSearch.value = "";
    hideTagRegistryDemoteTagPopup(state);
  });

  state.refs.demoteTagList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-remove-demote-tag]");
    if (!button || !state.demoteState) return;
    const tagId = button.getAttribute("data-remove-demote-tag");
    if (!tagId) return;
    callbacks.onDemoteTagRemove?.(tagId);
  });

  state.refs.confirmDemote.addEventListener("click", () => {
    callbacks.onDemoteSubmit?.();
  });

  state.refs.deleteModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.deleteModalClose)) return;
    closeTagRegistryDeleteModal(state);
    callbacks.onModalStateChange?.();
  });

  state.refs.confirmDeleteTag.addEventListener("click", () => {
    callbacks.onDeleteConfirm?.();
  });

  document.addEventListener("keydown", (event) => {
    const modalKind = getOpenTagRegistryModalKind(state);
    if (!modalKind) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeTagRegistryModalByKind(state, modalKind);
      callbacks.onModalStateChange?.();
      return;
    }

    if (event.key !== "Tab") return;
    trapModalFocus(event, getTagRegistryModalElement(state, modalKind));
  });
}

export function showTagRegistryImportModal(state) {
  captureModalRestoreFocus(state, "import");
  state.importModalOpen = true;
  state.importModalFocusReady = false;
  state.refs.importModal.hidden = false;
  syncModalFocusAfterOpen(state, "import");
}

export function hideTagRegistryImportModal(state) {
  const restoreTarget = state.importModalRestoreFocus;
  state.importModalOpen = false;
  state.importModalFocusReady = false;
  state.importModalRestoreFocus = null;
  state.refs.importModal.hidden = true;
  restoreModalFocus(restoreTarget);
}

export function setTagRegistrySelectedImportFile(state, file) {
  state.selectedFile = file || null;
  if (state.selectedFile) {
    state.refs.selectedFile.textContent = registryText(
      state.config,
      "selected_file_template",
      "Selected: {filename}",
      { filename: state.selectedFile.name }
    );
    clearTagRegistryImportResult(state);
    return;
  }
  state.refs.selectedFile.textContent = "";
}

export function setTagRegistryImportResult(state, kind, message) {
  setStatusText(state.refs.importResult, kind, message, UI_CLASS.toolbarResult);
}

export function clearTagRegistryImportResult(state) {
  setTagRegistryImportResult(state, "", "");
}

export function showTagRegistryPatchModal(state, snippet) {
  captureModalRestoreFocus(state, "patch");
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
  state.patchModalFocusReady = false;
  syncModalFocusAfterOpen(state, "patch");
}

export function hideTagRegistryPatchModal(state) {
  const restoreTarget = state.patchModalRestoreFocus;
  state.refs.patchModal.hidden = true;
  state.patchModalFocusReady = false;
  state.patchModalRestoreFocus = null;
  restoreModalFocus(restoreTarget);
}

export function openTagRegistryEditModal(state, tag) {
  captureModalRestoreFocus(state, "edit");
  const [, slug = ""] = String(tag.tagId || "").split(":", 2);
  state.editTagId = tag.tagId;
  state.refs.editTagId.innerHTML = `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(tag.group))}" title="${escapeHtml(String(state.groupDescriptions.get(tag.group) || tag.tagId))}">
      ${escapeHtml(tag.group)}
    </span>
  `;
  state.refs.editTagName.value = slug;
  state.refs.editDescription.value = String(tag.description || "");
  setStatusText(
    state.refs.editStatus,
    "",
    state.saveMode === "post"
      ? ""
      : registryText(state.config, "local_edit_required", "Local server is required for edit.")
  );
  state.refs.editModal.hidden = false;
  state.editModalFocusReady = false;
  syncModalFocusAfterOpen(state, "edit");
}

export function closeTagRegistryEditModal(state) {
  const restoreTarget = state.editModalRestoreFocus;
  state.refs.editModal.hidden = true;
  state.editModalFocusReady = false;
  state.editModalRestoreFocus = null;
  state.editTagId = "";
  state.refs.editTagName.value = "";
  state.refs.editDescription.value = "";
  restoreModalFocus(restoreTarget);
}

export function openTagRegistryNewModal(state) {
  captureModalRestoreFocus(state, "new");
  state.newTagState = {
    group: "",
    slug: "",
    description: ""
  };
  state.refs.newTagSlug.value = "";
  state.refs.newTagDescription.value = "";
  state.refs.newTagWarning.textContent = "";
  setStatusText(state.refs.newTagStatus, "", "");
  renderTagRegistryNewTagGroupKey(state);
  state.refs.createTag.disabled = true;
  state.refs.newModal.hidden = false;
  state.newModalFocusReady = false;
  syncModalFocusAfterOpen(state, "new");
}

export function closeTagRegistryNewModal(state) {
  const restoreTarget = state.newModalRestoreFocus;
  state.newTagState = null;
  state.refs.newModal.hidden = true;
  state.newModalFocusReady = false;
  state.newModalRestoreFocus = null;
  state.refs.newTagSlug.value = "";
  state.refs.newTagDescription.value = "";
  state.refs.newTagWarning.textContent = "";
  setStatusText(state.refs.newTagStatus, "", "");
  state.refs.newGroupKey.innerHTML = "";
  state.refs.createTag.disabled = true;
  restoreModalFocus(restoreTarget);
}

export function renderTagRegistryNewTagModalState(state, validation) {
  renderTagRegistryNewTagGroupKey(state);
  state.refs.newTagWarning.textContent = validation && validation.warning ? validation.warning : "";
  state.refs.createTag.disabled = !(validation && validation.valid);
  if (!(validation && validation.warning)) {
    setStatusText(state.refs.newTagStatus, "", "");
  }
}

export function openTagRegistryDemoteModal(state, options) {
  captureModalRestoreFocus(state, "demote");
  const tag = options && options.tag;
  const aliasKey = options && options.aliasKey ? options.aliasKey : tag.tagId;
  state.demoteState = {
    tagId: tag.tagId,
    tags: []
  };
  state.refs.demoteTagMeta.textContent = `tag: ${tag.tagId} -> alias "${aliasKey}"`;
  state.refs.demoteTagSearch.value = "";
  hideTagRegistryDemoteTagPopup(state);
  renderTagRegistryDemoteSelectionState(state, {
    selectedItems: [],
    canConfirm: false,
    statusKind: "",
    statusMessage: ""
  });
  state.refs.demoteModal.hidden = false;
  state.demoteModalFocusReady = false;
  syncModalFocusAfterOpen(state, "demote");
}

export function closeTagRegistryDemoteModal(state) {
  const restoreTarget = state.demoteModalRestoreFocus;
  state.demoteState = null;
  state.refs.demoteModal.hidden = true;
  state.demoteModalFocusReady = false;
  state.demoteModalRestoreFocus = null;
  state.refs.demoteTagMeta.textContent = "";
  state.refs.demoteTagSearch.value = "";
  state.refs.demoteTagList.innerHTML = "";
  state.refs.demoteGroupKey.innerHTML = "";
  state.refs.confirmDemote.disabled = true;
  setStatusText(state.refs.demoteStatus, "", "");
  hideTagRegistryDemoteTagPopup(state);
  restoreModalFocus(restoreTarget);
}

export function renderTagRegistryDemoteSelectionState(state, options = {}) {
  const selectedItems = Array.isArray(options.selectedItems) ? options.selectedItems : [];
  renderTagRegistryDemoteGroupKey(state, selectedItems);
  renderTagRegistryDemoteTagList(state, selectedItems);
  state.refs.confirmDemote.disabled = !options.canConfirm;
  setStatusText(state.refs.demoteStatus, options.statusKind || "", options.statusMessage || "");
}

export function showTagRegistryDemoteTagPopup(state, html) {
  state.refs.demoteTagPopup.innerHTML = html || "";
  state.refs.demoteTagPopupWrap.hidden = false;
}

export function renderTagRegistryDemoteTagPopup(state, result) {
  const matches = result && Array.isArray(result.matches) ? result.matches : [];
  if (!matches.length) {
    hideTagRegistryDemoteTagPopup(state);
    return;
  }
  showTagRegistryDemoteTagPopup(
    state,
    renderPopupTagOptions(state, matches, {
      attribute: "data-popup-demote-tag-id",
      truncated: Boolean(result && result.truncated)
    })
  );
}

export function hideTagRegistryDemoteTagPopup(state) {
  state.refs.demoteTagPopupWrap.hidden = true;
  state.refs.demoteTagPopup.innerHTML = "";
}

export function openTagRegistryDeleteModal(state, tag) {
  captureModalRestoreFocus(state, "delete");
  state.deleteTagId = tag.tagId;
  state.deletePreview = "";
  state.deletePreviewSeq += 1;
  state.refs.deleteTagMeta.innerHTML = renderDeleteTagMeta(state, tag);
  setStatusText(state.refs.deleteImpact, "", "", UI_CLASS.formImpact);
  setStatusText(state.refs.deleteStatus, "", "");
  state.refs.confirmDeleteTag.disabled = state.saveMode !== "post";
  state.refs.deleteModal.hidden = false;
  state.deleteModalFocusReady = false;
  syncModalFocusAfterOpen(state, "delete");
}

export function closeTagRegistryDeleteModal(state) {
  const restoreTarget = state.deleteModalRestoreFocus;
  state.refs.deleteModal.hidden = true;
  state.deleteModalFocusReady = false;
  state.deleteModalRestoreFocus = null;
  state.deleteTagId = "";
  state.deletePreview = "";
  state.deletePreviewSeq += 1;
  state.refs.deleteTagMeta.innerHTML = "";
  setStatusText(state.refs.deleteImpact, "", "", UI_CLASS.formImpact);
  setStatusText(state.refs.deleteStatus, "", "");
  state.refs.confirmDeleteTag.disabled = false;
  restoreModalFocus(restoreTarget);
}

export function setTagRegistryDeleteImpactStatus(state, kind, message) {
  setStatusText(state.refs.deleteImpact, kind, message, UI_CLASS.formImpact);
}

export function renderTagRegistryDeleteImpactPreview(state, options = {}) {
  const stats = options.response && typeof options.response === "object" ? options.response : {};
  const affectedSeries = Array.isArray(options.affectedSeries) ? options.affectedSeries : [];
  const aliasesUpdated = Math.max(
    0,
    Number(stats.aliases_rewritten || 0) - Number(stats.aliases_removed_empty || 0) - Number(stats.aliases_removed_redundant || 0)
  );
  const aliasesDeleted = Number(stats.aliases_removed_empty || 0) + Number(stats.aliases_removed_redundant || 0);
  const items = [
    renderDeleteImpactSeriesItem(state, affectedSeries),
    renderDeleteImpactCountItem(
      registryText(state.config, "delete_impact_aliases_updated", "aliases updated"),
      aliasesUpdated
    ),
    renderDeleteImpactCountItem(
      registryText(state.config, "delete_impact_aliases_deleted", "aliases deleted"),
      aliasesDeleted
    )
  ];
  state.refs.deleteImpact.className = `${UI_CLASS.formImpact} tagRegistryDelete__impactPanel`;
  delete state.refs.deleteImpact.dataset.state;
  state.refs.deleteImpact.innerHTML = `
    <ul class="${UI_CLASS.deleteImpactList}">
      ${items.join("")}
    </ul>
  `;
}

function renderPatchModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.patchModal,
    backdropRole: UI.role.patchModalClose,
    titleId: "tagRegistryPatchTitle",
    title: registryText(state.config, "patch_modal_title", "Registry Patch Preview"),
    size: "wide",
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(registryText(state.config, "patch_modal_label", "Manual patch snippet"))}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.patchSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.patchModalClose, label: registryText(state.config, "patch_modal_close_button", "Close") },
      { role: UI.role.copyPatch, label: registryText(state.config, "patch_modal_copy_button", "Copy"), primary: true }
    ])
  });
}

function renderImportModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.importModalClose,
    titleId: "tagRegistryImportTitle",
    title: registryText(state.config, "import_modal_title", "Import Registry"),
    size: "wide",
    hidden: !state.importModalOpen,
    bodyHtml: `
      <div class="tagStudioToolbar tagStudioToolbar--modalImport">
        <div class="tagStudioToolbar__row">
          <button type="button" class="tagStudio__button" data-role="${UI.role.chooseFile}">${escapeHtml(registryText(state.config, "choose_file_button", "Choose file"))}</button>
          <input type="file" data-role="${UI.role.importFile}" accept=".json,application/json" hidden>
          <select class="tagStudioToolbar__select" data-role="${UI.role.importMode}">
            <option value="add">${escapeHtml(registryText(state.config, "import_mode_option_add", "add (no overwrite)"))}</option>
            <option value="merge">${escapeHtml(registryText(state.config, "import_mode_option_merge", "add + overwrite"))}</option>
            <option value="replace">${escapeHtml(registryText(state.config, "import_mode_option_replace", "replace entire registry"))}</option>
          </select>
          <button type="button" class="tagStudio__button" data-role="${UI.role.importButton}">${escapeHtml(registryText(state.config, "import_button", "Import"))}</button>
        </div>
        <p class="tagStudioToolbar__selected" data-role="${UI.role.selectedFile}"></p>
        <p class="tagStudioToolbar__result" data-role="${UI.role.importResult}"></p>
      </div>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.importModalClose, label: registryText(state.config, "import_modal_close_button", "Close") }
    ])
  });
}

function renderEditModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.editModal,
    backdropRole: UI.role.editModalClose,
    titleId: "tagRegistryEditTitle",
    title: registryText(state.config, "edit_modal_title", "Edit Tag"),
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.editTagId}"></p>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <input type="text" class="tagStudio__input ${UI_CLASS.formReadonly}" data-role="${UI.role.editTagName}" autocomplete="off" readonly>
        </label>
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "edit_description_label", "description"))}</span>
          <textarea class="tagStudio__input ${UI_CLASS.formDescriptionInput}" data-role="${UI.role.editDescription}" rows="3" autocomplete="off"></textarea>
        </label>
      </div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.editStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.editModalClose, label: registryText(state.config, "edit_close_button", "Close") },
      { role: UI.role.saveEdit, label: registryText(state.config, "edit_save_button", "Save"), primary: true }
    ])
  });
}

function renderNewModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.newModal,
    backdropRole: UI.role.newModalClose,
    titleId: "tagRegistryNewTitle",
    title: registryText(state.config, "new_modal_title", "New Tag"),
    bodyHtml: `
      <div class="tagStudio__key ${UI_CLASS.newGroupKey}" data-role="${UI.role.newGroupKey}"></div>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "new_slug_label", "slug"))}</span>
          <input type="text" class="tagStudio__input" data-role="${UI.role.newTagSlug}" autocomplete="off">
        </label>
        <p class="${UI_CLASS.formWarning}" data-role="${UI.role.newTagWarning}"></p>
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "new_description_label", "description"))}</span>
          <textarea class="tagStudio__input ${UI_CLASS.formDescriptionInput}" data-role="${UI.role.newTagDescription}" rows="3" autocomplete="off"></textarea>
        </label>
      </div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.newTagStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.newModalClose, label: registryText(state.config, "new_cancel_button", "Cancel") },
      { role: UI.role.createTag, label: registryText(state.config, "new_create_button", "Create"), primary: true, disabled: true }
    ])
  });
}

function renderDemoteModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.demoteModal,
    backdropRole: UI.role.demoteModalClose,
    titleId: "tagRegistryDemoteTitle",
    title: registryText(state.config, "demote_modal_title", "Demote Tag to Alias"),
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.demoteTagMeta}"></p>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField} ${UI_CLASS.formSearchWrap}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "demote_search_label", "find target tags"))}</span>
          <input type="text" class="tagStudio__input" data-role="${UI.role.demoteTagSearch}" autocomplete="off" placeholder="${escapeHtml(registryText(state.config, "demote_search_placeholder", "search tags"))}">
          <div class="${UI_CLASS.popup}" data-role="${UI.role.demoteTagPopupWrap}" hidden>
            <div class="${UI_CLASS.popupInner}" data-role="${UI.role.demoteTagPopup}"></div>
          </div>
        </label>
      </div>
      <div class="tagStudio__key ${UI_CLASS.formKey}" data-role="${UI.role.demoteGroupKey}"></div>
      <div class="tagStudio__chipList ${UI_CLASS.formSelected}" data-role="${UI.role.demoteTagList}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.demoteStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.demoteModalClose, label: registryText(state.config, "demote_close_button", "Close") },
      { role: UI.role.confirmDemote, label: registryText(state.config, "demote_confirm_button", "Demote"), primary: true, disabled: true }
    ])
  });
}

function renderDeleteModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.deleteModal,
    backdropRole: UI.role.deleteModalClose,
    titleId: "tagRegistryDeleteTitle",
    title: registryText(state.config, "delete_modal_title", "Delete Tag"),
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.deleteTagMeta}"></p>
      <p class="${UI_CLASS.formImpact} tagRegistryDelete__intro">
        ${escapeHtml(registryText(
          state.config,
          "delete_impact_intro",
          "Deleting this tag also removes matching tag assignments and removes this tag from aliases. Aliases left with no targets are deleted."
        ))}
      </p>
      <div class="${UI_CLASS.formImpact} tagRegistryDelete__impactPanel" data-role="${UI.role.deleteImpact}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.deleteStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.deleteModalClose, label: registryText(state.config, "delete_close_button", "Cancel") },
      { role: UI.role.confirmDeleteTag, label: registryText(state.config, "delete_confirm_button", "Delete"), primary: true }
    ])
  });
}

function closeTagRegistryModalByKind(state, modalKind) {
  if (modalKind === "import") {
    hideTagRegistryImportModal(state);
    return;
  }
  if (modalKind === "patch") {
    hideTagRegistryPatchModal(state);
    return;
  }
  if (modalKind === "edit") {
    closeTagRegistryEditModal(state);
    return;
  }
  if (modalKind === "new") {
    closeTagRegistryNewModal(state);
    return;
  }
  if (modalKind === "demote") {
    closeTagRegistryDemoteModal(state);
    return;
  }
  if (modalKind === "delete") {
    closeTagRegistryDeleteModal(state);
  }
}

function getOpenTagRegistryModalKind(state) {
  return modalConfigs().find((config) => {
    const modal = state.refs[config.modalRef];
    return Boolean(modal && !modal.hidden);
  })?.kind || "";
}

function getTagRegistryModalElement(state, modalKind) {
  const config = modalConfig(modalKind);
  return config && state.refs[config.modalRef] ? state.refs[config.modalRef] : null;
}

function captureModalRestoreFocus(state, modalKind) {
  const config = modalConfig(modalKind);
  if (!config) return;
  state[config.restoreProp] = document.activeElement;
}

function syncModalFocusAfterOpen(state, modalKind) {
  const config = modalConfig(modalKind);
  const modal = getTagRegistryModalElement(state, modalKind);
  if (!config || !modal || modal.hidden) return;
  if (state[config.focusProp] && modal.contains(document.activeElement)) return;
  const target = modal.querySelector(config.focusSelector)
    || modal.querySelector(`[data-role="${config.closeRole}"]`)
    || modal.querySelector("[role='dialog']");
  if (target && typeof target.focus === "function") target.focus();
  state[config.focusProp] = true;
}

function trapModalFocus(event, modal) {
  if (!modal) return;
  const nodes = focusableNodes(modal);
  if (!nodes.length) return;
  const first = nodes[0];
  const last = nodes[nodes.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
    return;
  }
  if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function focusableNodes(root) {
  return Array.from(root.querySelectorAll([
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])"
  ].join(","))).filter((node) => node.getClientRects().length);
}

function restoreModalFocus(target) {
  try {
    if (target && typeof target.focus === "function" && target.getClientRects().length) {
      target.focus({ preventScroll: true });
    }
  } catch (_error) {
    // Focus return is best effort when a route re-render removes the opener.
  }
}

function modalConfig(modalKind) {
  return modalConfigs().find((config) => config.kind === modalKind) || null;
}

function modalConfigs() {
  return [
    {
      kind: "import",
      modalRef: "importModal",
      closeRole: UI.role.importModalClose,
      focusProp: "importModalFocusReady",
      restoreProp: "importModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.chooseFile}"]:not([disabled])`
    },
    {
      kind: "patch",
      modalRef: "patchModal",
      closeRole: UI.role.patchModalClose,
      focusProp: "patchModalFocusReady",
      restoreProp: "patchModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.copyPatch}"]:not([disabled])`
    },
    {
      kind: "edit",
      modalRef: "editModal",
      closeRole: UI.role.editModalClose,
      focusProp: "editModalFocusReady",
      restoreProp: "editModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.editDescription}"]`
    },
    {
      kind: "new",
      modalRef: "newModal",
      closeRole: UI.role.newModalClose,
      focusProp: "newModalFocusReady",
      restoreProp: "newModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.newTagSlug}"]`
    },
    {
      kind: "demote",
      modalRef: "demoteModal",
      closeRole: UI.role.demoteModalClose,
      focusProp: "demoteModalFocusReady",
      restoreProp: "demoteModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.demoteTagSearch}"]`
    },
    {
      kind: "delete",
      modalRef: "deleteModal",
      closeRole: UI.role.deleteModalClose,
      focusProp: "deleteModalFocusReady",
      restoreProp: "deleteModalRestoreFocus",
      focusSelector: `[data-role="${UI.role.confirmDeleteTag}"]:not([disabled])`
    }
  ];
}

function renderTagRegistryNewTagGroupKey(state) {
  if (!state.newTagState) {
    state.refs.newGroupKey.innerHTML = "";
    return;
  }
  state.refs.newGroupKey.innerHTML = getStudioGroups(state).map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"
        data-new-group="${escapeHtml(group)}"
        ${stateAttr(state.newTagState.group === group ? UI.state.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("") + renderGroupInfoControl(state);
}

function renderTagRegistryDemoteGroupKey(state, selectedItems) {
  if (!state.demoteState) {
    state.refs.demoteGroupKey.innerHTML = "";
    return;
  }
  const selected = new Set(selectedItems.map((item) => item && item.group).filter(Boolean));
  state.refs.demoteGroupKey.innerHTML = getStudioGroups(state).map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `<span class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"${stateAttr(selected.has(group) ? UI.state.active : "")} ${titleAttr}>${escapeHtml(group)}</span>`;
  }).join("") + renderGroupInfoControl(state);
}

function renderTagRegistryDemoteTagList(state, selectedItems) {
  if (!state.demoteState) {
    state.refs.demoteTagList.innerHTML = "";
    return;
  }
  const rows = selectedItems.map((item) => `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(item.group || "warning"))}" title="${escapeHtml(item.tagId)}">
      ${escapeHtml(item.label || item.tagId)}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-remove-demote-tag="${escapeHtml(item.tagId)}"
        aria-label="${escapeHtml(registryText(state.config, "remove_target_tag_aria_label", "Remove {tag_id}", { tag_id: item.tagId }))}"
      >
        x
      </button>
    </span>
  `).join("");
  state.refs.demoteTagList.innerHTML = rows || `<span class="${UI_CLASS.empty}">${escapeHtml(registryText(state.config, "empty_state", "none"))}</span>`;
}

function renderPopupTagOptions(state, matches, options = {}) {
  const attribute = options.attribute || "data-popup-tag-id";
  const chips = matches.map((item) => `
    <button
      type="button"
      class="${classNames(UI_CLASS.popupPill, chipGroupClass(item.group))}"
      ${attribute}="${escapeHtml(item.tagId)}"
      title="${escapeHtml(item.tagId)}"
    >
      ${escapeHtml(item.label)}
    </button>
  `);
  if (options.truncated) {
    chips.push(`<span class="${classNames(UI_CLASS.popupPill, UI_CLASS.popupMore)}" title="${escapeHtml(registryText(state.config, "popup_more_title", "More matches available"))}">...</span>`);
  }
  return chips.join("");
}

function renderDeleteTagMeta(state, tag) {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(tag.group), UI_CLASS.deleteMetaTag)}" title="${escapeHtml(tag.tagId)}">
      ${escapeHtml(tag.label)}
    </span>
  `;
}

function renderDeleteImpactCountItem(label, value) {
  return `
    <li class="${UI_CLASS.deleteImpactItem}">
      <span>${escapeHtml(label)}: ${escapeHtml(String(value))}</span>
    </li>
  `;
}

function renderDeleteImpactSeriesItem(state, seriesEntries) {
  const label = registryText(state.config, "delete_impact_series", "series affected");
  const emptyLabel = registryText(state.config, "empty_state", "none");
  const content = seriesEntries.length
    ? `<span class="${UI_CLASS.deleteImpactLinks}">${seriesEntries.map((entry) => `
        <a
          class="${UI_CLASS.deleteImpactLink}"
          href="${escapeHtml(entry.url)}"
          target="_blank"
          rel="noopener noreferrer"
        >${escapeHtml(entry.title)}</a>
      `).join(", ")}</span>`
    : `<span>${escapeHtml(emptyLabel)}</span>`;
  return `
    <li class="${UI_CLASS.deleteImpactItem}">
      <span>${escapeHtml(label)}: </span>${content}
    </li>
  `;
}

function renderGroupInfoControl(state) {
  const title = registryText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = registryText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
  return `
    <a
      class="${classNames(UI_CLASS.keyPill, UI_CLASS.keyInfoButton)}"
      href="${escapeHtml(state.groupInfoPagePath || "")}"
      target="_blank"
      rel="noopener noreferrer"
      title="${escapeHtml(title)}"
      aria-label="${escapeHtml(ariaLabel)}"
    >
      <em>i</em>
    </a>
  `;
}

function groupTitleAttr(state, group) {
  const description = String(state.groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function getStudioGroups(state) {
  return Array.isArray(state.studioGroups) && state.studioGroups.length
    ? state.studioGroups
    : ["subject", "domain", "form", "theme"];
}

function normalizeModalValue(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function setStatusText(target, kind, message, baseClass = UI_CLASS.formStatus) {
  if (!target) return;
  target.textContent = message || "";
  target.className = baseClass;
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function stateAttr(stateValue) {
  return stateValue ? ` data-state="${escapeHtml(stateValue)}"` : "";
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
