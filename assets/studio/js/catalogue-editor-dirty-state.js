import { buildChangedFieldNames } from "./catalogue-editor-records.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function hasSetItems(value) {
  return Boolean(value && typeof value.size === "number" && value.size > 0);
}

export function catalogueDraftChangedFieldNames(options = {}) {
  if (!options.baselineDraft) return [];
  return buildChangedFieldNames(options);
}

export function catalogueDraftFieldsChanged(options = {}) {
  return catalogueDraftChangedFieldNames(options).length > 0;
}

export function catalogueDraftHasChanges(options = {}) {
  const mode = normalizeText(options.mode);
  if (mode === "new") {
    return typeof options.newModeChanged === "function" ? Boolean(options.newModeChanged()) : true;
  }
  if (mode === "bulk") {
    return typeof options.bulkModeChanged === "function"
      ? Boolean(options.bulkModeChanged())
      : hasSetItems(options.touchedFields);
  }
  return catalogueDraftFieldsChanged(options);
}

export function catalogueDirtyWarningText(options = {}) {
  return options.dirty && normalizeText(options.mode) !== "new"
    ? normalizeText(options.message)
    : "";
}

export function catalogueSaveDisabled(options = {}) {
  return !options.hasRecord
    || Boolean(options.isSaving)
    || Boolean(options.hasErrors)
    || !options.dirty
    || !options.serverAvailable;
}

export function catalogueDeleteDisabled(options = {}) {
  return !options.hasRecord
    || normalizeText(options.mode) === "bulk"
    || Boolean(options.isSaving)
    || Boolean(options.isBuilding)
    || Boolean(options.isDeleting)
    || !options.serverAvailable;
}
