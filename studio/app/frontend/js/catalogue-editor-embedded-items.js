import {
  cloneEmbeddedEntries,
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
    firstFieldType: "text"
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
    firstFieldType: "url"
  })
});

export const WORK_DOWNLOAD_FIELDS = EMBEDDED_ITEM_DEFINITIONS.download.fields;
export const WORK_LINK_FIELDS = EMBEDDED_ITEM_DEFINITIONS.link.fields;

function definitionForKind(kind) {
  return EMBEDDED_ITEM_DEFINITIONS[normalizeText(kind)] || null;
}

export function getWorkEmbeddedItems(draft, kind) {
  const definition = definitionForKind(kind);
  if (!definition) return [];
  return cloneEmbeddedEntries(draft?.[definition.entriesKey], definition.fields);
}

export function buildWorkEmbeddedModalDescriptor(kind, index, draft) {
  const definition = definitionForKind(kind);
  if (!definition) return null;
  const entries = getWorkEmbeddedItems(draft, kind);
  const editing = Number.isInteger(index) && index >= 0 && index < entries.length;
  if (kind === "download" && !editing) return null;
  const current = editing ? entries[index] : {};
  return {
    entriesKey: definition.entriesKey,
    entries,
    editing,
    title: kind === "download" ? "Edit download" : editing ? "Edit link" : "Add link",
    titleId: definition.titleId,
    modalRole: definition.modalRole,
    statusId: definition.statusId,
    fields: [
      {
        fieldId: definition.firstFieldId,
        label: kind === "download" ? "filename" : "URL",
        key: definition.firstKey,
        value: editing ? current[definition.firstKey] : "",
        type: definition.firstFieldType,
        readOnly: kind === "download"
      },
      {
        fieldId: definition.secondFieldId,
        label: "label",
        key: definition.secondKey,
        value: editing ? current[definition.secondKey] : "",
        type: "text"
      }
    ]
  };
}

export function validateWorkEmbeddedEntryValues(kind, firstValue, secondValue) {
  const definition = definitionForKind(kind);
  if (!definition) return "";
  if (!normalizeText(firstValue)) {
    return kind === "download" ? "Each download needs a filename." : "Each link needs a URL.";
  }
  if (!normalizeText(secondValue)) {
    return kind === "download" ? "Each download needs a label." : "Each link needs a label.";
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

export function buildWorkEmbeddedDeleteConfirmation(kind, draft, index) {
  const definition = definitionForKind(kind);
  if (!definition) return null;
  const entries = getWorkEmbeddedItems(draft, kind);
  if (!Number.isInteger(index) || index < 0 || index >= entries.length) return null;
  const item = entries[index];
  const label = item.label;
  return {
    entriesKey: definition.entriesKey,
    entries,
    title: kind === "download" ? "Delete download" : "Delete link",
    body: kind === "download" ? `Delete download ${label}?` : `Delete link ${label}?`
  };
}

export function validateWorkEmbeddedItems(draft) {
  const errors = new Map();
  cloneEmbeddedEntries(draft?.downloads, WORK_DOWNLOAD_FIELDS).forEach((item) => {
    const message = validateWorkEmbeddedEntryValues("download", item.filename, item.label);
    if (message) errors.set("downloads", message);
  });
  cloneEmbeddedEntries(draft?.links, WORK_LINK_FIELDS).forEach((item) => {
    const message = validateWorkEmbeddedEntryValues("link", item.url, item.label);
    if (message) errors.set("links", message);
  });
  return errors;
}
