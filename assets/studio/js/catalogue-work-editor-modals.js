import {
  formatCatalogueBuildPreviewModalHtml
} from "./catalogue-editor-modal-formatters.js";
import {
  buildWorkEmbeddedDeleteConfirmation,
  buildWorkEmbeddedEntry,
  buildWorkEmbeddedModalDescriptor,
  validateWorkEmbeddedEntryValues
} from "./catalogue-editor-embedded-items.js";
import {
  openConfirmModal,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  normalizeText
} from "./catalogue-work-fields.js";

const ENTRY_SAVE_ROLE = "entry-modal-save";
const ENTRY_CANCEL_ROLE = "entry-modal-cancel";
const BUILD_PREVIEW_CLOSE_ROLE = "build-preview-modal-close";

export function closeCatalogueWorkModal(state) {
  if (state && state.modalHost) state.modalHost.innerHTML = "";
  if (state && state.activeModalKeydown) {
    document.removeEventListener("keydown", state.activeModalKeydown);
  }
  if (state) state.activeModalKeydown = null;
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

  const firstNode = state.modalHost.querySelector(`#${firstField.fieldId}`);
  const secondNode = state.modalHost.querySelector(`#${secondField.fieldId}`);
  const statusNode = state.modalHost.querySelector(`#${descriptor.statusId}`);
  const saveNode = state.modalHost.querySelector(`[data-role="${ENTRY_SAVE_ROLE}"]`);
  const cancelNodes = state.modalHost.querySelectorAll(`[data-role="${ENTRY_CANCEL_ROLE}"]`);

  return new Promise((resolve) => {
    const setModalStatus = (message) => {
      if (!statusNode) return;
      statusNode.textContent = message || "";
      if (message) {
        statusNode.dataset.state = "error";
      } else {
        delete statusNode.dataset.state;
      }
    };

    const cancel = () => {
      closeCatalogueWorkModal(state);
      resolve({ confirmed: false });
    };

    const submit = () => {
      const firstValue = normalizeText(firstNode && firstNode.value);
      const secondValue = normalizeText(secondNode && secondNode.value);
      const validationMessage = validateWorkEmbeddedEntryValues(kind, firstValue, secondValue, { text });
      if (validationMessage) {
        setModalStatus(validationMessage);
        return;
      }
      const nextEntry = buildWorkEmbeddedEntry(kind, firstValue, secondValue);
      const nextEntries = descriptor.entries.slice();
      if (descriptor.editing) {
        nextEntries[index] = nextEntry;
      } else {
        nextEntries.push(nextEntry);
      }
      closeCatalogueWorkModal(state);
      resolve({
        confirmed: true,
        entriesKey: descriptor.entriesKey,
        entries: nextEntries,
        entry: nextEntry,
        editing: descriptor.editing,
        index: descriptor.editing ? index : null
      });
    };

    state.activeModalKeydown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
      if (event.key === "Enter" && event.target && event.target.tagName === "INPUT") {
        event.preventDefault();
        submit();
      }
    };
    document.addEventListener("keydown", state.activeModalKeydown);
    cancelNodes.forEach((button) => button.addEventListener("click", cancel));
    if (saveNode) saveNode.addEventListener("click", submit);
    if (firstNode) firstNode.focus();
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
    cancelLabel: lookupText(text, "entry_modal_cancel_button", "Cancel")
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

export function openWorkBuildPreviewModal(state, response, changedFields, options = {}) {
  if (!state || !state.modalHost) return;
  const text = options.text;
  closeCatalogueWorkModal(state);
  state.modalHost.innerHTML = renderStudioModalFrame({
    hidden: false,
    title: lookupText(text, "build_preview_modal_title", "Public update preview"),
    titleId: "catalogueWorkBuildPreviewModalTitle",
    modalRole: "build-preview-modal",
    backdropRole: BUILD_PREVIEW_CLOSE_ROLE,
    bodyHtml: formatCatalogueBuildPreviewModalHtml(response, changedFields, {
      text,
      defaultTemplate: "Public update preview: work {work_ids}; series {series_ids}; catalogue search {search_rebuild}.",
      reasonsClass: "catalogueWorkBuildPreview__reasons"
    }),
    actions: [
      { role: BUILD_PREVIEW_CLOSE_ROLE, label: lookupText(text, "build_preview_modal_close", "Close") }
    ]
  });

  const closeNodes = state.modalHost.querySelectorAll(`[data-role="${BUILD_PREVIEW_CLOSE_ROLE}"]`);
  state.activeModalKeydown = (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeCatalogueWorkModal(state);
    }
  };
  document.addEventListener("keydown", state.activeModalKeydown);
  closeNodes.forEach((button) => button.addEventListener("click", () => closeCatalogueWorkModal(state)));
  const closeButton = state.modalHost.querySelector(`[data-role="${BUILD_PREVIEW_CLOSE_ROLE}"]`);
  if (closeButton) closeButton.focus();
}

export function renderWorkEmbeddedEntryModalHtml(descriptor, options = {}) {
  const text = options.text;
  const firstField = descriptor.fields[0];
  const secondField = descriptor.fields[1];
  return renderStudioModalFrame({
    hidden: false,
    title: descriptor.title,
    titleId: descriptor.titleId,
    modalRole: descriptor.modalRole,
    backdropRole: ENTRY_CANCEL_ROLE,
    bodyHtml: `
      <div class="tagStudioForm__fields">
        ${modalFieldHtml(firstField)}
        ${modalFieldHtml(secondField)}
      </div>
      <p class="tagStudioForm__status" id="${escapeHtml(descriptor.statusId)}"></p>
    `,
    actions: [
      { role: ENTRY_SAVE_ROLE, label: lookupText(text, "entry_modal_save_button", "Save") },
      { role: ENTRY_CANCEL_ROLE, label: lookupText(text, "entry_modal_cancel_button", "Cancel") }
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
