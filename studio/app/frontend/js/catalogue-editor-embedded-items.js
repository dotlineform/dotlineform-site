import {
  cloneEmbeddedEntries,
  normalizeEmbeddedEntries,
  normalizeText
} from "./catalogue-work-fields.js";

const EMBEDDED_ITEM_DEFINITIONS = Object.freeze({
  download: Object.freeze({
    entriesKey: "downloads",
    fields: Object.freeze(["filename", "label"]),
    firstKey: "filename",
    secondKey: "label",
    titleId: "catalogueWorkDownloadModalTitle",
    statusId: "catalogueWorkDownloadModalStatus",
    modalRole: "download-modal",
    firstFieldId: "catalogueWorkDownloadFilename",
    secondFieldId: "catalogueWorkDownloadLabel",
    firstFieldType: "text",
    addTitleKey: "files_add_modal_title",
    addTitleFallback: "Add download",
    editTitleKey: "files_edit_modal_title",
    editTitleFallback: "Edit download",
    firstLabelKey: "files_filename_label",
    firstLabelFallback: "filename",
    secondLabelKey: "files_label_label",
    secondLabelFallback: "label",
    missingFirstKey: "files_invalid_filename",
    missingFirstFallback: "Each download needs a filename.",
    missingSecondKey: "files_invalid_label",
    missingSecondFallback: "Each download needs a label.",
    deleteTitleKey: "files_delete_modal_title",
    deleteTitleFallback: "Delete download",
    deleteBodyKey: "files_delete_modal_body",
    deleteBodyFallback: "Delete download {label}?"
  }),
  link: Object.freeze({
    entriesKey: "links",
    fields: Object.freeze(["url", "label"]),
    firstKey: "url",
    secondKey: "label",
    titleId: "catalogueWorkLinkModalTitle",
    statusId: "catalogueWorkLinkModalStatus",
    modalRole: "link-modal",
    firstFieldId: "catalogueWorkLinkUrl",
    secondFieldId: "catalogueWorkLinkLabel",
    firstFieldType: "url",
    addTitleKey: "links_add_modal_title",
    addTitleFallback: "Add link",
    editTitleKey: "links_edit_modal_title",
    editTitleFallback: "Edit link",
    firstLabelKey: "links_url_label",
    firstLabelFallback: "URL",
    secondLabelKey: "links_label_label",
    secondLabelFallback: "label",
    missingFirstKey: "links_invalid_url",
    missingFirstFallback: "Each link needs a URL.",
    missingSecondKey: "links_invalid_label",
    missingSecondFallback: "Each link needs a label.",
    deleteTitleKey: "links_delete_modal_title",
    deleteTitleFallback: "Delete link",
    deleteBodyKey: "links_delete_modal_body",
    deleteBodyFallback: "Delete link {label}?"
  })
});

export const WORK_DOWNLOAD_FIELDS = EMBEDDED_ITEM_DEFINITIONS.download.fields;
export const WORK_LINK_FIELDS = EMBEDDED_ITEM_DEFINITIONS.link.fields;

function definitionForKind(kind) {
  return EMBEDDED_ITEM_DEFINITIONS[normalizeText(kind)] || null;
}

function interpolateText(template, tokens = null) {
  let text = normalizeText(template);
  if (!tokens || typeof tokens !== "object") return text;
  Object.entries(tokens).forEach(([key, value]) => {
    text = text.replaceAll(`{${key}}`, String(value == null ? "" : value));
  });
  return text;
}

function lookupText(text, key, fallback, tokens = null) {
  return typeof text === "function" ? text(key, fallback, tokens) : interpolateText(fallback, tokens);
}

export function getWorkEmbeddedItems(draft, kind) {
  const definition = definitionForKind(kind);
  if (!definition) return [];
  return cloneEmbeddedEntries(draft && draft[definition.entriesKey], definition.fields);
}

export function buildWorkEmbeddedModalDescriptor(kind, index, options = {}) {
  const definition = definitionForKind(kind);
  if (!definition) return null;
  const text = options.text;
  const entries = getWorkEmbeddedItems(options.draft, kind);
  const editing = Number.isInteger(index) && index >= 0 && index < entries.length;
  const current = editing ? entries[index] : {};
  return {
    entriesKey: definition.entriesKey,
    entries,
    editing,
    title: editing
      ? lookupText(text, definition.editTitleKey, definition.editTitleFallback)
      : lookupText(text, definition.addTitleKey, definition.addTitleFallback),
    titleId: definition.titleId,
    modalRole: definition.modalRole,
    statusId: definition.statusId,
    fields: [
      {
        fieldId: definition.firstFieldId,
        label: lookupText(text, definition.firstLabelKey, definition.firstLabelFallback),
        key: definition.firstKey,
        value: current[definition.firstKey] || "",
        type: definition.firstFieldType
      },
      {
        fieldId: definition.secondFieldId,
        label: lookupText(text, definition.secondLabelKey, definition.secondLabelFallback),
        key: definition.secondKey,
        value: current[definition.secondKey] || "",
        type: "text"
      }
    ]
  };
}

export function validateWorkEmbeddedEntryValues(kind, firstValue, secondValue, options = {}) {
  const definition = definitionForKind(kind);
  if (!definition) return "";
  const text = options.text;
  if (!normalizeText(firstValue)) {
    return lookupText(text, definition.missingFirstKey, definition.missingFirstFallback);
  }
  if (!normalizeText(secondValue)) {
    return lookupText(text, definition.missingSecondKey, definition.missingSecondFallback);
  }
  return "";
}

export function buildWorkEmbeddedEntry(kind, firstValue, secondValue) {
  const definition = definitionForKind(kind);
  if (!definition) return {};
  return {
    [definition.firstKey]: normalizeText(firstValue),
    [definition.secondKey]: normalizeText(secondValue)
  };
}

export function buildWorkEmbeddedDeleteConfirmation(kind, draft, index, options = {}) {
  const definition = definitionForKind(kind);
  if (!definition) return null;
  const entries = getWorkEmbeddedItems(draft, kind);
  if (!Number.isInteger(index) || index < 0 || index >= entries.length) return null;
  const item = entries[index];
  const text = options.text;
  const label = definition.entriesKey === "downloads"
    ? normalizeText(item.label || item.filename)
    : normalizeText(item.label || item.url);
  return {
    entriesKey: definition.entriesKey,
    entries,
    title: lookupText(text, definition.deleteTitleKey, definition.deleteTitleFallback),
    body: lookupText(text, definition.deleteBodyKey, definition.deleteBodyFallback, { label })
  };
}

export function validateWorkEmbeddedItems(draft, options = {}) {
  const errors = new Map();
  const text = options.text;
  normalizeEmbeddedEntries(draft && draft.downloads, WORK_DOWNLOAD_FIELDS).forEach((item) => {
    const message = validateWorkEmbeddedEntryValues("download", item.filename, item.label, { text });
    if (message) errors.set("downloads", message);
  });
  normalizeEmbeddedEntries(draft && draft.links, WORK_LINK_FIELDS).forEach((item) => {
    const message = validateWorkEmbeddedEntryValues("link", item.url, item.label, { text });
    if (message) errors.set("links", message);
  });
  return errors;
}
