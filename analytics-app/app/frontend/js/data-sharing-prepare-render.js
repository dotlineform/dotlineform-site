import { getAnalyticsText } from "./analytics-config.js";
import {
  createSelectableList
} from "/shared/frontend/js/selectable-list.js";
import {
  defaultFormatForPrepareConfig,
  prepareConfigSelection,
  selectedPrepareConfig,
  supportedFormatsForPrepareConfig,
  usesPrepareDocumentSelection,
  usesPrepareRecordSelection
} from "./data-sharing-prepare-workflow.js";

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

function dataDomainLabel(state, dataDomain = state.dataDomain) {
  const item = (state.dataDomains || []).find((candidate) => candidate.key === dataDomain);
  if (item && item.labelKey) return getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item && item.label) || normalizeText(item && item.fallback) || dataDomain;
}

function dataDomainTitle(state, dataDomain = state.dataDomain) {
  const label = dataDomainLabel(state, dataDomain);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : dataDomain;
}

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function docMatchesConfigFilter(state, docId) {
  const missingOnly = state.missingSummaryOnly.checked && state.missingSummaryOnlyWrap.hidden === false;
  const doc = state.docsById.get(docId);
  if (!doc) return false;
  return !missingOnly || !normalizeText(doc.summary);
}

function prepareListRecordId(record) {
  return normalizeText(record && record.id);
}

function prepareListRecordName(record) {
  return normalizeText(record && record.name);
}

export function selectedDataSharingPrepareConfig(state) {
  return selectedPrepareConfig(state.exportConfigs, state.configSelect.value);
}

function stateUsesPrepareRecordSelection(state) {
  return usesPrepareRecordSelection(state.prepareCapability, selectedDataSharingPrepareConfig(state));
}

export function supportedUiFormatsForDataSharingPrepareConfig(config) {
  return supportedFormatsForPrepareConfig(config)
    .filter((format) => FORMAT_OPTIONS.some((item) => item.key === format));
}

export function defaultUiFormatForDataSharingPrepareConfig(config) {
  return defaultFormatForPrepareConfig(config, FORMAT_OPTIONS.map((item) => item.key));
}

export function selectableDataSharingPrepareDocIds(state) {
  return selectableDataSharingPrepareDocs(state)
    .map((doc) => prepareListRecordId(doc))
    .filter(Boolean);
}

function selectableDataSharingPrepareDocs(state) {
  return state.docs.filter((doc) => docMatchesConfigFilter(state, prepareListRecordId(doc)));
}

export function currentDataSharingPrepareSelectedIds(state) {
  const selectableIds = new Set(selectableDataSharingPrepareDocIds(state));
  return Array.from(state.selectedIds || [])
    .filter((docId) => selectableIds.has(docId))
    .sort((left, right) => {
      if (left === right) return 0;
      return left < right ? -1 : 1;
    });
}

export function syncDataSharingPrepareCheckboxes(state) {
  if (!state.selectableList) return;
  state.selectableList.update({
    selectedIds: currentDataSharingPrepareSelectedIds(state),
    cascadeSelection: state.includeDescendants
  });
}

export function applyDataSharingPrepareSelectionFilter(state) {
  if (!stateUsesPrepareRecordSelection(state)) {
    state.selectedIds.clear();
    return;
  }
  const allowedIds = new Set(selectableDataSharingPrepareDocIds(state));
  state.selectedIds.forEach((docId) => {
    if (!allowedIds.has(docId)) state.selectedIds.delete(docId);
  });
}

export function updateDataSharingPrepareSelectionSummary(state) {
  if (!stateUsesPrepareRecordSelection(state)) {
    setText(state.selectionSummary, "");
    return;
  }
  const count = currentDataSharingPrepareSelectedIds(state).length;
  setText(
    state.selectionSummary,
    getAnalyticsText(
      state.config,
      count === 1
        ? "data_sharing_prepare.selection_summary_one"
        : "data_sharing_prepare.selection_summary",
      count === 1 ? "1 record selected." : "{count} records selected.",
      { count }
    )
  );
}

export function syncDataSharingPrepareListActions(state) {
  const actions = state.filterNode.closest(".dataSharingPreparePage__listActions");
  state.filterNode.innerHTML = "";
  if (actions) actions.hidden = false;
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
    state.targetFormat = supportedFormats.includes("json") ? "json" : defaultUiFormatForDataSharingPrepareConfig(config);
  }
  state.formatOptionsNode.innerHTML = FORMAT_OPTIONS.filter((format) => supportedFormats.includes(format.key)).map((format) => {
    const supported = supportedFormats.includes(format.key);
    const selected = state.targetFormat === format.key;
    const label = getAnalyticsText(state.config, `data_sharing_prepare.${format.labelKey}`, format.fallback);
    return `<option value="${escapeHtml(format.key)}"${selected ? " selected" : ""}${supported ? "" : " disabled"}>${escapeHtml(label)}</option>`;
  }).join("");
  state.formatOptionsNode.value = state.targetFormat;
}

export function syncDataSharingPrepareConfigOptions(state, options = {}) {
  const {
    preserveOptions = false,
    preserveSelection = false
  } = options;
  const config = selectedDataSharingPrepareConfig(state);
  const selection = prepareConfigSelection(config);
  const supportsMissing = Boolean(selection.supports_missing_summary_only);
  const supportsDescendantCascade = usesPrepareDocumentSelection(state.prepareCapability)
    && normalizeText(selection.mode) === "explicit_doc_ids";
  state.missingSummaryOnlyWrap.hidden = !usesPrepareDocumentSelection(state.prepareCapability) || !supportsMissing;
  if (!preserveOptions) state.missingSummaryOnly.checked = false;
  state.includeDescendantsWrap.hidden = !supportsDescendantCascade;
  if (preserveOptions) {
    state.includeDescendants = state.includeDescendantsInput.checked;
  } else {
    state.includeDescendants = supportsDescendantCascade && selection.include_descendants !== false;
    state.includeDescendantsInput.checked = state.includeDescendants;
    state.targetFormat = supportedUiFormatsForDataSharingPrepareConfig(config).includes("json")
      ? "json"
      : defaultUiFormatForDataSharingPrepareConfig(config);
  }
  renderDataSharingPrepareFormatOptions(state);
  if (!preserveSelection) applyDataSharingPrepareSelectionFilter(state);
  syncDataSharingPrepareListActions(state);
  renderDataSharingPrepareDocList(state);
}

export function renderDataSharingPrepareConfigSelect(state) {
  state.configSelect.innerHTML = state.exportConfigs.map((config) => {
    const id = normalizeText(config.id);
    const label = normalizeText(config.label) || id;
    return `<option value="${escapeHtml(id)}">${escapeHtml(label)}</option>`;
  }).join("");
  state.configSelect.selectedIndex = -1;
}

export function renderDataSharingPrepareDocList(state) {
  if (!stateUsesPrepareRecordSelection(state)) {
    if (state.selectableList) state.selectableList.update({ items: [], selectedIds: [] });
    state.listNode.innerHTML = "";
    state.listNode.hidden = false;
    updateDataSharingPrepareSelectionSummary(state);
    return;
  }
  const selectableDocs = selectableDataSharingPrepareDocs(state);
  state.listNode.hidden = false;
  if (!state.selectableList) {
    state.selectableList = createSelectableList(state.listNode, {
      id: "dataSharingPrepareRecords",
      selectAllButton: state.selectAllButton,
      clearButton: state.clearButton,
      tree: true,
      getId: (record) => prepareListRecordId(record),
      getLabel: (record) => prepareListRecordName(record),
      getMeta: () => [],
      getParentId: (record) => normalizeText(record && record.parent_id),
      onSelectionChange: ({ selectedIds }) => {
        state.selectedIds = new Set(selectedIds);
        updateDataSharingPrepareSelectionSummary(state);
        if (typeof state.onSelectionChange === "function") state.onSelectionChange();
      }
    });
  }
  state.selectableList.update({
    items: selectableDocs,
    selectedIds: currentDataSharingPrepareSelectedIds(state),
    cascadeSelection: state.includeDescendants,
    emptyMessage: ""
  });
  updateDataSharingPrepareSelectionSummary(state);
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
