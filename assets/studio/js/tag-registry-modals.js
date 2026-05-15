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

export function showTagRegistryImportModal(state) {
  state.importModalOpen = true;
  state.refs.importModal.hidden = false;
}

export function hideTagRegistryImportModal(state) {
  state.importModalOpen = false;
  state.refs.importModal.hidden = true;
}

export function showTagRegistryPatchModal(state, snippet) {
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
}

export function hideTagRegistryPatchModal(state) {
  state.refs.patchModal.hidden = true;
}

export function showTagRegistryEditModal(state) {
  state.refs.editModal.hidden = false;
}

export function hideTagRegistryEditModal(state) {
  state.refs.editModal.hidden = true;
}

export function showTagRegistryNewModal(state) {
  state.refs.newModal.hidden = false;
}

export function hideTagRegistryNewModal(state) {
  state.refs.newModal.hidden = true;
}

export function showTagRegistryDemoteModal(state) {
  state.refs.demoteModal.hidden = false;
}

export function hideTagRegistryDemoteModal(state) {
  state.refs.demoteModal.hidden = true;
}

export function showTagRegistryDeleteModal(state) {
  state.refs.deleteModal.hidden = false;
}

export function hideTagRegistryDeleteModal(state) {
  state.refs.deleteModal.hidden = true;
}

function renderPatchModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.patchModal,
    backdropRole: UI.role.patchModalClose,
    titleId: "tagRegistryPatchTitle",
    title: registryText(state.config, "patch_modal_title", "Registry Patch Preview"),
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(registryText(state.config, "patch_modal_label", "Manual patch snippet"))}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.patchSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.copyPatch, label: registryText(state.config, "patch_modal_copy_button", "Copy") },
      { role: UI.role.patchModalClose, label: registryText(state.config, "patch_modal_close_button", "Close") }
    ])
  });
}

function renderImportModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.importModalClose,
    titleId: "tagRegistryImportTitle",
    title: registryText(state.config, "import_modal_title", "Import Registry"),
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
      { role: UI.role.saveEdit, label: registryText(state.config, "edit_save_button", "Save") },
      { role: UI.role.editModalClose, label: registryText(state.config, "edit_close_button", "Close") }
    ])
  });
}

function renderNewModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.newModal,
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
      { role: UI.role.createTag, label: registryText(state.config, "new_create_button", "Create"), disabled: true },
      { role: UI.role.newModalClose, label: registryText(state.config, "new_cancel_button", "Cancel") }
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
      { role: UI.role.confirmDemote, label: registryText(state.config, "demote_confirm_button", "Demote"), disabled: true },
      { role: UI.role.demoteModalClose, label: registryText(state.config, "demote_close_button", "Close") }
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
      { role: UI.role.confirmDeleteTag, label: registryText(state.config, "delete_confirm_button", "Delete") },
      { role: UI.role.deleteModalClose, label: registryText(state.config, "delete_close_button", "Close") }
    ])
  });
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
