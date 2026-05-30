import { getAnalyticsText } from "./analytics-config.js";
import {
  defaultFormatForPrepareConfig,
  prepareConfigSelection,
  selectedPrepareConfig,
  supportedFormatsForPrepareConfig,
  usesPrepareDocumentSelection
} from "./data-sharing-prepare-workflow.js";

const LIST_FILTERS = [
  { key: "all", labelKey: "filter_show_all", fallback: "show all [{count}]" },
  { key: "no_content", labelKey: "filter_no_content", fallback: "no content [{count}]" },
  { key: "not_viewable", labelKey: "filter_not_viewable", fallback: "not viewable [{count}]" }
];
const FORMAT_OPTIONS = [
  { key: "json", labelKey: "format_json", fallback: "JSON" },
  { key: "jsonl", labelKey: "format_jsonl", fallback: "JSONL" }
];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function scopeLabel(state, scope = state.scope) {
  const item = (state.workflowScopes || []).find((candidate) => candidate.key === scope);
  if (item && item.labelKey) return getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item && item.label) || normalizeText(item && item.fallback) || scope;
}

function scopeTitle(state, scope = state.scope) {
  const label = scopeLabel(state, scope);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : scope;
}

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function descendantIds(state, docId) {
  const ids = [];
  const collect = (parentId) => {
    const children = state.childrenByParent.get(parentId) || [];
    children.forEach((child) => {
      const childId = normalizeText(child.doc_id);
      if (!childId) return;
      ids.push(childId);
      collect(childId);
    });
  };
  collect(docId);
  return ids;
}

function contentTextLength(doc) {
  const value = Number(doc && doc.content_text_length);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function docHasNoContent(doc) {
  return contentTextLength(doc) === 0;
}

function docMatchesListFilter(state, doc) {
  if (!doc) return false;
  if (state.listFilter === "no_content") return docHasNoContent(doc);
  if (state.listFilter === "not_viewable") return doc.published !== false && doc.viewable === false;
  return true;
}

function docMatchesConfigFilter(state, docId) {
  const missingOnly = state.missingSummaryOnly.checked && state.missingSummaryOnlyWrap.hidden === false;
  const doc = state.docsById.get(docId);
  if (!doc) return false;
  return !missingOnly || !normalizeText(doc.summary);
}

function rowMatchesCurrentFilters(state, docId) {
  const doc = state.docsById.get(docId);
  return Boolean(doc && docMatchesConfigFilter(state, docId) && docMatchesListFilter(state, doc));
}

function listFilterCounts(state) {
  const docs = state.docs.filter((doc) => docMatchesConfigFilter(state, normalizeText(doc.doc_id)));
  return {
    all: docs.length,
    no_content: docs.filter((doc) => docHasNoContent(doc)).length,
    not_viewable: docs.filter((doc) => doc.published !== false && doc.viewable === false).length
  };
}

function renderDocRow(state, doc) {
  const docId = normalizeText(doc.doc_id);
  const title = normalizeText(doc.title) || docId;
  const depth = Math.max(0, Number(state.depthById.get(docId) || 0));
  const viewable = doc.viewable === true;
  const noContent = docHasNoContent(doc);
  return `
    <li class="analyticsList__row analyticsList__row--center dataSharingPrepareList__row" data-data-sharing-prepare-doc="${escapeHtml(docId)}" data-data-sharing-prepare-viewable="${viewable ? "true" : "false"}" data-data-sharing-prepare-no-content="${noContent ? "true" : "false"}" style="--data-sharing-prepare-depth: ${depth};">
      <label class="dataSharingPrepareList__label">
        <input class="dataSharingPrepareList__checkbox" type="checkbox" value="${escapeHtml(docId)}">
        <span class="dataSharingPrepareList__viewable${viewable ? " is-viewable" : ""}" aria-label="${viewable ? "viewable" : ""}"></span>
        <span class="dataSharingPrepareList__title">${escapeHtml(title)}</span>
      </label>
    </li>
  `;
}

export function dataSharingPrepareListFilters() {
  return LIST_FILTERS.map((filter) => filter.key);
}

export function selectedDataSharingPrepareConfig(state) {
  return selectedPrepareConfig(state.exportConfigs, state.configSelect.value);
}

export function supportedUiFormatsForDataSharingPrepareConfig(config) {
  return supportedFormatsForPrepareConfig(config)
    .filter((format) => FORMAT_OPTIONS.some((item) => item.key === format));
}

export function defaultUiFormatForDataSharingPrepareConfig(config) {
  return defaultFormatForPrepareConfig(config, FORMAT_OPTIONS.map((item) => item.key));
}

export function selectableDataSharingPrepareDocIds(state, { visibleOnly = false } = {}) {
  return state.docs
    .filter((doc) => {
      const docId = normalizeText(doc.doc_id);
      if (!docMatchesConfigFilter(state, docId)) return false;
      return !visibleOnly || docMatchesListFilter(state, doc);
    })
    .map((doc) => normalizeText(doc.doc_id))
    .filter(Boolean);
}

export function syncDataSharingPrepareCheckboxes(state) {
  const visibleSelected = new Set(
    selectableDataSharingPrepareDocIds(state, { visibleOnly: true }).filter((docId) => state.selectedIds.has(docId))
  );
  state.listNode.querySelectorAll("[data-data-sharing-prepare-doc]").forEach((row) => {
    const docId = normalizeText(row.getAttribute("data-data-sharing-prepare-doc"));
    const checkbox = row.querySelector("input[type='checkbox']");
    if (!(checkbox instanceof HTMLInputElement)) return;
    const subtreeIds = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesCurrentFilters(state, id));
    const selectedCount = subtreeIds.filter((id) => visibleSelected.has(id)).length;
    checkbox.checked = subtreeIds.length > 0 && selectedCount === subtreeIds.length;
    checkbox.indeterminate = selectedCount > 0 && selectedCount < subtreeIds.length;
  });
}

export function applyDataSharingPrepareSelectionFilter(state) {
  if (!usesPrepareDocumentSelection(state.prepareCapability)) {
    state.selectedIds.clear();
    return;
  }
  const allowedIds = new Set(selectableDataSharingPrepareDocIds(state));
  state.selectedIds.forEach((docId) => {
    if (!allowedIds.has(docId)) state.selectedIds.delete(docId);
  });
}

export function updateDataSharingPrepareSelectionSummary(state) {
  if (!usesPrepareDocumentSelection(state.prepareCapability)) {
    setText(
      state.selectionSummary,
      getAnalyticsText(
        state.config,
        "data_sharing_prepare.selection_not_required",
        "No record selection required."
      )
    );
    return;
  }
  const count = state.selectedIds.size;
  setText(
    state.selectionSummary,
    getAnalyticsText(
      state.config,
      count === 1
        ? "data_sharing_prepare.selection_summary_one"
        : "data_sharing_prepare.selection_summary",
      count === 1 ? "1 document selected." : "{count} documents selected.",
      { count }
    )
  );
}

export function renderDataSharingPrepareListFilters(state) {
  const actions = state.filterNode.closest(".dataSharingPreparePage__listActions");
  if (!usesPrepareDocumentSelection(state.prepareCapability)) {
    if (actions) actions.hidden = true;
    state.filterNode.innerHTML = "";
    return;
  }
  if (actions) actions.hidden = false;
  const counts = listFilterCounts(state);
  state.filterNode.innerHTML = LIST_FILTERS.map((filter) => {
    const count = Number(counts[filter.key] || 0);
    const active = state.listFilter === filter.key;
    const label = getAnalyticsText(state.config, `data_sharing_prepare.${filter.labelKey}`, filter.fallback, { count });
    return `
      <button type="button" class="analytics__keyPill analyticsFilters__groupBtn" data-data-sharing-prepare-filter="${escapeHtml(filter.key)}" data-state="${active ? "active" : ""}" aria-pressed="${active ? "true" : "false"}">
        ${escapeHtml(label)}
      </button>
    `;
  }).join("");
}

export function renderDataSharingPrepareFormatOptions(state) {
  const config = selectedDataSharingPrepareConfig(state);
  const supportedFormats = supportedUiFormatsForDataSharingPrepareConfig(config);
  if (!config) {
    state.formatOptionsNode.innerHTML = "";
    state.targetFormat = "";
    return;
  }
  if (!supportedFormats.includes(state.targetFormat)) {
    state.targetFormat = defaultUiFormatForDataSharingPrepareConfig(config);
  }
  state.formatOptionsNode.innerHTML = FORMAT_OPTIONS.map((format) => {
    const supported = supportedFormats.includes(format.key);
    const checked = state.targetFormat === format.key;
    const label = getAnalyticsText(state.config, `data_sharing_prepare.${format.labelKey}`, format.fallback);
    return `
      <label class="dataSharingPreparePage__formatOption">
        <input type="radio" name="dataSharingPrepareFormat" value="${escapeHtml(format.key)}"${checked ? " checked" : ""}${supported ? "" : " disabled"}>
        <span class="analytics__keyPill analyticsFilters__groupBtn" data-state="${checked ? "active" : ""}" aria-disabled="${supported ? "false" : "true"}">${escapeHtml(label)}</span>
      </label>
    `;
  }).join("");
}

export function syncDataSharingPrepareConfigOptions(state) {
  const config = selectedDataSharingPrepareConfig(state);
  const selection = prepareConfigSelection(config);
  const supportsMissing = Boolean(selection.supports_missing_summary_only);
  state.missingSummaryOnlyWrap.hidden = !usesPrepareDocumentSelection(state.prepareCapability) || !supportsMissing;
  state.missingSummaryOnly.checked = supportsMissing && Boolean(selection.default_missing_summary_only);
  state.targetFormat = defaultUiFormatForDataSharingPrepareConfig(config);
  renderDataSharingPrepareFormatOptions(state);
  applyDataSharingPrepareSelectionFilter(state);
  renderDataSharingPrepareListFilters(state);
  renderDataSharingPrepareDocList(state);
}

export function renderDataSharingPrepareConfigSelect(state) {
  state.configSelect.innerHTML = state.exportConfigs.map((config) => {
    const id = normalizeText(config.id);
    const label = normalizeText(config.label) || id;
    return `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`;
  }).join("");
}

export function renderDataSharingPrepareDocList(state) {
  if (!usesPrepareDocumentSelection(state.prepareCapability)) {
    state.listNode.innerHTML = `<p class="analytics__status">${escapeHtml(getAnalyticsText(
      state.config,
      "data_sharing_prepare.profile_only_empty_state",
      "This profile packages the selected data family."
    ))}</p>`;
    updateDataSharingPrepareSelectionSummary(state);
    return;
  }
  const visibleDocIds = new Set(selectableDataSharingPrepareDocIds(state, { visibleOnly: true }));
  const rows = state.docs
    .filter((doc) => visibleDocIds.has(normalizeText(doc.doc_id)))
    .map((doc) => renderDocRow(state, doc));
  state.listNode.innerHTML = rows.length
    ? `<ul class="analyticsList__rows dataSharingPrepareList__rows">${rows.join("")}</ul>`
    : `<p class="analytics__status">${escapeHtml(getAnalyticsText(
      state.config,
      "data_sharing_prepare.empty_state",
      "No matching {scope_label} documents.",
      { scope_label: scopeTitle(state) }
    ))}</p>`;
  syncDataSharingPrepareCheckboxes(state);
  updateDataSharingPrepareSelectionSummary(state);
}

export function updateDataSharingPrepareSelectionFromChange(state, event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return false;
  const row = target.closest("[data-data-sharing-prepare-doc]");
  const docId = normalizeText(row ? row.getAttribute("data-data-sharing-prepare-doc") : "");
  if (!docId) return false;
  const ids = [docId, ...descendantIds(state, docId)].filter((id) => rowMatchesCurrentFilters(state, id));
  ids.forEach((id) => {
    if (target.checked) {
      state.selectedIds.add(id);
    } else {
      state.selectedIds.delete(id);
    }
  });
  return true;
}

export function renderDataSharingPrepareResultBody(state, payload) {
  const files = outputFiles(payload);
  const fileText = files.join("\n");
  const fileLabel = getAnalyticsText(state.config, "data_sharing_prepare.result_files_label", "files created");
  const emptyFiles = getAnalyticsText(state.config, "data_sharing_prepare.result_files_empty", "No files created.");
  const formatLabel = getAnalyticsText(state.config, "data_sharing_prepare.result_format_label", "format");
  const targetFormat = normalizeText(payload && payload.target_format).toUpperCase();
  return `
    <dl class="dataSharingPrepareModal__details">
      <div class="dataSharingPrepareModal__countRow" data-detail-key="format">
        <dt>${escapeHtml(formatLabel)}</dt>
        <dd>${escapeHtml(targetFormat || "n/a")}</dd>
      </div>
    </dl>
    <dl class="dataSharingPrepareModal__counts">
      ${countRows(state, payload && payload.counts, payload)}
    </dl>
    <label class="dataSharingPrepareModal__files">
      <span>${escapeHtml(fileLabel)}</span>
      <textarea class="analytics__input dataSharingPrepareModal__fileList" readonly rows="${Math.max(1, files.length)}">${escapeHtml(fileText || emptyFiles)}</textarea>
    </label>
    ${issueList(state, payload && payload.warnings, payload && payload.errors)}
  `;
}

function countRows(state, counts, payload) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const unit = normalizeText(payload && payload.count_unit) || "document";
  const rows = [
    ["selected", "data_sharing_prepare.count_selected", "selected", Number(safeCounts.selected || 0)],
    ["exported", "data_sharing_prepare.count_exported", "packaged", Number(safeCounts.exported || 0)],
    ["skipped", "data_sharing_prepare.count_skipped", "skipped", Number(safeCounts.skipped || 0)],
    ["failed", "data_sharing_prepare.count_failed", "failed", Number(safeCounts.failed || 0)],
    ["truncated", "data_sharing_prepare.count_truncated", "truncated", Number(safeCounts.truncated || 0)]
  ];
  return rows.map(([key, textKey, fallback, count]) => `
    <div class="dataSharingPrepareModal__countRow" data-count-key="${escapeHtml(key)}">
      <dt>${escapeHtml(getAnalyticsText(state.config, textKey, fallback))}</dt>
      <dd>${escapeHtml(countLabel(count, unit))}</dd>
    </div>
  `).join("");
}

function issueList(state, warnings, errors) {
  const errorItems = Array.isArray(errors) ? errors.map(normalizeText).filter(Boolean) : [];
  const warningItems = Array.isArray(warnings) ? warnings.map(normalizeText).filter(Boolean) : [];
  const items = [...errorItems, ...warningItems];
  if (!items.length) return "";
  const heading = getAnalyticsText(
    state.config,
    errorItems.length ? "data_sharing_prepare.issues_heading" : "data_sharing_prepare.warnings_heading",
    errorItems.length ? "Issues" : "Warnings"
  );
  return `
    <div class="dataSharingPrepareModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function outputFiles(payload) {
  const files = [];
  const outputFiles = Array.isArray(payload && payload.output_files) ? payload.output_files : [];
  outputFiles.forEach((file) => {
    const filename = basename(file);
    if (filename) files.push(filename);
  });
  const outputFile = basename(payload && payload.output_file);
  if (outputFile && !files.includes(outputFile)) files.push(outputFile);
  return files;
}

function basename(path) {
  const value = normalizeText(path);
  if (!value) return "";
  const parts = value.split(/[\\/]+/).filter(Boolean);
  return parts[parts.length - 1] || value;
}

function countLabel(count, unit = "document") {
  const safeCount = Number(count || 0);
  const normalizedUnit = normalizeText(unit) || "document";
  if (normalizedUnit === "record") return safeCount === 1 ? "1 record" : `${safeCount} records`;
  if (normalizedUnit === "file") return safeCount === 1 ? "1 file" : `${safeCount} files`;
  return safeCount === 1 ? "1 document" : `${safeCount} documents`;
}
