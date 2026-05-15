import { getStudioText } from "./studio-config.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import { tagAliasesUi } from "./studio-ui.js";

const UI = tagAliasesUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

export function renderTagAliasesModals(state) {
  return [
    renderImportModal(state),
    renderPatchModal(state),
    renderPromotionModal(state),
    renderDemoteModal(state),
    renderEditModal(state)
  ].join("");
}

export function collectTagAliasesModalRefs(root) {
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
    promotionModal: root.querySelector(UI_SELECTOR.promotionModal),
    promotionAliasMeta: root.querySelector(UI_SELECTOR.promotionAliasMeta),
    promotionGroupKey: root.querySelector(UI_SELECTOR.promotionGroupKey),
    promotionStatus: root.querySelector(UI_SELECTOR.promotionStatus),
    confirmPromotion: root.querySelector(UI_SELECTOR.confirmPromotion),
    demoteModal: root.querySelector(UI_SELECTOR.demoteModal),
    demoteTagMeta: root.querySelector(UI_SELECTOR.demoteTagMeta),
    demoteTagSearch: root.querySelector(UI_SELECTOR.demoteTagSearch),
    demoteTagPopupWrap: root.querySelector(UI_SELECTOR.demoteTagPopupWrap),
    demoteTagPopup: root.querySelector(UI_SELECTOR.demoteTagPopup),
    demoteGroupKey: root.querySelector(UI_SELECTOR.demoteGroupKey),
    demoteTagList: root.querySelector(UI_SELECTOR.demoteTagList),
    demoteStatus: root.querySelector(UI_SELECTOR.demoteStatus),
    confirmDemote: root.querySelector(UI_SELECTOR.confirmDemote),
    editModal: root.querySelector(UI_SELECTOR.editModal),
    editModalTitle: root.querySelector(UI_SELECTOR.editModalTitle),
    editAliasName: root.querySelector(UI_SELECTOR.editAliasName),
    editAliasWarning: root.querySelector(UI_SELECTOR.editAliasWarning),
    editAliasDescription: root.querySelector(UI_SELECTOR.editAliasDescription),
    editTagSearch: root.querySelector(UI_SELECTOR.editTagSearch),
    editTagPopupWrap: root.querySelector(UI_SELECTOR.editTagPopupWrap),
    editTagPopup: root.querySelector(UI_SELECTOR.editTagPopup),
    editGroupKey: root.querySelector(UI_SELECTOR.editGroupKey),
    editTagList: root.querySelector(UI_SELECTOR.editTagList),
    editStatus: root.querySelector(UI_SELECTOR.editStatus),
    saveEditAlias: root.querySelector(UI_SELECTOR.saveEditAlias)
  };
}

export function showTagAliasesImportModal(state) {
  state.importModalOpen = true;
  state.refs.importModal.hidden = false;
}

export function hideTagAliasesImportModal(state) {
  state.importModalOpen = false;
  state.refs.importModal.hidden = true;
}

export function setTagAliasesSelectedImportFile(state, file) {
  state.selectedFile = file || null;
  if (state.selectedFile) {
    state.refs.selectedFile.textContent = aliasesText(
      state.config,
      "selected_file_template",
      "Selected: {filename}",
      { filename: state.selectedFile.name }
    );
    clearTagAliasesImportResult(state);
    return;
  }
  state.refs.selectedFile.textContent = "";
}

export function setTagAliasesImportResult(state, kind, message) {
  setStatusText(state.refs.importResult, kind, message, UI_CLASS.toolbarResult);
}

export function clearTagAliasesImportResult(state) {
  setTagAliasesImportResult(state, "", "");
}

export function showTagAliasesPatchModal(state, snippet) {
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
}

export function hideTagAliasesPatchModal(state) {
  state.refs.patchModal.hidden = true;
}

export function openTagAliasesPromotionModal(state, aliasKey, suggestedGroup) {
  state.promotionState = {
    aliasKey,
    group: getStudioGroups(state).includes(suggestedGroup) ? suggestedGroup : ""
  };
  updateTagAliasesPromotionUi(state);
  state.refs.promotionModal.hidden = false;
}

export function closeTagAliasesPromotionModal(state) {
  state.promotionState = null;
  state.refs.promotionModal.hidden = true;
  state.refs.promotionAliasMeta.textContent = "";
  state.refs.promotionGroupKey.innerHTML = "";
  setTagAliasesPromotionStatus(state, "", "");
  state.refs.confirmPromotion.disabled = true;
}

export function updateTagAliasesPromotionUi(state) {
  if (!state.promotionState || !state.refs.promotionAliasMeta || !state.refs.confirmPromotion) return;
  state.refs.promotionAliasMeta.textContent = aliasesText(
    state.config,
    "promotion_alias_meta",
    "Alias: {alias_key}",
    { alias_key: state.promotionState.aliasKey }
  );
  renderPromotionGroupKey(state);
  if (!state.promotionState.group) {
    setTagAliasesPromotionStatus(state, "", aliasesText(state.config, "promotion_group_required", "Choose a group."));
    state.refs.confirmPromotion.disabled = true;
    return;
  }
  setTagAliasesPromotionStatus(state, "", "");
  state.refs.confirmPromotion.disabled = false;
}

export function setTagAliasesPromotionStatus(state, kind, message) {
  if (!state.refs.promotionStatus) return;
  setStatusText(state.refs.promotionStatus, kind, message);
}

export function setTagAliasesDemoteStatus(state, kind, message) {
  setStatusText(state.refs.demoteStatus, kind, message);
}

export function showTagAliasesDemoteTagPopup(state, html) {
  state.refs.demoteTagPopup.innerHTML = html || "";
  state.refs.demoteTagPopupWrap.hidden = false;
}

export function hideTagAliasesDemoteTagPopup(state) {
  state.refs.demoteTagPopupWrap.hidden = true;
  state.refs.demoteTagPopup.innerHTML = "";
}

export function setTagAliasesEditStatus(state, kind, message) {
  setStatusText(state.refs.editStatus, kind, message);
}

export function showTagAliasesEditTagPopup(state, html) {
  state.refs.editTagPopup.innerHTML = html || "";
  state.refs.editTagPopupWrap.hidden = false;
}

export function hideTagAliasesEditTagPopup(state) {
  state.refs.editTagPopupWrap.hidden = true;
  state.refs.editTagPopup.innerHTML = "";
}

function renderImportModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.importModalClose,
    titleId: "tagAliasesImportTitle",
    title: aliasesText(state.config, "import_modal_title", "Import Aliases"),
    hidden: !state.importModalOpen,
    bodyHtml: `
      <div class="tagStudioToolbar tagStudioToolbar--modalImport">
        <div class="tagStudioToolbar__row">
          <button type="button" class="tagStudio__button" data-role="${UI.role.chooseFile}">${escapeHtml(aliasesText(state.config, "choose_file_button", "Choose file"))}</button>
          <input type="file" data-role="${UI.role.importFile}" accept=".json,application/json" hidden>
          <select class="tagStudioToolbar__select" data-role="${UI.role.importMode}">
            <option value="add">${escapeHtml(aliasesText(state.config, "import_mode_option_add", "add (no overwrite)"))}</option>
            <option value="merge">${escapeHtml(aliasesText(state.config, "import_mode_option_merge", "add + overwrite"))}</option>
            <option value="replace">${escapeHtml(aliasesText(state.config, "import_mode_option_replace", "replace entire aliases"))}</option>
          </select>
          <button type="button" class="tagStudio__button" data-role="${UI.role.importButton}">${escapeHtml(aliasesText(state.config, "import_button", "Import"))}</button>
        </div>
        <p class="tagStudioToolbar__selected" data-role="${UI.role.selectedFile}"></p>
        <p class="tagStudioToolbar__result" data-role="${UI.role.importResult}"></p>
      </div>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.importModalClose, label: aliasesText(state.config, "import_modal_close_button", "Close") }
    ])
  });
}

function renderPatchModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.patchModal,
    backdropRole: UI.role.patchModalClose,
    titleId: "tagAliasesPatchTitle",
    title: aliasesText(state.config, "patch_modal_title", "Aliases Patch Preview"),
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(aliasesText(state.config, "patch_modal_label", "Manual patch snippet"))}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.patchSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.copyPatch, label: aliasesText(state.config, "patch_modal_copy_button", "Copy") },
      { role: UI.role.patchModalClose, label: aliasesText(state.config, "patch_modal_close_button", "Close") }
    ])
  });
}

function renderPromotionModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.promotionModal,
    backdropRole: UI.role.promotionModalClose,
    titleId: "tagAliasesPromotionTitle",
    title: aliasesText(state.config, "promotion_modal_title", "Promote Alias"),
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.promotionAliasMeta}"></p>
      <p class="${UI_CLASS.formStatus}">${escapeHtml(aliasesText(state.config, "promotion_modal_prompt", "Choose the canonical tag group for this alias."))}</p>
      <div class="tagStudio__key ${UI_CLASS.formKey}" data-role="${UI.role.promotionGroupKey}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.promotionStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.confirmPromotion, label: aliasesText(state.config, "promotion_button", "Promote"), disabled: true },
      { role: UI.role.promotionModalClose, label: aliasesText(state.config, "promotion_cancel_button", "Cancel") }
    ])
  });
}

function renderDemoteModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.demoteModal,
    backdropRole: UI.role.demoteModalClose,
    titleId: "tagAliasesDemotionTitle",
    title: aliasesText(state.config, "demotion_modal_title", "Demote Tag to Alias"),
    bodyHtml: `
      <p class="${UI_CLASS.formMeta}" data-role="${UI.role.demoteTagMeta}">${escapeHtml(aliasesText(state.config, "demotion_modal_meta", "tag: {tag_id} -> alias \"{alias_key}\""))}</p>
      <div class="tagStudio__key ${UI_CLASS.formKey}" data-role="${UI.role.demoteGroupKey}"></div>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField} ${UI_CLASS.formSearchWrap}">
          <input type="text" class="tagStudio__input" data-role="${UI.role.demoteTagSearch}" autocomplete="off" placeholder="${escapeHtml(aliasesText(state.config, "demotion_search_placeholder", "search tags"))}">
          <div class="${UI_CLASS.popup}" data-role="${UI.role.demoteTagPopupWrap}" hidden>
            <div class="${UI_CLASS.popupInner}" data-role="${UI.role.demoteTagPopup}"></div>
          </div>
        </label>
      </div>
      <div class="tagStudio__chipList ${UI_CLASS.formSelected}" data-role="${UI.role.demoteTagList}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.demoteStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.confirmDemote, label: aliasesText(state.config, "demotion_confirm_button", "Demote"), disabled: true },
      { role: UI.role.demoteModalClose, label: aliasesText(state.config, "demotion_cancel_button", "Cancel") }
    ])
  });
}

function renderEditModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.editModal,
    titleId: "tagAliasesEditTitle",
    titleRole: UI.role.editModalTitle,
    title: aliasesText(state.config, "edit_modal_title", "Edit Alias"),
    dialogClass: UI_CLASS.editDialog,
    bodyHtml: `
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(aliasesText(state.config, "edit_alias_label", "alias"))}</span>
          <input type="text" class="tagStudio__input" data-role="${UI.role.editAliasName}" autocomplete="off">
        </label>
        <p class="${UI_CLASS.formWarning}" data-role="${UI.role.editAliasWarning}"></p>
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(aliasesText(state.config, "edit_description_label", "description"))}</span>
          <textarea class="tagStudio__input ${UI_CLASS.editDescription}" data-role="${UI.role.editAliasDescription}" rows="2"></textarea>
        </label>
        <div class="tagStudio__key ${UI_CLASS.formKey}" data-role="${UI.role.editGroupKey}"></div>
        <label class="${UI_CLASS.formField} ${UI_CLASS.formSearchWrap}">
          <input type="text" class="tagStudio__input" data-role="${UI.role.editTagSearch}" autocomplete="off" placeholder="${escapeHtml(aliasesText(state.config, "edit_search_placeholder", "search tags"))}">
          <div class="${UI_CLASS.popup}" data-role="${UI.role.editTagPopupWrap}" hidden>
            <div class="${UI_CLASS.popupInner}" data-role="${UI.role.editTagPopup}"></div>
          </div>
        </label>
      </div>
      <div class="tagStudio__chipList ${UI_CLASS.formSelected}" data-role="${UI.role.editTagList}"></div>
      <p class="${UI_CLASS.formStatus}" data-role="${UI.role.editStatus}"></p>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.saveEditAlias, label: aliasesText(state.config, "edit_save_button", "Save"), disabled: true },
      { role: UI.role.editModalClose, label: aliasesText(state.config, "edit_cancel_button", "Cancel") }
    ])
  });
}

function renderPromotionGroupKey(state) {
  if (!state.refs.promotionGroupKey) return;
  if (!state.promotionState) {
    state.refs.promotionGroupKey.innerHTML = "";
    return;
  }
  state.refs.promotionGroupKey.innerHTML = getStudioGroups(state).map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"
        data-promotion-group="${escapeHtml(group)}"
        ${stateAttr(state.promotionState.group === group ? UI.state.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("") + renderGroupInfoControl(state);
}

function renderGroupInfoControl(state) {
  const title = aliasesText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = aliasesText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
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

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
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
