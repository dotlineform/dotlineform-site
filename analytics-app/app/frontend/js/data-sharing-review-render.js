import { getAnalyticsText } from "./analytics-config.js";
import {
  createSelectableList
} from "/shared/frontend/js/selectable-list.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
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

export function buildDataSharingReviewPreviewRows(state, payload) {
  const genericRows = Array.isArray(payload && payload.review_rows) ? payload.review_rows : [];
  return genericRows
    .filter((row) => {
      const rowType = normalizeText(row && row.type);
      const rowKind = normalizeText(row && row.kind);
      return rowType !== "relationship_tree" && rowKind !== "relationship_tree";
    })
    .map((row, index) => normalizeReviewRow(state, row, index))
    .filter(Boolean);
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
