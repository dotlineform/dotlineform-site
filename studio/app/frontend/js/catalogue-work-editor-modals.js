import {
  buildWorkEmbeddedDeleteConfirmation,
  buildWorkEmbeddedEntry,
  buildWorkEmbeddedModalDescriptor,
  validateWorkEmbeddedEntryValues
} from "./catalogue-editor-embedded-items.js";
import {
  activateStudioModalFrame,
  openConfirmModal,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";

const ENTRY_SAVE_ROLE = "entry-modal-save";
const ENTRY_CANCEL_ROLE = "entry-modal-cancel";
const SECTION_SAVE_ROLE = "detail-section-modal-save";
const SECTION_CANCEL_ROLE = "detail-section-modal-cancel";
const DETAIL_SORT_MODES = new Set(["detail_id", "title"]);

export function closeCatalogueWorkModal(state) {
  if (state && state.activeModalController) {
    const controller = state.activeModalController;
    state.activeModalController = null;
    controller.destroy({ restoreFocus: false });
    return;
  }
  if (state && state.modalHost) state.modalHost.innerHTML = "";
}

export function openWorkEmbeddedEntryModal(state, kind, index = null, options = {}) {
  if (!state || !state.currentRecord || state.mode === "bulk") return Promise.resolve(null);
  const text = options.text;
  const descriptor = buildWorkEmbeddedModalDescriptor(kind, index, {
    draft: state.draft,
    text
  });
  if (!descriptor) return Promise.resolve(null);
  const firstField = descriptor.fields[0];
  const secondField = descriptor.fields[1];

  closeCatalogueWorkModal(state);
  state.modalHost.innerHTML = renderWorkEmbeddedEntryModalHtml(descriptor, { text });

  const controller = activateStudioModalFrame(state.modalHost, {
    cancelRoles: [ENTRY_CANCEL_ROLE],
    submitRoles: [ENTRY_SAVE_ROLE],
    focusSelector: `#${firstField.fieldId}`,
    selectInitialFocus: true,
    onSubmit(api) {
      const firstNode = state.modalHost.querySelector(`#${firstField.fieldId}`);
      const secondNode = state.modalHost.querySelector(`#${secondField.fieldId}`);
      const firstValue = normalizeText(firstNode && firstNode.value);
      const secondValue = normalizeText(secondNode && secondNode.value);
      const validationMessage = validateWorkEmbeddedEntryValues(kind, firstValue, secondValue, { text });
      if (validationMessage) {
        api.setStatus("error", validationMessage);
        if (firstNode && !firstValue) firstNode.focus();
        else if (secondNode && !secondValue) secondNode.focus();
        return false;
      }
      const nextEntry = buildWorkEmbeddedEntry(kind, firstValue, secondValue);
      const nextEntries = descriptor.entries.slice();
      if (descriptor.editing) {
        nextEntries[index] = nextEntry;
      } else {
        nextEntries.push(nextEntry);
      }
      return {
        entriesKey: descriptor.entriesKey,
        entries: nextEntries,
        entry: nextEntry,
        editing: descriptor.editing,
        index: descriptor.editing ? index : null
      };
    }
  });
  state.activeModalController = controller;
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}

export async function confirmWorkEmbeddedDeleteModal(state, kind, index, options = {}) {
  if (!state || !state.currentRecord || state.mode === "bulk") return null;
  const text = options.text;
  const confirmation = buildWorkEmbeddedDeleteConfirmation(kind, state.draft, index, { text });
  if (!confirmation) return null;
  const result = await openConfirmModal({
    root: state.root,
    title: confirmation.title,
    body: confirmation.body,
    primaryLabel: lookupText(text, "entry_modal_delete_button", "Delete"),
    cancelLabel: lookupText(text, "entry_modal_cancel_button", "Cancel"),
    defaultAction: "cancel",
    size: "compact"
  });
  if (!result || !result.confirmed) return { confirmed: false };
  const nextEntries = confirmation.entries.slice();
  nextEntries.splice(index, 1);
  return {
    confirmed: true,
    entriesKey: confirmation.entriesKey,
    entries: nextEntries,
    index
  };
}

export function openWorkDetailSectionEditModal(state, row, rows = [], options = {}) {
  if (!state || !state.currentRecord || state.mode === "bulk") return Promise.resolve(null);
  const text = options.text;
  const section = row && row.section ? row.section : {};
  const sectionId = normalizeText(row && row.id);
  if (!sectionId) return Promise.resolve(null);

  const orderedRows = Array.isArray(rows) ? rows : [];
  const totalSections = orderedRows.length || 1;
  const currentPosition = Math.max(1, orderedRows.findIndex((candidate) => normalizeText(candidate && candidate.id) === sectionId) + 1);
  const currentTitle = normalizeText(section.section_title || row.label);
  const currentSort = normalizeDetailSort(section.detail_sort);
  const descriptor = {
    title: lookupText(text, "detail_section_edit_modal_title", "Edit detail section"),
    titleId: "catalogueWorkDetailSectionEditTitle",
    statusId: "catalogueWorkDetailSectionEditStatus",
    sectionId,
    totalSections,
    currentPosition,
    currentTitle,
    currentSort
  };

  closeCatalogueWorkModal(state);
  state.modalHost.innerHTML = renderDetailSectionEditModalHtml(descriptor, { text });

  const controller = activateStudioModalFrame(state.modalHost, {
    cancelRoles: [SECTION_CANCEL_ROLE],
    submitRoles: [SECTION_SAVE_ROLE],
    focusSelector: "#catalogueWorkDetailSectionTitle",
    selectInitialFocus: true,
    onSubmit(api) {
      const titleNode = state.modalHost.querySelector("#catalogueWorkDetailSectionTitle");
      const orderNode = state.modalHost.querySelector("#catalogueWorkDetailSectionOrder");
      const sortNode = state.modalHost.querySelector("#catalogueWorkDetailSectionSort");
      const sectionTitle = normalizeText(titleNode && titleNode.value);
      if (!sectionTitle) {
        api.setStatus("error", lookupText(text, "detail_section_edit_title_required", "Enter a section title."));
        if (titleNode && typeof titleNode.focus === "function") titleNode.focus();
        return false;
      }
      const rawPosition = normalizeText(orderNode && orderNode.value);
      const sectionPosition = Number(rawPosition);
      if (totalSections > 1 && (!Number.isInteger(sectionPosition) || sectionPosition < 1 || sectionPosition > totalSections)) {
        api.setStatus("error", lookupText(text, "detail_section_edit_order_invalid", "Enter a section order from 1 to {count}.", {
          count: String(totalSections)
        }));
        if (orderNode && typeof orderNode.focus === "function") orderNode.focus();
        return false;
      }
      const detailSort = normalizeDetailSort(sortNode && sortNode.value);
      if (!DETAIL_SORT_MODES.has(detailSort)) {
        api.setStatus("error", lookupText(text, "detail_section_edit_sort_invalid", "Choose a detail sort."));
        if (sortNode && typeof sortNode.focus === "function") sortNode.focus();
        return false;
      }
      const payload = {
        section_id: sectionId,
        section_title: sectionTitle,
        detail_sort: detailSort
      };
      if (totalSections > 1) {
        payload.section_position = sectionPosition;
      }
      return {
        sectionId,
        payload,
        changed: sectionTitle !== currentTitle
          || detailSort !== currentSort
          || (totalSections > 1 && sectionPosition !== currentPosition)
      };
    }
  });
  state.activeModalController = controller;
  return controller.promise.finally(() => {
    if (state.activeModalController === controller) state.activeModalController = null;
  });
}

export function renderWorkEmbeddedEntryModalHtml(descriptor, options = {}) {
  const text = options.text;
  const firstField = descriptor.fields[0];
  const secondField = descriptor.fields[1];
  return renderStudioModalFrame({
    hidden: false,
    title: descriptor.title,
    titleId: descriptor.titleId,
    modalRole: "studio-modal",
    backdropRole: ENTRY_CANCEL_ROLE,
    bodyHtml: `
      <div class="studioForm__fields">
        ${modalFieldHtml(firstField)}
        ${modalFieldHtml(secondField)}
      </div>
      <p class="studioForm__status studioModal__status" data-role="modal-status" id="${escapeHtml(descriptor.statusId)}" hidden></p>
    `,
    actions: [
      { role: ENTRY_CANCEL_ROLE, label: lookupText(text, "entry_modal_cancel_button", "Cancel") },
      { role: ENTRY_SAVE_ROLE, label: lookupText(text, "entry_modal_save_button", "Save"), primary: true }
    ]
  });
}

function renderDetailSectionEditModalHtml(descriptor, options = {}) {
  const text = options.text;
  const orderDisabled = descriptor.totalSections <= 1;
  return renderStudioModalFrame({
    hidden: false,
    title: descriptor.title,
    titleId: descriptor.titleId,
    modalRole: "studio-modal",
    backdropRole: SECTION_CANCEL_ROLE,
    bodyHtml: `
      <div class="studioForm__fields">
        <label class="studioForm__field" for="catalogueWorkDetailSectionTitle">
          <span class="studioForm__label">${escapeHtml(lookupText(text, "detail_section_title_label", "section title"))}</span>
          <input class="studioUi__input" id="catalogueWorkDetailSectionTitle" type="text" value="${escapeHtml(descriptor.currentTitle)}">
        </label>
        <label class="studioForm__field" for="catalogueWorkDetailSectionOrder">
          <span class="studioForm__label">${escapeHtml(lookupText(text, "detail_section_order_label", "order"))}</span>
          <input class="studioUi__input" id="catalogueWorkDetailSectionOrder" type="number" min="1" max="${escapeHtml(descriptor.totalSections)}" step="1" value="${escapeHtml(descriptor.currentPosition)}"${orderDisabled ? " disabled" : ""}>
        </label>
        <label class="studioForm__field" for="catalogueWorkDetailSectionSort">
          <span class="studioForm__label">${escapeHtml(lookupText(text, "detail_section_detail_sort_label", "detail sort"))}</span>
          <select class="studioUi__input" id="catalogueWorkDetailSectionSort">
            ${detailSortOptionHtml("detail_id", lookupText(text, "detail_section_detail_sort_id", "id"), descriptor.currentSort)}
            ${detailSortOptionHtml("title", lookupText(text, "detail_section_detail_sort_title", "title"), descriptor.currentSort)}
          </select>
        </label>
      </div>
      <p class="studioForm__status studioModal__status" data-role="modal-status" id="${escapeHtml(descriptor.statusId)}" hidden></p>
    `,
    actions: [
      { role: SECTION_CANCEL_ROLE, label: lookupText(text, "entry_modal_cancel_button", "Cancel") },
      { role: SECTION_SAVE_ROLE, label: lookupText(text, "entry_modal_save_button", "Save"), primary: true }
    ]
  });
}

function modalFieldHtml({ fieldId, label, value, type = "text" }) {
  return `
    <label class="studioForm__field" for="${escapeHtml(fieldId)}">
      <span class="studioForm__label">${escapeHtml(label)}</span>
      <input class="studioUi__input" id="${escapeHtml(fieldId)}" type="${escapeHtml(type)}" value="${escapeHtml(value)}">
    </label>
  `;
}

function detailSortOptionHtml(value, label, selectedValue) {
  return `<option value="${escapeHtml(value)}"${value === selectedValue ? " selected" : ""}>${escapeHtml(label)}</option>`;
}

function normalizeDetailSort(value) {
  const text = normalizeText(value);
  return text === "title" ? "title" : "detail_id";
}

function lookupText(text, key, fallback, tokens = null) {
  return typeof text === "function" ? text(key, fallback, tokens) : interpolateText(fallback, tokens);
}

function interpolateText(template, tokens = null) {
  let text = normalizeText(template);
  if (!tokens || typeof tokens !== "object") return text;
  Object.entries(tokens).forEach(([key, value]) => {
    text = text.replaceAll(`{${key}}`, String(value == null ? "" : value));
  });
  return text;
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
