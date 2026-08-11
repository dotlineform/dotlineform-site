import { getStudioText } from "./studio-config.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  captureTagModalRestoreFocus,
  chipGroupClass as tagChipGroupClass,
  classNames,
  closeTagModalByKind,
  escapeHtml,
  getOpenTagModalKind,
  getTagModalElement,
  restoreTagModalFocus,
  setStatusText as setTagModalStatusText,
  stateAttr,
  syncTagModalFocusAfterOpen,
  trapTagModalFocus
} from "./tag-modal-shell.js";
import { tagRegistryUi } from "./tag-ui.js";
import {
  tagRegistryDocumentHref,
  sameTagDocumentTarget
} from "./tag-registry-documents.js";

const UI = tagRegistryUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

export function renderTagRegistryModals(state) {
  return [
    renderPatchModal(state),
    renderEditModal(state),
    renderNewModal(state),
    renderDemoteModal(state),
    renderDeleteModal(state)
  ].join("");
}

export function collectTagRegistryModalRefs(root) {
  return {
    patchModal: root.querySelector(UI_SELECTOR.patchModal),
    patchSnippet: root.querySelector(UI_SELECTOR.patchSnippet),
    copyPatch: root.querySelector(UI_SELECTOR.copyPatch),
    editModal: root.querySelector(UI_SELECTOR.editModal),
    editTitle: root.querySelector(UI_SELECTOR.editTitle),
    editGroupKey: root.querySelector(UI_SELECTOR.editGroupKey),
    editDocumentList: root.querySelector(UI_SELECTOR.editDocumentList),
    editStatus: root.querySelector(UI_SELECTOR.editStatus),
    saveEdit: root.querySelector(UI_SELECTOR.saveEdit),
    newModal: root.querySelector(UI_SELECTOR.newModal),
    newGroupKey: root.querySelector(UI_SELECTOR.newGroupKey),
    newTagSlug: root.querySelector(UI_SELECTOR.newTagSlug),
    newTagWarning: root.querySelector(UI_SELECTOR.newTagWarning),
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
  state.refs.patchModal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.patchModalClose)) return;
    hideTagRegistryPatchModal(state);
  });

  state.refs.copyPatch.addEventListener("click", () => {
    callbacks.onPatchCopy?.();
  });

  state.refs.editModal.addEventListener("click", (event) => {
    if (event.target.closest(UI_SELECTOR.editModalClose)) {
      closeTagRegistryEditModal(state);
      callbacks.onModalStateChange?.();
      return;
    }
    const primaryButton = event.target.closest(
      "button[data-select-edit-primary]"
    );
    if (primaryButton && state.editTagId) {
      callbacks.onEditPrimarySelect?.({
        scope: "analysis",
        sub_scope: "tags",
        doc_id: primaryButton.getAttribute("data-select-edit-primary")
      });
      return;
    }
    const groupButton = event.target.closest("button[data-edit-group]");
    if (!groupButton || !state.editTagId) return;
    const group = normalizeModalValue(groupButton.getAttribute("data-edit-group"));
    if (!getStudioGroups(state).includes(group)) return;
    state.editTagGroup = group;
    renderTagRegistryEditGroupKey(state);
    callbacks.onEditGroupInput?.();
  });

  state.refs.saveEdit.addEventListener("click", () => {
    callbacks.onEditSave?.();
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
    const modalKind = getOpenTagModalKind(state, modalConfigs());
    if (!modalKind) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeTagModalByKind(state, modalKind, tagRegistryModalCloseHandlers);
      callbacks.onModalStateChange?.();
      return;
    }

    if (event.key !== "Tab") return;
    trapTagModalFocus(event, getTagModalElement(state, modalKind, modalConfigs()));
  });
}

export function setTagRegistryRouteResult(state, kind, message) {
  setStatusText(state.refs.routeResult, kind, message, UI_CLASS.toolbarResult);
}

export function clearTagRegistryRouteResult(state) {
  setTagRegistryRouteResult(state, "", "");
}

export function showTagRegistryPatchModal(state, snippet) {
  captureTagModalRestoreFocus(state, "patch", modalConfigs());
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
  state.patchModalFocusReady = false;
  syncTagModalFocusAfterOpen(state, "patch", modalConfigs());
}

export function hideTagRegistryPatchModal(state) {
  const restoreTarget = state.patchModalRestoreFocus;
  state.refs.patchModal.hidden = true;
  state.patchModalFocusReady = false;
  state.patchModalRestoreFocus = null;
  restoreTagModalFocus(restoreTarget);
}

export function openTagRegistryEditModal(state, tag) {
  captureTagModalRestoreFocus(state, "edit", modalConfigs());
  state.editTagId = tag.tagId;
  state.editTagGroup = tag.group;
  state.editTagPrimaryDocument = tag.primaryDocument
    ? { ...tag.primaryDocument }
    : null;
  state.editTagPrimaryChanged = false;
  state.editTagDocuments = Array.isArray(tag.documents)
    ? tag.documents.map((document) => ({
        ...document,
        target: { ...document.target }
      }))
    : [];
  state.editTagUnavailablePrimary = tag.unavailablePrimary
    ? { target: { ...tag.unavailablePrimary.target } }
    : null;
  state.refs.editTitle.textContent = tag.tagId;
  renderTagRegistryEditGroupKey(state);
  renderTagRegistryEditDocuments(state);
  setStatusText(
    state.refs.editStatus,
    "",
    state.saveMode === "post"
      ? ""
      : registryText(state.config, "local_edit_required", "Local server is required for edit.")
  );
  state.refs.editModal.hidden = false;
  state.editModalFocusReady = false;
  syncTagModalFocusAfterOpen(state, "edit", modalConfigs());
}

export function closeTagRegistryEditModal(state) {
  const restoreTarget = state.editModalRestoreFocus;
  state.refs.editModal.hidden = true;
  state.editModalFocusReady = false;
  state.editModalRestoreFocus = null;
  state.editTagId = "";
  state.editTagGroup = "";
  state.editTagPrimaryDocument = null;
  state.editTagPrimaryChanged = false;
  state.editTagDocuments = [];
  state.editTagUnavailablePrimary = null;
  state.refs.editTitle.textContent = registryText(
    state.config,
    "edit_modal_title",
    "Edit Tag"
  );
  state.refs.editGroupKey.innerHTML = "";
  state.refs.editDocumentList.innerHTML = "";
  restoreTagModalFocus(restoreTarget);
}

export function renderTagRegistryEditDocuments(state) {
  const documents = Array.isArray(state.editTagDocuments)
    ? state.editTagDocuments
    : [];
  const unavailableText = registryText(
    state.config,
    "unavailable_document",
    "Unavailable document"
  );
  const currentPills = documents.map((record) => {
        const title = record.title || record.target.doc_id;
        const selected = sameTagDocumentTarget(
          state.editTagPrimaryDocument,
          record.target
        );
        const label = record.url
          ? `<a
              class="tagRegistryEdit__documentLabel"
              href="${escapeHtml(tagRegistryDocumentHref(state.config, record.url))}"
              target="_blank"
              rel="noopener noreferrer"
            >${escapeHtml(title)}</a>`
          : `<span class="tagRegistryEdit__documentLabel">${escapeHtml(title)}</span>`;
        return `
          <span
            class="analytics__chip analytics__chip--inherited tagRegistryEdit__documentPill"
          >
            ${label}
            <button
              type="button"
              class="tagRegistryEdit__primarySelector"
              data-select-edit-primary="${escapeHtml(record.target.doc_id)}"
              role="radio"
              aria-checked="${selected ? "true" : "false"}"
              title="${escapeHtml(selected ? `${title} is primary` : `Make ${title} primary`)}"
              aria-label="${escapeHtml(selected ? `${title} is the primary document` : `Make ${title} the primary document`)}"
            ><span aria-hidden="true"></span></button>
          </span>
        `;
      }).join("");
  const showUnavailable = state.editTagUnavailablePrimary
    && sameTagDocumentTarget(
      state.editTagPrimaryDocument,
      state.editTagUnavailablePrimary.target
    );
  const unavailablePill = showUnavailable
    ? `<span
        class="analytics__chip analytics__chip--warning tagRegistryEdit__documentPill tagRegistryEdit__unavailablePrimary"
        title="${escapeHtml(state.editTagUnavailablePrimary.target.doc_id)}"
      >${escapeHtml(unavailableText)} — ${escapeHtml(state.editTagUnavailablePrimary.target.doc_id)}</span>`
    : "";
  state.refs.editDocumentList.innerHTML = (currentPills || unavailablePill)
    ? `${currentPills}${unavailablePill}`
    : `<span class="${UI_CLASS.empty}">${escapeHtml(
        registryText(state.config, "no_linked_documents", "No linked documents.")
      )}</span>`;
}

export function openTagRegistryNewModal(state) {
  captureTagModalRestoreFocus(state, "new", modalConfigs());
  state.newTagState = {
    group: "",
    slug: ""
  };
  state.refs.newTagSlug.value = "";
  state.refs.newTagWarning.textContent = "";
  setStatusText(state.refs.newTagStatus, "", "");
  renderTagRegistryNewTagGroupKey(state);
  state.refs.createTag.disabled = true;
  state.refs.newModal.hidden = false;
  state.newModalFocusReady = false;
  syncTagModalFocusAfterOpen(state, "new", modalConfigs());
}

export function closeTagRegistryNewModal(state) {
  const restoreTarget = state.newModalRestoreFocus;
  state.newTagState = null;
  state.refs.newModal.hidden = true;
  state.newModalFocusReady = false;
  state.newModalRestoreFocus = null;
  state.refs.newTagSlug.value = "";
  state.refs.newTagWarning.textContent = "";
  setStatusText(state.refs.newTagStatus, "", "");
  state.refs.newGroupKey.innerHTML = "";
  state.refs.createTag.disabled = true;
  restoreTagModalFocus(restoreTarget);
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
  captureTagModalRestoreFocus(state, "demote", modalConfigs());
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
  syncTagModalFocusAfterOpen(state, "demote", modalConfigs());
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
  restoreTagModalFocus(restoreTarget);
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
  captureTagModalRestoreFocus(state, "delete", modalConfigs());
  state.deleteTagId = tag.tagId;
  state.deletePreview = "";
  state.deletePreviewSeq += 1;
  state.refs.deleteTagMeta.innerHTML = renderDeleteTagMeta(state, tag);
  setStatusText(state.refs.deleteImpact, "", "", UI_CLASS.formImpact);
  setStatusText(state.refs.deleteStatus, "", "");
  state.refs.confirmDeleteTag.disabled = true;
  state.refs.deleteModal.hidden = false;
  state.deleteModalFocusReady = false;
  syncTagModalFocusAfterOpen(state, "delete", modalConfigs());
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
  restoreTagModalFocus(restoreTarget);
}

export function setTagRegistryDeleteImpactStatus(state, kind, message) {
  setStatusText(state.refs.deleteImpact, kind, message, UI_CLASS.formImpact);
}

export function renderTagRegistryDeleteImpactPreview(state, options = {}) {
  const stats = options.response && typeof options.response === "object" ? options.response : {};
  const affectedSeries = Array.isArray(options.affectedSeries) ? options.affectedSeries : [];
  const documentAssociations = Array.isArray(stats.document_associations)
    ? stats.document_associations
    : [];
  const blocked = stats.blocked === true || documentAssociations.length > 0;
  const aliasesUpdated = Math.max(
    0,
    Number(stats.aliases_rewritten || 0) - Number(stats.aliases_removed_empty || 0) - Number(stats.aliases_removed_redundant || 0)
  );
  const aliasesDeleted = Number(stats.aliases_removed_empty || 0) + Number(stats.aliases_removed_redundant || 0);
  const items = [
    renderDeleteImpactDocumentsItem(state, documentAssociations),
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
  state.refs.confirmDeleteTag.disabled = blocked || state.saveMode !== "post";
  if (blocked) {
    setStatusText(
      state.refs.deleteStatus,
      "error",
      registryText(
        state.config,
        "delete_documents_blocked",
        "Edit or delete the associated documents before deleting this Tag."
      )
    );
  }
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

function renderEditModal(state) {
  return renderStudioModalFrame({
    modalRole: UI.role.editModal,
    backdropRole: UI.role.editModalClose,
    titleId: "tagRegistryEditTitle",
    titleRole: UI.role.editTitle,
    title: registryText(state.config, "edit_modal_title", "Edit Tag"),
    dialogClass: "tagRegistryEdit__dialog",
    bodyHtml: `
      <div class="${UI_CLASS.formFields}">
        <div class="${UI_CLASS.formField} tagRegistryEdit__groupField">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "edit_group_label", "group"))}</span>
          <div class="studioUi__key ${UI_CLASS.newGroupKey}" data-role="${UI.role.editGroupKey}"></div>
        </div>
        <div class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "edit_documents_label", "documents"))}</span>
          <div
            class="tagRegistryEdit__documents"
            data-role="${UI.role.editDocumentList}"
            role="radiogroup"
            aria-label="${escapeHtml(registryText(state.config, "edit_primary_document_label", "Primary document"))}"
          ></div>
        </div>
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
      <div class="studioUi__key ${UI_CLASS.newGroupKey}" data-role="${UI.role.newGroupKey}"></div>
      <div class="${UI_CLASS.formFields}">
        <label class="${UI_CLASS.formField}">
          <span class="${UI_CLASS.formLabel}">${escapeHtml(registryText(state.config, "new_slug_label", "slug"))}</span>
          <input type="text" class="studioUi__input" data-role="${UI.role.newTagSlug}" autocomplete="off">
        </label>
        <p class="${UI_CLASS.formWarning}" data-role="${UI.role.newTagWarning}"></p>
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
          <input type="text" class="studioUi__input" data-role="${UI.role.demoteTagSearch}" autocomplete="off" placeholder="${escapeHtml(registryText(state.config, "demote_search_placeholder", "search tags"))}">
          <div class="${UI_CLASS.popup}" data-role="${UI.role.demoteTagPopupWrap}" hidden>
            <div class="${UI_CLASS.popupInner}" data-role="${UI.role.demoteTagPopup}"></div>
          </div>
        </label>
      </div>
      <div class="studioUi__key ${UI_CLASS.formKey}" data-role="${UI.role.demoteGroupKey}"></div>
      <div class="analytics__chipList ${UI_CLASS.formSelected}" data-role="${UI.role.demoteTagList}"></div>
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
          "Delete is blocked while a document is associated with this Tag. Otherwise, deleting it also removes matching tag assignments and removes it from aliases. Aliases left with no targets are deleted."
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

const tagRegistryModalCloseHandlers = {
  patch: hideTagRegistryPatchModal,
  edit: closeTagRegistryEditModal,
  new: closeTagRegistryNewModal,
  demote: closeTagRegistryDemoteModal,
  delete: closeTagRegistryDeleteModal
};

function modalConfigs() {
  return [
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
      focusSelector: `[data-role="${UI.role.editGroupKey}"] button`
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
        aria-pressed="${state.newTagState.group === group ? "true" : "false"}"
        ${stateAttr(state.newTagState.group === group ? UI.state.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");
}

function renderTagRegistryEditGroupKey(state) {
  if (!state.editTagId) {
    state.refs.editGroupKey.innerHTML = "";
    return;
  }
  state.refs.editGroupKey.innerHTML = getStudioGroups(state).map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group))}"
        data-edit-group="${escapeHtml(group)}"
        aria-pressed="${state.editTagGroup === group ? "true" : "false"}"
        ${stateAttr(state.editTagGroup === group ? UI.state.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");
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
  }).join("");
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
      ${escapeHtml(tag.tagId)}
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

function renderDeleteImpactDocumentsItem(state, associations) {
  const label = registryText(
    state.config,
    "delete_impact_documents",
    "associated documents"
  );
  const emptyLabel = registryText(state.config, "empty_state", "none");
  const links = associations.map((association) => {
    const target = association && association.target;
    const docId = String(target && target.doc_id || "").trim();
    const title = String(association && association.title || "").trim() || docId;
    const url = String(association && association.url || "").trim();
    if (!docId || !url) return "";
    return `
      <a
        class="${UI_CLASS.deleteImpactLink}"
        href="${escapeHtml(url)}"
        target="_blank"
        rel="noopener noreferrer"
      >${escapeHtml(title)} — ${escapeHtml(docId)}</a>
    `;
  }).filter(Boolean);
  const content = links.length
    ? `<span class="${UI_CLASS.deleteImpactLinks}">${links.join(", ")}</span>`
    : `<span>${escapeHtml(emptyLabel)}</span>`;
  return `
    <li class="${UI_CLASS.deleteImpactItem}">
      <span>${escapeHtml(label)}: </span>${content}
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
  setTagModalStatusText(target, kind, message, baseClass);
}

function chipGroupClass(group) {
  return tagChipGroupClass(UI_CLASS, group);
}
