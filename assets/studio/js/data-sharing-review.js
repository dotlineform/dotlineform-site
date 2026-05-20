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
import {
  confirmDataSharingReviewApply,
  showDataSharingReviewResultModal
} from "./data-sharing-review-modals.js";
import {
  buildDataSharingReviewPreviewRows,
  renderDataSharingReviewPreviewList,
  selectableDataSharingReviewPreviewIds,
  selectedDataSharingReviewRecordIndices,
  syncDataSharingReviewPreviewCheckboxes,
  updateDataSharingReviewSelectionFromChange,
  updateDataSharingReviewSelectionSummary
} from "./data-sharing-review-render.js";
import {
  workflowCapabilityForOperation,
  workflowDomainForKey,
  workflowDomainFromUrl,
  workflowDomainIsActive,
  workflowScopeParamForKey,
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
  return state.applyActions.some((action) => action.status === "active");
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

function normalizeId(value) {
  return normalizeText(value).toLowerCase();
}

function actionUi(action) {
  return action && action.ui && typeof action.ui === "object" ? action.ui : {};
}

function actionResult(action) {
  return action && action.result && typeof action.result === "object" ? action.result : {};
}

function normalizeApplyAction(action, index) {
  if (!action || typeof action !== "object") return null;
  const id = normalizeText(action.id);
  if (!id) return null;
  const ui = actionUi(action);
  return {
    ...action,
    id,
    status: normalizeId(action.status) || "active",
    label: normalizeText(action.label) || id,
    controlId: normalizeText(ui.control_id) || `dataSharingReviewApplyAction${index + 1}`,
    controlSelector: normalizeText(ui.control_selector) || "",
    activityActionId: normalizeText(ui.activity_action_id) || `apply-returned-${id.replace(/_/g, "-")}`,
    selectionRequiredMessage: normalizeText(ui.selection_required_message),
    preflightStatus: normalizeText(ui.preflight_status),
    runningStatus: normalizeText(ui.running_status),
    cancelledStatus: normalizeText(ui.cancelled_status),
    successStatus: normalizeText(ui.success_status),
    failedStatus: normalizeText(ui.failed_status),
    unavailableTitle: normalizeText(ui.unavailable_title),
    noChangeCountKey: normalizeText(ui.no_change_count_key),
    resultTitle: normalizeText(actionResult(action).title),
    countText: normalizeText(actionResult(action).count_text),
    countRows: Array.isArray(actionResult(action).count_rows) ? actionResult(action).count_rows : []
  };
}

function applyActionsForCapability(capability) {
  const rawActions = Array.isArray(capability && capability.apply_actions) ? capability.apply_actions : [];
  return rawActions.map(normalizeApplyAction).filter(Boolean);
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

function hideApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || !state.actionMenuButton) return;
  state.applyActionMenu.hidden = true;
  state.applyActionMenu.style.left = "";
  state.applyActionMenu.style.top = "";
  state.applyActionMenu.style.minWidth = "";
  state.actionMenuButton.setAttribute("aria-expanded", "false");
}

function positionApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || !state.actionMenuButton) return;
  const triggerRect = state.actionMenuButton.getBoundingClientRect();
  state.applyActionMenu.style.left = "0px";
  state.applyActionMenu.style.top = "0px";
  state.applyActionMenu.style.minWidth = `${Math.max(triggerRect.width, 176)}px`;
  const menuRect = state.applyActionMenu.getBoundingClientRect();
  const maxLeft = Math.max(8, window.innerWidth - menuRect.width - 8);
  const maxTop = Math.max(8, window.innerHeight - menuRect.height - 8);
  state.applyActionMenu.style.left = `${Math.min(triggerRect.left, maxLeft)}px`;
  state.applyActionMenu.style.top = `${Math.min(triggerRect.bottom + 6, maxTop)}px`;
}

function showApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || !state.actionMenuButton || state.actionMenuButton.disabled) return;
  if (!state.applyButtons.size) return;
  state.applyActionMenu.hidden = false;
  state.actionMenuButton.setAttribute("aria-expanded", "true");
  positionApplyActionsMenu(state);
}

function toggleApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || state.applyActionMenu.hidden) {
    showApplyActionsMenu(state);
    return;
  }
  hideApplyActionsMenu(state);
}

function renderApplyActions(state) {
  state.applyButtons.clear();
  state.applyActionMenu.innerHTML = "";
  const actions = state.applyActions.length
    ? state.applyActions
    : [];
  actions.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dataSharingReviewPage__actionMenuItem";
    button.id = action.controlId;
    button.setAttribute("role", "menuitem");
    button.dataset.dataSharingApplyAction = action.id;
    button.textContent = action.label;
    button.disabled = true;
    button.title = action.status === "active"
      ? normalizeText(action.title)
      : (action.unavailableTitle || scopeUnavailableMessage(state));
    state.applyActionMenu.appendChild(button);
    state.applyButtons.set(action.id, button);
  });
  hideApplyActionsMenu(state);
}

function updateScopeUrl(scope, domains = WORKFLOW_SCOPES) {
  const nextScope = normalizeText(scope).toLowerCase();
  if (!domains.some((item) => item.key === nextScope)) return;
  const scopeParam = workflowScopeParamForKey(domains, nextScope);
  const url = new URL(window.location.href);
  if (nextScope === DEFAULT_SCOPE) {
    url.searchParams.delete("scope");
  } else {
    url.searchParams.set("scope", scopeParam);
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
  renderDataSharingReviewPreviewList(state);
  updateSelectionSummary(state);
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


function updateSelectionSummary(state) {
  updateDataSharingReviewSelectionSummary(state);
  syncApplyActionState(state);
}

function handlePreviewListChange(state, event) {
  if (!updateDataSharingReviewSelectionFromChange(state, event)) return;
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
  state.previewRows = failed ? [] : buildDataSharingReviewPreviewRows(state, payload);
  state.selectedPreviewIds.clear();
  renderDataSharingReviewPreviewList(state);
  updateSelectionSummary(state);
  state.lastImportResult = failed ? null : result;
  showDataSharingReviewResultModal(state, result, { restoreFocus: state.previewButton });
}

function setControlsDisabled(state, disabled) {
  const supportsApply = scopeSupportsSourceApply(state);
  const selectedRecordCount = selectedDataSharingReviewRecordIndices(state).length;
  const disableApplyMenu = disabled || !supportsApply || !state.serviceAvailable || !state.applyButtons.size;
  state.fileSelect.disabled = disabled || !state.files.length;
  state.previewButton.disabled = disabled || !state.serviceAvailable || !state.files.length;
  state.selectAllButton.disabled = disabled || !state.previewRows.length;
  state.clearButton.disabled = disabled || !state.previewRows.length;
  state.actionMenuButton.disabled = disableApplyMenu;
  if (disableApplyMenu) hideApplyActionsMenu(state);
  state.applyButtons.forEach((button, actionId) => {
    const action = state.applyActions.find((item) => item.id === actionId);
    const disabledForSelection = !selectedRecordCount;
    button.disabled = disabled || !supportsApply || !action || action.status !== "active" || !state.serviceAvailable || disabledForSelection;
    button.title = disabledForSelection
      ? (action && action.selectionRequiredMessage) || getStudioText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
      : normalizeText(action && action.title);
  });
}

function syncApplyActionState(state) {
  const supportsApply = scopeSupportsSourceApply(state);
  const selectedRecordCount = selectedDataSharingReviewRecordIndices(state).length;
  const disableApplyMenu = state.isRunning || !supportsApply || !state.serviceAvailable || !state.applyButtons.size;
  state.actionMenuButton.disabled = disableApplyMenu;
  if (disableApplyMenu) hideApplyActionsMenu(state);
  state.applyButtons.forEach((button, actionId) => {
    const action = state.applyActions.find((item) => item.id === actionId);
    const disabledForSelection = !selectedRecordCount;
    button.disabled = state.isRunning || !supportsApply || !action || action.status !== "active" || !state.serviceAvailable || disabledForSelection;
    button.title = disabledForSelection
      ? (action && action.selectionRequiredMessage) || getStudioText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
      : normalizeText(action && action.title);
  });
  if (state.applyActionMenu && !state.applyActionMenu.hidden) positionApplyActionsMenu(state);
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

function selectedFileName(state) {
  const file = selectedFile(state);
  return normalizeText(file && file.filename);
}

function countValue(counts, row) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const key = normalizeText(row && row.key);
  if (!key) return "";
  const fallbackKey = normalizeText(row && row.fallback_key);
  return Number(safeCounts[key] || (fallbackKey ? safeCounts[fallbackKey] : 0) || 0);
}

function actionCountRows(action, counts) {
  if (!action.countRows.length) {
    const safeCounts = counts && typeof counts === "object" ? counts : {};
    return Object.keys(safeCounts).map((key) => ({
      label: key.replace(/_/g, " "),
      value: Number(safeCounts[key] || 0)
    }));
  }
  return action.countRows.map((row) => ({
    label: normalizeText(row && row.label) || normalizeText(row && row.key),
    value: countValue(counts, row)
  })).filter((row) => row.label);
}

function actionCountsText(action, counts) {
  const template = normalizeText(action.countText);
  if (!template) return "";
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return template.replace(/\{([^}]+)\}/g, (_match, key) => String(Number(safeCounts[normalizeText(key)] || 0)));
}

function actionChangeCount(action, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  const key = action.noChangeCountKey || (action.countRows[0] && normalizeText(action.countRows[0].key)) || "updates";
  return Number(safeCounts[key] || 0);
}

function renderApplyActionResult(state, action, payload) {
  const countsValue = actionCountsText(action, payload && payload.counts);
  const summary = normalizeText(payload && payload.summary_text);
  showDataSharingReviewResultModal(state, {
    title: action.resultTitle || getStudioText(state.config, "data_sharing_review.apply_result_title", "Apply complete"),
    summary: `${summary} ${countsValue}`.trim(),
    countRows: actionCountRows(action, payload && payload.counts),
    issues: applyIssues(payload || {}, action.id)
  }, {
    restoreFocus: state.actionMenuButton
  });
}

function actionActivityContext(state, action, stagedFilename) {
  const controlSelector = normalizeText(action.controlSelector) || `#${action.controlId}`;
  return buildStudioActivityContext({
    pageId: "data-sharing-review",
    actionId: action.activityActionId,
    route: "/studio/data-sharing/review/",
    controlId: action.controlId,
    controlSelector,
    recordIdField: "staged_filename",
    recordId: stagedFilename
  });
}

async function runApplyAction(state, actionId) {
  if (!state.serviceAvailable || state.isRunning) return;
  const action = state.applyActions.find((item) => item.id === actionId);
  if (!action || action.status !== "active") return;
  hideResultButton(state);
  const stagedFilename = selectedFileName(state);
  const recordIndices = selectedDataSharingReviewRecordIndices(state);
  if (!stagedFilename || !recordIndices.length) {
    setStatus(
      state.statusNode,
      "error",
      action.selectionRequiredMessage || getStudioText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
    );
    return;
  }

  state.isRunning = true;
  setControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    action.preflightStatus || getStudioText(state.config, "data_sharing_review.apply_preflight_status", "Checking selected rows...")
  );

  try {
    const preflight = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: action.id,
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: false
    });
    const countsTextValue = actionCountsText(action, preflight.counts);
    if (!preflight.ok || actionChangeCount(action, preflight.counts) < 1) {
      setStatus(state.statusNode, preflight.ok ? "warn" : "error", preflight.summary_text || countsTextValue);
      renderApplyActionResult(state, action, preflight);
      return;
    }

    const confirm = await confirmDataSharingReviewApply(state, action, preflight, countsTextValue);
    if (!confirm.confirmed) {
      setStatus(
        state.statusNode,
        "",
        action.cancelledStatus || getStudioText(state.config, "data_sharing_review.apply_cancelled", "Apply cancelled.")
      );
      return;
    }

    setStatus(
      state.statusNode,
      "",
      action.runningStatus || getStudioText(state.config, "data_sharing_review.apply_running_status", "Applying selected changes...")
    );
    const applied = await postJson(DATA_SHARING_ENDPOINTS.apply, {
      data_domain: state.scope,
      operation: "apply",
      apply_action: action.id,
      staged_filename: stagedFilename,
      record_indices: recordIndices,
      confirm: true,
      activity_context: actionActivityContext(state, action, stagedFilename)
    });
    renderApplyActionResult(state, action, applied);
    setStatus(
      state.statusNode,
      "success",
      applied.summary_text || action.successStatus || getStudioText(state.config, "data_sharing_review.apply_success", "Changes applied.")
    );
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    const message = normalizeText(payload.summary_text) || normalizeText(error && error.message)
      || action.failedStatus || getStudioText(state.config, "data_sharing_review.apply_failed", "Apply failed.");
    renderApplyActionResult(state, action, { ...payload, summary_text: message });
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
    adapterRegistry: null,
    applyCapability: null,
    applyActions: [],
    applyButtons: new Map(),
    scopeLabelNode: document.getElementById("dataSharingReviewScopeLabel"),
    scopeSelect: document.getElementById("dataSharingReviewScopeSelect"),
    fileLabelNode: document.getElementById("dataSharingReviewFileLabel"),
    fileSelect: document.getElementById("dataSharingReviewFileSelect"),
    previewButton: document.getElementById("dataSharingReviewRun"),
    applyActionContainer: document.getElementById("dataSharingReviewApplyActions"),
    actionMenuButton: document.getElementById("dataSharingReviewActionsButton"),
    applyActionMenu: document.getElementById("dataSharingReviewActionsMenu"),
    statusNode: document.getElementById("dataSharingReviewStatus"),
    resultButton: document.getElementById("dataSharingReviewResults"),
    selectionSummary: document.getElementById("dataSharingReviewSelectionSummary"),
    selectAllButton: document.getElementById("dataSharingReviewSelectAll"),
    clearButton: document.getElementById("dataSharingReviewClear"),
    listNode: document.getElementById("dataSharingReviewList"),
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
    state.applyActionContainer,
    state.actionMenuButton,
    state.applyActionMenu,
    state.statusNode,
    state.resultButton,
    state.selectionSummary,
    state.selectAllButton,
    state.clearButton,
    state.listNode
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadStudioConfigWithText("data_sharing_review");
    const adapterRegistry = await loadAdapterRegistry(state.config);
    state.adapterRegistry = adapterRegistry;
    state.workflowScopes = workflowDomainsForOperation(adapterRegistry, "list_returned", WORKFLOW_SCOPES);
    state.scope = workflowScopeFromUrl(state.workflowScopes);
    state.applyCapability = workflowCapabilityForOperation(adapterRegistry, "apply", state.scope);
    state.applyActions = applyActionsForCapability(state.applyCapability && state.applyCapability.capability)
      .filter((action) => action.status === "active");
    renderScopeSelect(state);
    renderApplyActions(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());

    setText(state.scopeLabelNode, getStudioText(state.config, "data_sharing_review.scope_label", "scope"));
    setText(state.fileLabelNode, getStudioText(state.config, "data_sharing_review.file_label", "staged file"));
    setText(state.previewButton, getStudioText(state.config, "data_sharing_review.preview_button", "Review package"));
    setText(state.actionMenuButton, getStudioText(state.config, "data_sharing_review.actions_button", "Actions"));
    setText(state.resultButton, getStudioText(state.config, "data_sharing_review.result_button", "results"));
    setText(state.selectAllButton, getStudioText(state.config, "data_sharing_review.select_all", "select all"));
    setText(state.clearButton, getStudioText(state.config, "data_sharing_review.clear", "clear"));
    if (!scopeSupportsSourceApply(state)) {
      const unsupportedApplyTitle = getStudioText(
        state.config,
        "data_sharing_review.apply_unsupported_title",
        "{scope_label} source apply actions are not implemented yet.",
        { scope_label: scopeTitle(state) }
      );
      state.applyButtons.forEach((button) => {
        button.title = unsupportedApplyTitle;
      });
    }
    renderDataSharingReviewPreviewList(state);
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
    state.actionMenuButton.addEventListener("click", () => {
      toggleApplyActionsMenu(state);
    });
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Node ? event.target : null;
      if (!target || state.applyActionContainer.contains(target)) return;
      hideApplyActionsMenu(state);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") hideApplyActionsMenu(state);
    });
    window.addEventListener("scroll", () => hideApplyActionsMenu(state), { passive: true });
    window.addEventListener("resize", () => hideApplyActionsMenu(state));
    state.resultButton.addEventListener("click", () => {
      if (state.lastImportResult) showDataSharingReviewResultModal(state, state.lastImportResult, { restoreFocus: state.resultButton });
    });
    state.selectAllButton.addEventListener("click", () => {
      selectableDataSharingReviewPreviewIds(state).forEach((rowId) => state.selectedPreviewIds.add(rowId));
      syncDataSharingReviewPreviewCheckboxes(state);
      updateSelectionSummary(state);
    });
    state.clearButton.addEventListener("click", () => {
      state.selectedPreviewIds.clear();
      syncDataSharingReviewPreviewCheckboxes(state);
      updateSelectionSummary(state);
    });
    state.listNode.addEventListener("change", (event) => handlePreviewListChange(state, event));
    state.applyActionContainer.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target.closest("[data-data-sharing-apply-action]") : null;
      if (!(target instanceof HTMLButtonElement)) return;
      const actionId = normalizeText(target.dataset.dataSharingApplyAction);
      hideApplyActionsMenu(state);
      runApplyAction(state, actionId).catch((error) => console.warn("data_sharing_review: unexpected apply failure", error));
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
