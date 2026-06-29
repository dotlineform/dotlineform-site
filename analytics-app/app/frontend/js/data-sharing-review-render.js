import { getAnalyticsText } from "./analytics-config.js";
import {
  createSelectableList
} from "/shared/frontend/js/selectable-list.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function previewRowId(item, index) {
  return normalizeText(item && item.id)
    || normalizeText(item && item.path)
    || normalizeText(item && item.doc_id)
    || `preview-${index + 1}`;
}

export function buildDataSharingReviewPreviewRows(state, payload) {
  const genericRows = Array.isArray(payload && payload.review_rows) ? payload.review_rows : [];
  return genericRows
    .map((row, index) => normalizeReviewRow(state, row, index))
    .filter(Boolean);
}

function normalizeReviewRow(state, row, index) {
  if (!row || typeof row !== "object") return null;
  const recordIndex = Number.isInteger(row.record_index) ? row.record_index : null;
  return {
    id: previewRowId(row, index),
    type: normalizeText(row.type) || getAnalyticsText(state.config, "data_sharing_review.row_type_record", "record"),
    title: normalizeText(row.title) || getAnalyticsText(state.config, "data_sharing_review.missing_title", "missing title"),
    meta: "",
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
    "Select a staged file to list documents."
  );
  if (!state.selectableList) {
    state.selectableList = createSelectableList(state.listNode, {
      id: "dataSharingReviewDocuments",
      readOnly: true,
      getId: (row) => normalizeText(row && row.id),
      getLabel: (row) => normalizeText(row && row.title),
      getMeta: () => [],
      getIndent: (row) => `${Math.max(0, Number(row && row.depth || 0)) * 1.15}rem`,
      isDisabled: (row) => row && row.selectable === false
    });
  }
  state.selectableList.update({
    items: state.previewRows,
    selectedIds: [],
    disabled: Boolean(state.isRunning),
    emptyMessage,
    readOnly: true
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
    .filter((row) => row.selectable !== false && Number.isInteger(row.recordIndex))
    .map((row) => row.recordIndex);
}

export function updateDataSharingReviewSelectionSummary(state) {
  const count = state.previewRows.length;
  if (!state.selectionSummary) return;
  state.selectionSummary.textContent = normalizeText(getAnalyticsText(
    state.config,
    count === 1
      ? "data_sharing_review.records_summary_one"
      : "data_sharing_review.records_summary",
    count === 1 ? "1 staged document." : "{count} staged documents.",
    { count }
  ));
}
