import {
  committedDocumentLocation,
  createDocumentLocationProvider,
  normalizeDocumentLocationScopeIds
} from "/shared/frontend/js/document-location-provider.js";
import {
  bindSearchList
} from "/shared/frontend/js/search-list.js";


function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function scopeLabel(scopeId) {
  const value = normalizeText(scopeId);
  return value ? `${value.slice(0, 1).toUpperCase()}${value.slice(1)}` : "";
}

function currentExcludedUrls(value) {
  const urls = typeof value === "function" ? value() : value;
  return Array.isArray(urls) ? urls : [];
}

export function documentLocationOptionHtml(record, { showScope = false } = {}) {
  const context = [
    normalizeText(record && record.report_title),
    showScope ? scopeLabel(record && record.scope_id) : ""
  ].filter(Boolean);
  return `
    <span class="sharedDocumentLocationPicker__title">${escapeHtml(record && record.document_title)}</span>
    ${context.length ? `<span class="sharedDocumentLocationPicker__context">${escapeHtml(context.join(" • "))}</span>` : ""}
  `;
}

/**
 * Bind one app-neutral document-location search field.
 *
 * The consumer owns supported-scope policy, exclusions, durable draft state,
 * modal lifecycle, and all writes. A commit returns one exact location record.
 */
export function bindDocumentLocationPicker(inputNode, popupNode, options = {}) {
  const scopeIds = normalizeDocumentLocationScopeIds(options.scopeIds);
  const provider = options.provider || createDocumentLocationProvider();
  if (!provider || typeof provider.search !== "function") {
    throw new Error("document location picker requires a provider");
  }
  const showScope = scopeIds.length > 1;
  const controller = bindSearchList(inputNode, popupNode, {
    id: options.id,
    maxOptions: Number.isFinite(options.maxOptions) ? options.maxOptions : 20,
    openOnFocus: options.openOnFocus !== false,
    getOptionValue: (record) => normalizeText(record && record.document_title),
    filterOptions: (records) => records,
    loadOptions: (query) => provider.search({
      scopeIds,
      query,
      excludedUrls: currentExcludedUrls(options.excludedUrls)
    }),
    renderOption: (record) => documentLocationOptionHtml(record, { showScope }),
    renderNoResults: () => (
      `<p class="sharedSearchList__empty">${escapeHtml(options.noResultsText || "No matching documents.")}</p>`
    ),
    renderError: (error) => (
      `<p class="sharedSearchList__empty">${escapeHtml(
        normalizeText(error && error.message) || options.errorText || "Documents could not be loaded."
      )}</p>`
    ),
    onTransientInput: options.onTransientInput,
    onCancel: options.onCancel,
    onCommitError: options.onCommitError,
    onCommit: async (record) => {
      if (typeof options.onCommit === "function") {
        await options.onCommit(committedDocumentLocation(record));
      }
    }
  });
  popupNode.classList.add("sharedDocumentLocationPicker__popup");
  return controller;
}
