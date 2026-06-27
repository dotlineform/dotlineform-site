import { getAnalyticsText } from "./analytics-config.js";
import {
  createSelectableList
} from "/shared/frontend/js/selectable-list.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function dataDomainLabel(state, dataDomain = state.dataDomain) {
  const item = (state.dataDomains || []).find((candidate) => candidate.key === dataDomain);
  if (item && item.labelKey) return getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback);
  return normalizeText(item && item.label) || normalizeText(item && item.fallback) || dataDomain;
}

function dataDomainTitle(state, dataDomain = state.dataDomain) {
  const label = dataDomainLabel(state, dataDomain);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : dataDomain;
}

function issueLabel(issue) {
  const code = normalizeText(issue && issue.code);
  const level = normalizeText(issue && issue.level);
  const docId = normalizeText(issue && issue.doc_id);
  const message = normalizeText(issue && issue.message);
  const prefix = [level, code].filter(Boolean).join(" ");
  const suffix = docId ? ` (${docId})` : "";
  return `${prefix ? `${prefix}: ` : ""}${message}${suffix}`;
}

function issueItems(issues) {
  return Array.isArray(issues) ? issues.map(issueLabel).filter(Boolean) : [];
}

function previewRowId(item, index) {
  return normalizeText(item && item.id)
    || normalizeText(item && item.path)
    || normalizeText(item && item.doc_id)
    || `preview-${index + 1}`;
}

function recordRowId(record, index) {
  const recordIndex = Number.isInteger(record && record.record_index) ? record.record_index : index;
  const docId = normalizeText(record && record.doc_id) || "missing-doc-id";
  return `${docId}-record-${recordIndex + 1}`;
}

function previewFilesByRecord(previewFiles) {
  const byRecordIndex = new Map();
  const byDocId = new Map();
  (Array.isArray(previewFiles) ? previewFiles : []).forEach((item, index) => {
    if (!item || typeof item !== "object") return;
    const kind = normalizeText(item.kind);
    if (kind === "relationship_tree") return;
    const recordIndex = Number.isInteger(item.record_index) ? item.record_index : null;
    if (recordIndex !== null && !byRecordIndex.has(recordIndex)) byRecordIndex.set(recordIndex, item);
    const docId = normalizeText(item.doc_id);
    if (docId && !byDocId.has(docId)) byDocId.set(docId, item);
  });
  return { byRecordIndex, byDocId };
}

function duplicateDocIds(records) {
  const counts = new Map();
  records.forEach((record) => {
    const docId = normalizeText(record && record.doc_id);
    if (!docId) return;
    counts.set(docId, Number(counts.get(docId) || 0) + 1);
  });
  return new Set(Array.from(counts.entries()).filter(([, count]) => count > 1).map(([docId]) => docId));
}

function rowMetaParts(state, { docId, duplicate, currentLibrary }) {
  const parts = [];
  parts.push(
    docId
      || getAnalyticsText(state.config, "data_sharing_review.missing_doc_id", "missing doc_id")
  );
  if (duplicate) {
    parts.push(getAnalyticsText(state.config, "data_sharing_review.duplicate_doc_id", "duplicate doc_id"));
  }
  if (currentLibrary && currentLibrary.exists === false) {
    parts.push(getAnalyticsText(
      state.config,
      "data_sharing_review.not_current_data_domain",
      "not in current {data_domain_label}",
      { data_domain_label: dataDomainTitle(state) }
    ));
  }
  return parts.filter(Boolean);
}

function buildDocumentRows(state, payload, previewLookup) {
  const records = Array.isArray(payload && payload.records) ? payload.records : [];
  const duplicates = duplicateDocIds(records);
  return records.map((record, index) => {
    const recordIndex = Number.isInteger(record && record.record_index) ? record.record_index : index;
    const docId = normalizeText(record && record.doc_id);
    const previewFile = previewLookup.byRecordIndex.get(recordIndex) || previewLookup.byDocId.get(docId) || null;
    const path = normalizeText(previewFile && previewFile.path);
    const currentLibrary = record && typeof record.current_library === "object" ? record.current_library : null;
    const duplicate = docId ? duplicates.has(docId) : false;
    return {
      id: recordRowId(record, index),
      type: "document",
      docId,
      parentId: normalizeText(record && record.parent_id),
      recordIndex,
      duplicate,
      kind: normalizeText(previewFile && previewFile.kind) || "document",
      path,
      title: normalizeText(record && record.title)
        || getAnalyticsText(state.config, "data_sharing_review.missing_title", "missing title"),
      meta: rowMetaParts(state, { docId, duplicate, currentLibrary }).join(" \u00b7 "),
      depth: 0,
      selectable: true,
      issues: Array.isArray(record && record.issues) ? record.issues : []
    };
  });
}

function documentRowDepth(row, byDocId, activeDocIds = new Set()) {
  if (!row || !row.docId || !row.parentId || row.parentId === row.docId) return 0;
  if (activeDocIds.has(row.docId)) return 0;
  const parent = byDocId.get(row.parentId);
  if (!parent) return 0;
  const nextActive = new Set(activeDocIds);
  nextActive.add(row.docId);
  return documentRowDepth(parent, byDocId, nextActive) + 1;
}

function prepareDocumentRowsForDisplay(rows) {
  const byDocId = new Map();
  rows.forEach((row) => {
    if (row.docId && !byDocId.has(row.docId)) byDocId.set(row.docId, row);
  });
  rows.forEach((row) => {
    row.depth = documentRowDepth(row, byDocId);
  });
  return rows;
}

export function buildDataSharingReviewPreviewRows(state, payload) {
  const genericRows = Array.isArray(payload && payload.review_rows) ? payload.review_rows : [];
  if (genericRows.length) {
    return genericRows.map((row, index) => normalizeReviewRow(state, row, index)).filter(Boolean);
  }
  const previewLookup = previewFilesByRecord(payload && payload.preview_files);
  const documentRows = prepareDocumentRowsForDisplay(buildDocumentRows(state, payload, previewLookup));
  return documentRows;
}

function normalizeReviewRow(state, row, index) {
  if (!row || typeof row !== "object") return null;
  const recordIndex = Number.isInteger(row.record_index) ? row.record_index : null;
  const issueTexts = issueItems(row.issues);
  const metaParts = [
    normalizeText(row.meta),
    recordIndex === null
      ? ""
      : getAnalyticsText(state.config, "data_sharing_review.record_index_meta", "row {record_index}", { record_index: recordIndex + 1 }),
    issueTexts.length
      ? getAnalyticsText(state.config, "data_sharing_review.row_issues_meta", "{count} issue(s)", { count: issueTexts.length })
      : ""
  ].filter(Boolean);
  return {
    id: previewRowId(row, index),
    type: normalizeText(row.type) || getAnalyticsText(state.config, "data_sharing_review.row_type_record", "record"),
    title: normalizeText(row.title) || getAnalyticsText(state.config, "data_sharing_review.missing_title", "missing title"),
    meta: metaParts.join(" \u00b7 "),
    recordIndex,
    selectable: row.selectable !== false && Number.isInteger(recordIndex),
    issues: Array.isArray(row.issues) ? row.issues : [],
    depth: Math.max(0, Number(row.depth || 0))
  };
}

export function renderDataSharingReviewPreviewList(state) {
  const emptyMessage = getAnalyticsText(
    state.config,
    "data_sharing_review.empty_state",
    "Generate a preview to list staged documents."
  );
  if (!state.selectableList) {
    state.selectableList = createSelectableList(state.listNode, {
      id: "dataSharingReviewDocuments",
      selectAllButton: state.selectAllButton,
      clearButton: state.clearButton,
      getId: (row) => normalizeText(row && row.id),
      getLabel: (row) => normalizeText(row && row.title),
      getMeta: () => [],
      getIndent: (row) => `${Math.max(0, Number(row && row.depth || 0)) * 1.15}rem`,
      isDisabled: (row) => row && row.selectable === false,
      onSelectionChange: ({ selectedIds }) => {
        state.selectedPreviewIds = new Set(selectedIds);
        if (typeof state.onPreviewSelectionChange === "function") {
          state.onPreviewSelectionChange();
        } else {
          updateDataSharingReviewSelectionSummary(state);
        }
      }
    });
  }
  state.selectableList.update({
    items: state.previewRows,
    selectedIds: Array.from(state.selectedPreviewIds),
    disabled: Boolean(state.isRunning),
    emptyMessage
  });
  updateDataSharingReviewSelectionSummary(state);
}

export function selectableDataSharingReviewPreviewIds(state) {
  return state.previewRows
    .filter((row) => row.selectable !== false)
    .map((row) => row.id)
    .filter(Boolean);
}

export function selectedDataSharingReviewRecordIndices(state) {
  return state.previewRows
    .filter((row) => state.selectedPreviewIds.has(row.id) && row.selectable !== false && Number.isInteger(row.recordIndex))
    .map((row) => row.recordIndex);
}

export function updateDataSharingReviewSelectionSummary(state) {
  const count = state.selectedPreviewIds.size;
  if (!state.selectionSummary) return;
  state.selectionSummary.textContent = normalizeText(getAnalyticsText(
    state.config,
    count === 1
      ? "data_sharing_review.selection_summary_one"
      : "data_sharing_review.selection_summary",
    count === 1 ? "1 preview selected." : "{count} previews selected.",
    { count }
  ));
}
