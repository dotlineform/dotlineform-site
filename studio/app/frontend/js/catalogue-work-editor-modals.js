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
      <div class="tagStudioForm__fields">
        ${modalFieldHtml(firstField)}
        ${modalFieldHtml(secondField)}
      </div>
      <p class="tagStudioForm__status tagStudioModal__status" data-role="modal-status" id="${escapeHtml(descriptor.statusId)}" hidden></p>
    `,
    actions: [
      { role: ENTRY_CANCEL_ROLE, label: lookupText(text, "entry_modal_cancel_button", "Cancel") },
      { role: ENTRY_SAVE_ROLE, label: lookupText(text, "entry_modal_save_button", "Save"), primary: true }
    ]
  });
}

function modalFieldHtml({ fieldId, label, value, type = "text" }) {
  return `
    <label class="tagStudioForm__field" for="${escapeHtml(fieldId)}">
      <span class="tagStudioForm__label">${escapeHtml(label)}</span>
      <input class="tagStudio__input" id="${escapeHtml(fieldId)}" type="${escapeHtml(type)}" value="${escapeHtml(value)}">
    </label>
  `;
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
