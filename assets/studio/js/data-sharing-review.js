import { getStudioDataPath, getStudioText, loadStudioConfigWithText } from "./studio-config.js";
import {
  DATA_SHARING_ENDPOINTS,
  getJson,
  postJson,
  probeDataSharingHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import { openConfirmDetailModal, openNoticeModal } from "./studio-modal.js";
import {
  workflowDomainForKey,
  workflowDomainFromUrl,
  workflowDomainIsActive,
  workflowDomainsForOperation
} from "./data-sharing-adapters.js";

const DEFAULT_SCOPE = "library";
const WORKFLOW_SCOPES = [
  { key: "library", labelKey: "scope_library", fallback: "library" },
  { key: "tags", labelKey: "scope_tags", fallback: "tags" }
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

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
}

function workflowScopeFromUrl(domains = WORKFLOW_SCOPES) {
  return workflowDomainFromUrl(domains, DEFAULT_SCOPE);
}

function scopeSupportsSourceApply(state) {
  return workflowDomainIsActive(state.summaryApplyScopes, state.scope)
    || workflowDomainIsActive(state.hierarchyApplyScopes, state.scope);
}

function scopeLabel(state, scope = state.scope) {
  const item = workflowDomainForKey(state.workflowScopes, scope) || WORKFLOW_SCOPES[0];
  if (item.labelKey) return getStudioText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback);
  return normalizeText(item.label) || item.fallback || scope;
}

function scopeTitle(state, scope = state.scope) {
  const label = scopeLabel(state, scope);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : scope;
}

function renderScopeSelect(state) {
  state.scopeSelect.innerHTML = state.workflowScopes.map((item) => {
    const label = item.labelKey
      ? getStudioText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback);
    const selected = item.key === state.scope ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
}

function updateScopeUrl(scope, domains = WORKFLOW_SCOPES) {
  const nextScope = normalizeText(scope).toLowerCase();
  if (!domains.some((item) => item.key === nextScope)) return;
  const url = new URL(window.location.href);
  if (nextScope === DEFAULT_SCOPE) {
    url.searchParams.delete("scope");
  } else {
    url.searchParams.set("scope", nextScope);
  }
  window.location.href = url.toString();
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function loadAdapterRegistry(config) {
  const registryPath = getStudioDataPath(config, "data_sharing_adapters")
    || "/assets/studio/data/data_sharing_adapters.json";
  return loadJson(registryPath);
}

function scopeUnavailableMessage(state) {
  const domain = workflowDomainForKey(state.workflowScopes, state.scope);
  return normalizeText(domain && domain.message)
    || getStudioText(
      state.config,
      "data_sharing_review.scope_unsupported",
      "{scope_label} returned-package review is not implemented yet.",
      { scope_label: scopeTitle(state) }
    );
}

function routeModeForState(state) {
  if (state.previewRows && state.previewRows.length) {
    return "result";
  }
  return "selection";
}

function routeStateDetail(state) {
  if (state && state.root) state.root.dataset.studioScope = state.scope;
  return {
    route: "data-sharing-review",
    mode: routeModeForState(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.files && state.files.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function selectedFile(state) {
  const filename = normalizeText(state.fileSelect.value);
  return state.files.find((file) => normalizeText(file.filename) === filename) || null;
}

function resetResult(state) {
  state.selectedPreviewIds.clear();
  state.previewRows = [];
  renderPreviewList(state);
  updateSelectionSummary(state);
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

function countRowsHtml(rows) {
  const items = Array.isArray(rows) ? rows : [];
  if (!items.length) return "";
  return `
    <dl class="dataSharingReviewResultModal__counts">
      ${items.map((row) => `
        <div>
          <dt>${escapeHtml(row.label)}</dt>
          <dd>${escapeHtml(row.value)}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}

function issuesHtml(state, issues) {
  const items = issueItems(issues);
  if (!items.length) return "";
  const heading = getStudioText(state.config, "data_sharing_review.issues_heading", "Issues");
  return `
    <div class="dataSharingReviewResultModal__issues">
      <h4>${escapeHtml(heading)}</h4>
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function showResultModal(state, { title, summary, countRows, issues }) {
  const summaryHtml = normalizeText(summary)
    ? `<p class="tagStudioModal__label dataSharingReviewResultModal__summary">${escapeHtml(summary)}</p>`
    : "";
  const bodyHtml = `
    ${summaryHtml}
    ${countRowsHtml(countRows)}
    ${issuesHtml(state, issues)}
  `;
  openNoticeModal({
    root: state.root,
    title,
    bodyHtml,
    closeLabel: getStudioText(state.config, "data_sharing_review.result_close_button", "Close")
  }).catch((error) => console.warn("data_sharing_review: result modal failed", error));
}

function hideResultButton(state) {
  if (!state || !state.resultButton) return;
  state.resultButton.hidden = true;
}

function maybeShowResultButton(state, summary) {
  if (!state || !state.resultButton || !state.lastImportResult) return;
  const currentSummary = normalizeText(summary);
  state.resultButton.hidden = !currentSummary || currentSummary !== state.lastImportResult.summary;
}

function previewRowId(item, index) {
  return normalizeText(item && item.path)
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
  const treeFiles = [];
  (Array.isArray(previewFiles) ? previewFiles : []).forEach((item, index) => {
    if (!item || typeof item !== "object") return;
    const kind = normalizeText(item.kind);
    if (kind === "relationship_tree") {
      treeFiles.push({ item, index });
      return;
    }
    const recordIndex = Number.isInteger(item.record_index) ? item.record_index : null;
    if (recordIndex !== null && !byRecordIndex.has(recordIndex)) byRecordIndex.set(recordIndex, item);
    const docId = normalizeText(item.doc_id);
    if (docId && !byDocId.has(docId)) byDocId.set(docId, item);
  });
  return { byRecordIndex, byDocId, treeFiles };
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
      || getStudioText(state.config, "data_sharing_review.missing_doc_id", "missing doc_id")
  );
  if (duplicate) {
    parts.push(getStudioText(state.config, "data_sharing_review.duplicate_doc_id", "duplicate doc_id"));
  }
  if (currentLibrary && currentLibrary.exists === false) {
    parts.push(getStudioText(
      state.config,
      "data_sharing_review.not_current_scope",
      "not in current {scope_label}",
      { scope_label: scopeTitle(state) }
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
        || getStudioText(state.config, "data_sharing_review.missing_title", "missing title"),
      meta: rowMetaParts(state, { docId, duplicate, currentLibrary }).join(" · "),
      depth: 0
    };
  });
}

function orderDocumentRows(rows) {
  const ids = new Set(rows.map((row) => row.docId).filter(Boolean));
  const childrenByParent = new Map();
  rows.forEach((row) => {
    const parentId = row.parentId && row.parentId !== row.docId ? row.parentId : "";
    if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
    childrenByParent.get(parentId).push(row);
  });

  const roots = rows.filter((row) => !row.parentId || !ids.has(row.parentId) || row.parentId === row.docId);
  const ordered = [];
  const rendered = new Set();

  const visit = (row, depth, activeDocIds) => {
    if (!row || rendered.has(row.id)) return;
    row.depth = depth;
    ordered.push(row);
    rendered.add(row.id);
    if (!row.docId || activeDocIds.has(row.docId)) return;
    const nextActive = new Set(activeDocIds);
    nextActive.add(row.docId);
    (childrenByParent.get(row.docId) || []).forEach((child) => visit(child, depth + 1, nextActive));
  };

  roots.forEach((row) => visit(row, 0, new Set()));
  rows.forEach((row) => visit(row, 0, new Set()));
  return ordered;
}

function buildTreeRows(state, previewLookup) {
  return previewLookup.treeFiles.map(({ item, index }) => {
    const path = normalizeText(item.path);
    const count = Number(item.record_count || 0);
    const countText = getStudioText(
      state.config,
      "data_sharing_review.relationship_tree_count",
      "{count} records",
      { count }
    );
    return {
      id: previewRowId(item, index),
      type: "relationship_tree",
      docId: "",
      parentId: "",
      recordIndex: null,
      duplicate: false,
      kind: "relationship_tree",
      path,
      title: getStudioText(state.config, "data_sharing_review.relationship_tree_title", "Relationship tree"),
      meta: countText,
      depth: 0
    };
  });
}

function buildPreviewRows(state, payload) {
  const previewLookup = previewFilesByRecord(payload && payload.preview_files);
  const treeRows = buildTreeRows(state, previewLookup);
  const documentRows = orderDocumentRows(buildDocumentRows(state, payload, previewLookup));
  return [...treeRows, ...documentRows];
}

function renderPreviewRow(row) {
  const depth = Math.max(0, Number(row.depth || 0));
  const treeClass = row.type === "relationship_tree" ? " dataSharingReviewList__row--tree" : "";
  return `
    <li class="tagStudioList__row tagStudioList__row--center dataSharingReviewList__row${treeClass}" data-data-sharing-review-preview="${escapeHtml(row.id)}" data-data-sharing-review-depth="${depth}" style="--data-sharing-review-depth: ${depth};">
      <label class="dataSharingReviewList__label">
        <input class="dataSharingReviewList__checkbox" type="checkbox" value="${escapeHtml(row.id)}">
        <span class="dataSharingReviewList__title">${escapeHtml(row.title)}</span>
        ${row.meta ? `<span class="dataSharingReviewList__meta">${escapeHtml(row.meta)}</span>` : ""}
      </label>
    </li>
  `;
}

function renderPreviewList(state) {
  if (!state.previewRows.length) {
    const emptyState = getStudioText(
      state.config,
      "data_sharing_review.empty_state",
      "Generate a preview to list staged documents."
    );
    state.listNode.innerHTML = `<p class="tagStudio__status">${escapeHtml(emptyState)}</p>`;
    return;
  }
  state.listNode.innerHTML = `<ul class="tagStudioList__rows dataSharingReviewList__rows">${state.previewRows.map(renderPreviewRow).join("")}</ul>`;
  syncPreviewCheckboxes(state);
}

function selectablePreviewIds(state) {
  return state.previewRows.map((row) => row.id).filter(Boolean);
}

function selectedDocumentRecordIndices(state) {
  return state.previewRows
    .filter((row) => state.selectedPreviewIds.has(row.id) && row.type === "document" && Number.isInteger(row.recordIndex))
    .map((row) => row.recordIndex);
}

function syncPreviewCheckboxes(state) {
  state.listNode.querySelectorAll("[data-data-sharing-review-preview]").forEach((row) => {
    const rowId = normalizeText(row.getAttribute("data-data-sharing-review-preview"));
    const checkbox = row.querySelector("input[type='checkbox']");
    if (!(checkbox instanceof HTMLInputElement)) return;
    checkbox.checked = state.selectedPreviewIds.has(rowId);
  });
}

function updateSelectionSummary(state) {
  const count = state.selectedPreviewIds.size;
  setText(
    state.selectionSummary,
    getStudioText(
      state.config,
      count === 1
        ? "data_sharing_review.selection_summary_one"
        : "data_sharing_review.selection_summary",
      count === 1 ? "1 preview selected." : "{count} previews selected.",
      { count }
    )
  );
  syncApplyActionState(state);
}

function handlePreviewListChange(state, event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return;
  const row = target.closest("[data-data-sharing-review-preview]");
  const rowId = normalizeText(row ? row.getAttribute("data-data-sharing-review-preview") : "");
  if (!rowId) return;
  if (target.checked) {
    state.selectedPreviewIds.add(rowId);
  } else {
    state.selectedPreviewIds.delete(rowId);
  }
  updateSelectionSummary(state);
}

function previewCountRows(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return [
    {
      label: getStudioText(state.config, "data_sharing_review.count_records", "records"),
      value: Number(safeCounts.records || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_parsed", "parsed"),
      value: Number(safeCounts.parsed_records || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_malformed", "malformed"),
      value: Number(safeCounts.malformed_records || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_warnings", "warnings"),
      value: Number(safeCounts.warnings || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_errors", "errors"),
      value: Number(safeCounts.errors || 0)
    }
  ];
}

function renderResult(state, payload, failed = false) {
  const result = {
    title: getStudioText(
      state.config,
      failed ? "data_sharing_review.result_title_failed" : "data_sharing_review.result_title",
      failed ? "Returned package review failed" : "Returned package review"
    ),
    summary: normalizeText(payload.summary_text || ""),
    countRows: previewCountRows(state, payload.counts),
    issues: payload.issues
  };
  state.previewRows = failed ? [] : buildPreviewRows(state, payload);
  state.selectedPreviewIds.clear();
  renderPreviewList(state);
  updateSelectionSummary(state);
  state.lastImportResult = failed ? null : result;
  showResultModal(state, result);
}

function setControlsDisabled(state, disabled) {
  const supportsApply = scopeSupportsSourceApply(state);
  state.fileSelect.disabled = disabled || !state.files.length;
  state.previewButton.disabled = disabled || !state.serviceAvailable || !state.files.length;
  state.selectAllButton.disabled = disabled || !state.previewRows.length;
  state.clearButton.disabled = disabled || !state.previewRows.length;
  state.updateSummaryButton.disabled = disabled || !supportsApply || !state.serviceAvailable || !selectedDocumentRecordIndices(state).length;
  state.applyHierarchyButton.disabled = disabled || !supportsApply || !state.serviceAvailable || !selectedDocumentRecordIndices(state).length;
}

function syncApplyActionState(state) {
  if (!state.updateSummaryButton || !state.applyHierarchyButton) return;
  const supportsApply = scopeSupportsSourceApply(state);
  state.updateSummaryButton.disabled = state.isRunning || !supportsApply || !state.serviceAvailable || !selectedDocumentRecordIndices(state).length;
  state.applyHierarchyButton.disabled = state.isRunning || !supportsApply || !state.serviceAvailable || !selectedDocumentRecordIndices(state).length;
}

async function loadImportFiles(scope) {
  const url = `${DATA_SHARING_ENDPOINTS.returnedPackages}?data_domain=${encodeURIComponent(scope)}`;
  const payload = await getJson(url);
  return Array.isArray(payload.files) ? payload.files : [];
}

async function runPreview(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedFile(state);
  if (!file) {
    hideResultButton(state);
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "data_sharing_review.file_required", "Select a staged data file first.")
    );
    return;
  }

  resetResult(state);
  hideResultButton(state);
  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "data_sharing_review.running_status", "Generating returned package reviews...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.review, {
      data_domain: state.scope,
      operation: "review",
      staged_filename: file.filename
    });
    renderResult(state, payload, false);
    const successMessage = payload.summary_text || getStudioText(state.config, "data_sharing_review.status_success", "Returned package reviews generated.");
    setStatus(
      state.statusNode,
      "success",
      successMessage
    );
    maybeShowResultButton(state, successMessage);
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    renderResult(state, payload, true);
    hideResultButton(state);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || getStudioText(state.config, "data_sharing_review.status_failed", "Returned package review failed.")
    );
  } finally {
    state.isRunning = false;
    setControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

function applyCountsText(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return getStudioText(
    state.config,
    "data_sharing_review.summary_apply_counts",
    "{updates} updates; {skipped} skipped; {errors} errors.",
    {
      updates: Number(safeCounts.updates || 0),
      skipped: Number(safeCounts.skipped || 0),
      errors: Number(safeCounts.errors || 0)
    }
  );
}

function applyCountRows(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return [
    {
      label: getStudioText(state.config, "data_sharing_review.count_updates", "updates"),
      value: Number(safeCounts.updates || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_skipped", "skipped"),
      value: Number(safeCounts.skipped || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_errors", "errors"),
      value: Number(safeCounts.errors || 0)
    }
  ];
}

function hierarchyCountsText(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return getStudioText(
    state.config,
    "data_sharing_review.hierarchy_apply_counts",
    "{changed} changed; {unchanged} unchanged; {skipped} skipped; {warnings} warnings; {errors} errors.",
    {
      changed: Number(safeCounts.changed || safeCounts.updates || 0),
      unchanged: Number(safeCounts.unchanged || 0),
      skipped: Number(safeCounts.skipped || 0),
      warnings: Number(safeCounts.warnings || 0),
      errors: Number(safeCounts.errors || 0)
    }
  );
}

function hierarchyCountRows(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return [
    {
      label: getStudioText(state.config, "data_sharing_review.count_changed", "changed"),
      value: Number(safeCounts.changed || safeCounts.updates || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_unchanged", "unchanged"),
      value: Number(safeCounts.unchanged || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_skipped", "skipped"),
      value: Number(safeCounts.skipped || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_warnings", "warnings"),
      value: Number(safeCounts.warnings || 0)
    },
    {
      label: getStudioText(state.config, "data_sharing_review.count_errors", "errors"),
      value: Number(safeCounts.errors || 0)
    }
  ];
}

function applyIssues(payload, fallbackPrefix) {
  const errors = Array.isArray(payload && payload.errors) ? payload.errors : [];
  const warnings = Array.isArray(payload && payload.warnings) ? payload.warnings : [];
  const skipped = Array.isArray(payload && payload.skipped) ? payload.skipped : [];
  return [
    ...errors.map((item) => ({
      level: "error",
      code: item.reason || item.code || "error",
      doc_id: item.doc_id,
      message: item.message || item.reason || `${fallbackPrefix} error`
    })),
    ...warnings.map((item) => ({
      level: item.level || "warning",
      code: item.reason || item.code || "warning",
      doc_id: item.doc_id,
      message: item.message || item.reason || `${fallbackPrefix} warning`
    })),
    ...skipped.map((item) => ({
      level: "warning",
      code: item.reason || "skipped",
      doc_id: item.doc_id,
      message: item.message || "selected row skipped"
    }))
  ];
}

function renderSummaryApplyResult(state, payload) {
  const countsValue = applyCountsText(state, payload && payload.counts);
  const summary = normalizeText(payload && payload.summary_text);
  showResultModal(state, {
    title: getStudioText(state.config, "data_sharing_review.summary_apply_result_title", "Summary update complete"),
    summary: `${summary} ${countsValue}`.trim(),
    countRows: applyCountRows(state, payload && payload.counts),
    issues: applyIssues(payload || {}, "summary apply")
  });
}

function renderHierarchyApplyResult(state, payload) {
  const countsValue = hierarchyCountsText(state, payload && payload.counts);
  const summary = normalizeText(payload && payload.summary_text);
  showResultModal(state, {
    title: getStudioText(state.config, "data_sharing_review.hierarchy_apply_result_title", "Hierarchy update complete"),
    summary: `${summary} ${countsValue}`.trim(),
    countRows: hierarchyCountRows(state, payload && payload.counts),
    issues: applyIssues(payload || {}, "hierarchy apply")
  });
}

function selectedFileName(state) {
  const file = selectedFile(state);
  return normalizeText(file && file.filename);
}

async function runSummaryApply(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  hideResultButton(state);
  const stagedFilename = selectedFileName(state);
  const recordIndices = selectedDocumentRecordIndices(state);
  if (!stagedFilename || !recordIndices.length) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "data_sharing_review.summary_apply_selection_required", "Select at least one document preview.")
    );
    return;
  }

  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "data_sharing_review.summary_apply_preflight_status", "Checking selected summaries...")
  );

  try {
    const preflight = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: "summary_apply",
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: false
    });
    const countsTextValue = applyCountsText(state, preflight.counts);
    if (!preflight.ok || Number(preflight.counts && preflight.counts.updates || 0) < 1) {
      setStatus(state.statusNode, preflight.ok ? "warn" : "error", preflight.summary_text || countsTextValue);
      renderSummaryApplyResult(state, preflight);
      return;
    }

    const confirm = await openConfirmDetailModal({
      root: state.root,
      title: getStudioText(state.config, "data_sharing_review.summary_apply_confirm_title", "Update summaries?"),
      body: [
        preflight.summary_text || countsTextValue,
        countsTextValue,
        getStudioText(
          state.config,
          "data_sharing_review.summary_apply_confirm_body",
          "This will back up and update selected Library source files."
        )
      ],
      primaryLabel: getStudioText(state.config, "data_sharing_review.summary_apply_confirm_ok", "OK"),
      cancelLabel: getStudioText(state.config, "data_sharing_review.summary_apply_confirm_cancel", "Cancel")
    });
    if (!confirm.confirmed) {
      setStatus(
        state.statusNode,
        "",
        getStudioText(state.config, "data_sharing_review.summary_apply_cancelled", "Summary update cancelled.")
      );
      return;
    }

    setStatus(
      state.statusNode,
      "",
      getStudioText(state.config, "data_sharing_review.summary_apply_running_status", "Updating selected summaries...")
    );
    const applied = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: "summary_apply",
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: true,
      activity_context: buildStudioActivityContext({
        pageId: "data-sharing-review",
        actionId: "apply-returned-summaries",
        route: "/studio/data-sharing/review/",
        controlId: "dataSharingReviewUpdateSummary",
        controlSelector: "#dataSharingReviewUpdateSummary",
        recordIdField: "staged_filename",
        recordId: stagedFilename
      })
    });
    renderSummaryApplyResult(state, applied);
    setStatus(
      state.statusNode,
      "success",
      applied.summary_text || getStudioText(state.config, "data_sharing_review.summary_apply_success", "Summaries updated.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    const message = normalizeText(payload.summary_text) || normalizeText(error && error.message)
      || getStudioText(state.config, "data_sharing_review.summary_apply_failed", "Summary update failed.");
    renderSummaryApplyResult(state, { ...payload, summary_text: message });
    setStatus(state.statusNode, "error", message);
  } finally {
    state.isRunning = false;
    setControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

async function runHierarchyApply(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  hideResultButton(state);
  const stagedFilename = selectedFileName(state);
  const recordIndices = selectedDocumentRecordIndices(state);
  if (!stagedFilename || !recordIndices.length) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "data_sharing_review.summary_apply_selection_required", "Select at least one document preview.")
    );
    return;
  }

  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "data_sharing_review.hierarchy_apply_preflight_status", "Checking selected hierarchy changes...")
  );

  try {
    const preflight = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: "hierarchy_apply",
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: false
    });
    const countsTextValue = hierarchyCountsText(state, preflight.counts);
    if (!preflight.ok || Number(preflight.counts && (preflight.counts.changed || preflight.counts.updates) || 0) < 1) {
      setStatus(state.statusNode, preflight.ok ? "warn" : "error", preflight.summary_text || countsTextValue);
      renderHierarchyApplyResult(state, preflight);
      return;
    }

    const confirm = await openConfirmDetailModal({
      root: state.root,
      title: getStudioText(state.config, "data_sharing_review.hierarchy_apply_confirm_title", "Update hierarchy?"),
      body: [
        preflight.summary_text || countsTextValue,
        countsTextValue,
        getStudioText(
          state.config,
          "data_sharing_review.hierarchy_apply_confirm_body",
          "This will back up and update selected Library source parent ids."
        )
      ],
      primaryLabel: getStudioText(state.config, "data_sharing_review.hierarchy_apply_confirm_ok", "OK"),
      cancelLabel: getStudioText(state.config, "data_sharing_review.hierarchy_apply_confirm_cancel", "Cancel")
    });
    if (!confirm.confirmed) {
      setStatus(
        state.statusNode,
        "",
        getStudioText(state.config, "data_sharing_review.hierarchy_apply_cancelled", "Hierarchy update cancelled.")
      );
      return;
    }

    setStatus(
      state.statusNode,
      "",
      getStudioText(state.config, "data_sharing_review.hierarchy_apply_running_status", "Updating selected hierarchy...")
    );
    const applied = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: "hierarchy_apply",
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: true,
      activity_context: buildStudioActivityContext({
        pageId: "data-sharing-review",
        actionId: "apply-returned-hierarchy",
        route: "/studio/data-sharing/review/",
        controlId: "dataSharingReviewApplyHierarchy",
        controlSelector: "#dataSharingReviewApplyHierarchy",
        recordIdField: "staged_filename",
        recordId: stagedFilename
      })
    });
    renderHierarchyApplyResult(state, applied);
    setStatus(
      state.statusNode,
      "success",
      applied.summary_text || getStudioText(state.config, "data_sharing_review.hierarchy_apply_success", "Hierarchy updated.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    const message = normalizeText(payload.summary_text) || normalizeText(error && error.message)
      || getStudioText(state.config, "data_sharing_review.hierarchy_apply_failed", "Hierarchy update failed.");
    renderHierarchyApplyResult(state, { ...payload, summary_text: message });
    setStatus(state.statusNode, "error", message);
  } finally {
    state.isRunning = false;
    setControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

async function init() {
  const bootStatus = document.getElementById("dataSharingReviewBootStatus");
  const root = document.getElementById("dataSharingReviewRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "data-sharing-review", mode: "selection" });

  const state = {
    bootStatus,
    root,
    scope: workflowScopeFromUrl(),
    workflowScopes: WORKFLOW_SCOPES,
    summaryApplyScopes: WORKFLOW_SCOPES,
    hierarchyApplyScopes: WORKFLOW_SCOPES,
    scopeLabelNode: document.getElementById("dataSharingReviewScopeLabel"),
    scopeSelect: document.getElementById("dataSharingReviewScopeSelect"),
    fileLabelNode: document.getElementById("dataSharingReviewFileLabel"),
    fileSelect: document.getElementById("dataSharingReviewFileSelect"),
    previewButton: document.getElementById("dataSharingReviewRun"),
    statusNode: document.getElementById("dataSharingReviewStatus"),
    resultButton: document.getElementById("dataSharingReviewResults"),
    selectionSummary: document.getElementById("dataSharingReviewSelectionSummary"),
    selectAllButton: document.getElementById("dataSharingReviewSelectAll"),
    clearButton: document.getElementById("dataSharingReviewClear"),
    listNode: document.getElementById("dataSharingReviewList"),
    updateSummaryButton: document.getElementById("dataSharingReviewUpdateSummary"),
    applyHierarchyButton: document.getElementById("dataSharingReviewApplyHierarchy"),
    config: null,
    files: [],
    previewRows: [],
    selectedPreviewIds: new Set(),
    lastImportResult: null,
    serviceAvailable: false,
    isRunning: false
  };

  const requiredNodes = [
    state.scopeLabelNode,
    state.scopeSelect,
    state.fileLabelNode,
    state.fileSelect,
    state.previewButton,
    state.statusNode,
    state.resultButton,
    state.selectionSummary,
    state.selectAllButton,
    state.clearButton,
    state.listNode,
    state.updateSummaryButton,
    state.applyHierarchyButton
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadStudioConfigWithText("data_sharing_review");
    const adapterRegistry = await loadAdapterRegistry(state.config);
    state.workflowScopes = workflowDomainsForOperation(adapterRegistry, "list_returned", WORKFLOW_SCOPES);
    state.summaryApplyScopes = workflowDomainsForOperation(adapterRegistry, "apply", []);
    state.hierarchyApplyScopes = workflowDomainsForOperation(adapterRegistry, "apply", []);
    state.scope = workflowScopeFromUrl(state.workflowScopes);
    renderScopeSelect(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());

    setText(state.scopeLabelNode, getStudioText(state.config, "data_sharing_review.scope_label", "scope"));
    setText(state.fileLabelNode, getStudioText(state.config, "data_sharing_review.file_label", "staged file"));
    setText(state.previewButton, getStudioText(state.config, "data_sharing_review.preview_button", "Review package"));
    setText(state.resultButton, getStudioText(state.config, "data_sharing_review.result_button", "results"));
    setText(state.selectAllButton, getStudioText(state.config, "data_sharing_review.select_all", "select all"));
    setText(state.clearButton, getStudioText(state.config, "data_sharing_review.clear", "clear"));
    setText(
      state.updateSummaryButton,
      getStudioText(state.config, "data_sharing_review.update_summary_button", "Update summary")
    );
    setText(
      state.applyHierarchyButton,
      getStudioText(state.config, "data_sharing_review.apply_hierarchy_button", "Apply hierarchy")
    );
    state.updateSummaryButton.title = getStudioText(
      state.config,
      "data_sharing_review.update_summary_title",
      "Update selected document summaries from the staged file."
    );
    state.applyHierarchyButton.title = getStudioText(
      state.config,
      "data_sharing_review.apply_hierarchy_title",
      "Update selected document parent ids from the staged file."
    );
    if (!scopeSupportsSourceApply(state)) {
      const unsupportedApplyTitle = getStudioText(
        state.config,
        "data_sharing_review.apply_unsupported_title",
        "{scope_label} source apply actions are not implemented yet.",
        { scope_label: scopeTitle(state) }
      );
      state.updateSummaryButton.title = unsupportedApplyTitle;
      state.applyHierarchyButton.title = unsupportedApplyTitle;
    }
    renderPreviewList(state);
    updateSelectionSummary(state);
    setControlsDisabled(state, true);

    root.hidden = false;
    bootStatus.hidden = true;

    state.scopeSelect.addEventListener("change", () => updateScopeUrl(state.scopeSelect.value, state.workflowScopes));

    if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
      setControlsDisabled(state, true);
      setStatus(state.statusNode, "warn", scopeUnavailableMessage(state));
      markRouteReady(state, true);
      return;
    }

    if (!state.serviceAvailable) {
      setControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "error",
        getStudioText(
          state.config,
          "data_sharing_review.service_unavailable",
          "Docs management service unavailable. Start bin/dev-studio to review {scope_label} returned packages.",
          { scope_label: scopeLabel(state) }
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.files = await loadImportFiles(state.scope);
    if (!state.files.length) {
      setControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "warn",
        getStudioText(
          state.config,
          "data_sharing_review.no_files",
          "No staged {scope_label} data files found under var/studio/data-sharing/{scope}/import-staging/.",
          { scope_label: scopeLabel(state), scope: state.scope }
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.fileSelect.innerHTML = state.files.map((file) => {
      const filename = normalizeText(file.filename);
      return `<option value="${escapeHtml(filename)}">${escapeHtml(filename)}</option>`;
    }).join("");
    setControlsDisabled(state, false);
    setStatus(
      state.statusNode,
      "",
      getStudioText(
        state.config,
        "data_sharing_review.idle_status",
        "Select a staged {scope_label} data file and generate previews.",
        { scope_label: scopeLabel(state) }
      )
    );
    markRouteReady(state, true);

    state.fileSelect.addEventListener("change", () => {
      resetResult(state);
      state.lastImportResult = null;
      hideResultButton(state);
      setControlsDisabled(state, false);
      setStatus(
        state.statusNode,
        "",
        getStudioText(
          state.config,
          "data_sharing_review.idle_status",
          "Select a staged {scope_label} data file and generate previews.",
          { scope_label: scopeLabel(state) }
        )
      );
      syncRouteBusyState(state);
    });
    state.previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("data_sharing_review: unexpected preview failure", error));
    });
    state.resultButton.addEventListener("click", () => {
      if (state.lastImportResult) showResultModal(state, state.lastImportResult);
    });
    state.selectAllButton.addEventListener("click", () => {
      selectablePreviewIds(state).forEach((rowId) => state.selectedPreviewIds.add(rowId));
      syncPreviewCheckboxes(state);
      updateSelectionSummary(state);
    });
    state.clearButton.addEventListener("click", () => {
      state.selectedPreviewIds.clear();
      syncPreviewCheckboxes(state);
      updateSelectionSummary(state);
    });
    state.listNode.addEventListener("change", (event) => handlePreviewListChange(state, event));
    state.updateSummaryButton.addEventListener("click", () => {
      runSummaryApply(state).catch((error) => console.warn("data_sharing_review: unexpected summary apply failure", error));
    });
    state.applyHierarchyButton.addEventListener("click", () => {
      runHierarchyApply(state).catch((error) => console.warn("data_sharing_review: unexpected hierarchy apply failure", error));
    });
  } catch (error) {
    console.warn("data_sharing_review: init failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    state.serviceAvailable = false;
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config || {},
        "data_sharing_review.load_failed",
        "Failed to load {scope_label} returned package data.",
        { scope_label: state.config ? scopeTitle(state) : "Library" }
      )
    );
    markRouteReady(state, true);
  } finally {
    state.isRunning = false;
    syncRouteBusyState(state);
  }
}

init();
