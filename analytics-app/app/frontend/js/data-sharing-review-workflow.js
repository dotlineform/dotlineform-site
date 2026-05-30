import { getAnalyticsText } from "./analytics-config.js";
import {
  renderDataSharingReviewPreviewList,
  selectableDataSharingReviewPreviewIds,
  selectedDataSharingReviewRecordIndices,
  syncDataSharingReviewPreviewCheckboxes,
  updateDataSharingReviewSelectionFromChange,
  updateDataSharingReviewSelectionSummary
} from "./data-sharing-review-render.js";
import {
  workflowDomainForKey,
  workflowDomainFromUrl,
  workflowScopeParamForKey
} from "./data-sharing-adapters.js";

export const DEFAULT_DATA_SHARING_REVIEW_SCOPE = "library";
export const DATA_SHARING_REVIEW_SCOPES = [
  { key: "library", labelKey: "scope_library", fallback: "library" },
  { key: "tags", labelKey: "scope_tags", fallback: "tags" }
];

export function normalizeDataSharingReviewText(value) {
  return String(value == null ? "" : value).trim();
}

export function escapeDataSharingReviewHtml(value) {
  return normalizeDataSharingReviewText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function workflowScopeFromDataSharingReviewUrl(domains = DATA_SHARING_REVIEW_SCOPES) {
  return workflowDomainFromUrl(domains, DEFAULT_DATA_SHARING_REVIEW_SCOPE);
}

export function dataSharingReviewScopeSupportsApply(state) {
  return state.applyActions.some((action) => action.status === "active");
}

export function dataSharingReviewScopeLabel(state, scope = state.scope) {
  const item = workflowDomainForKey(state.workflowScopes, scope) || DATA_SHARING_REVIEW_SCOPES[0];
  if (item.labelKey) return getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback);
  return normalizeDataSharingReviewText(item.label) || item.fallback || scope;
}

export function dataSharingReviewScopeTitle(state, scope = state.scope) {
  const label = dataSharingReviewScopeLabel(state, scope);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : scope;
}

export function dataSharingReviewApplyActionsForCapability(capability) {
  const rawActions = Array.isArray(capability && capability.apply_actions) ? capability.apply_actions : [];
  return rawActions.map(normalizeApplyAction).filter(Boolean);
}

export function renderDataSharingReviewScopeSelect(state) {
  state.scopeSelect.innerHTML = state.workflowScopes.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback)
      : (normalizeDataSharingReviewText(item.label) || item.fallback);
    const selected = item.key === state.scope ? " selected" : "";
    return `<option value="${escapeDataSharingReviewHtml(item.key)}"${selected}>${escapeDataSharingReviewHtml(label)}</option>`;
  }).join("");
}

export function hideDataSharingReviewApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || !state.actionMenuButton) return;
  state.applyActionMenu.hidden = true;
  state.applyActionMenu.style.left = "";
  state.applyActionMenu.style.top = "";
  state.applyActionMenu.style.minWidth = "";
  state.actionMenuButton.setAttribute("aria-expanded", "false");
}

export function positionDataSharingReviewApplyActionsMenu(state) {
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

export function showDataSharingReviewApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || !state.actionMenuButton || state.actionMenuButton.disabled) return;
  if (!state.applyButtons.size) return;
  state.applyActionMenu.hidden = false;
  state.actionMenuButton.setAttribute("aria-expanded", "true");
  positionDataSharingReviewApplyActionsMenu(state);
}

export function toggleDataSharingReviewApplyActionsMenu(state) {
  if (!state || !state.applyActionMenu || state.applyActionMenu.hidden) {
    showDataSharingReviewApplyActionsMenu(state);
    return;
  }
  hideDataSharingReviewApplyActionsMenu(state);
}

export function renderDataSharingReviewApplyActions(state) {
  state.applyButtons.clear();
  state.applyActionMenu.innerHTML = "";
  const actions = state.applyActions.length ? state.applyActions : [];
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
      ? normalizeDataSharingReviewText(action.title)
      : (action.unavailableTitle || dataSharingReviewScopeUnavailableMessage(state));
    state.applyActionMenu.appendChild(button);
    state.applyButtons.set(action.id, button);
  });
  hideDataSharingReviewApplyActionsMenu(state);
}

export function updateDataSharingReviewScopeUrl(scope, domains = DATA_SHARING_REVIEW_SCOPES) {
  const nextScope = normalizeDataSharingReviewText(scope).toLowerCase();
  if (!domains.some((item) => item.key === nextScope)) return;
  const scopeParam = workflowScopeParamForKey(domains, nextScope);
  const url = new URL(window.location.href);
  if (nextScope === DEFAULT_DATA_SHARING_REVIEW_SCOPE) {
    url.searchParams.delete("scope");
  } else {
    url.searchParams.set("scope", scopeParam);
  }
  window.location.href = url.toString();
}

export function dataSharingReviewScopeUnavailableMessage(state) {
  const domain = workflowDomainForKey(state.workflowScopes, state.scope);
  return normalizeDataSharingReviewText(domain && domain.message)
    || getAnalyticsText(
      state.config,
      "data_sharing_review.scope_unsupported",
      "{scope_label} returned-package review is not implemented yet.",
      { scope_label: dataSharingReviewScopeTitle(state) }
    );
}

export function selectedDataSharingReviewFile(state) {
  const filename = normalizeDataSharingReviewText(state.fileSelect.value);
  return state.files.find((file) => normalizeDataSharingReviewText(file.filename) === filename) || null;
}

export function resetDataSharingReviewResult(state) {
  state.selectedPreviewIds.clear();
  state.previewRows = [];
  renderDataSharingReviewPreviewList(state);
  updateDataSharingReviewSelectionState(state);
}

export function hideDataSharingReviewResultButton(state) {
  if (!state || !state.resultButton) return;
  state.resultButton.hidden = true;
}

export function maybeShowDataSharingReviewResultButton(state, summary) {
  if (!state || !state.resultButton || !state.lastImportResult) return;
  const currentSummary = normalizeDataSharingReviewText(summary);
  state.resultButton.hidden = !currentSummary || currentSummary !== state.lastImportResult.summary;
}

export function updateDataSharingReviewSelectionState(state) {
  updateDataSharingReviewSelectionSummary(state);
  syncDataSharingReviewApplyActionState(state);
}

export function handleDataSharingReviewPreviewListChange(state, event) {
  if (!updateDataSharingReviewSelectionFromChange(state, event)) return;
  updateDataSharingReviewSelectionState(state);
}

export function selectAllDataSharingReviewPreviewRows(state) {
  selectableDataSharingReviewPreviewIds(state).forEach((rowId) => state.selectedPreviewIds.add(rowId));
  syncDataSharingReviewPreviewCheckboxes(state);
  updateDataSharingReviewSelectionState(state);
}

export function clearDataSharingReviewPreviewSelection(state) {
  state.selectedPreviewIds.clear();
  syncDataSharingReviewPreviewCheckboxes(state);
  updateDataSharingReviewSelectionState(state);
}

export function setDataSharingReviewControlsDisabled(state, disabled) {
  const supportsApply = dataSharingReviewScopeSupportsApply(state);
  const selectedRecordCount = selectedDataSharingReviewRecordIndices(state).length;
  const disableApplyMenu = disabled || !supportsApply || !state.serviceAvailable || !state.applyButtons.size;
  state.fileSelect.disabled = disabled || !state.files.length;
  state.previewButton.disabled = disabled || !state.serviceAvailable || !state.files.length;
  state.selectAllButton.disabled = disabled || !state.previewRows.length;
  state.clearButton.disabled = disabled || !state.previewRows.length;
  state.actionMenuButton.disabled = disableApplyMenu;
  if (disableApplyMenu) hideDataSharingReviewApplyActionsMenu(state);
  state.applyButtons.forEach((button, actionId) => {
    const action = state.applyActions.find((item) => item.id === actionId);
    const disabledForSelection = !selectedRecordCount;
    button.disabled = disabled || !supportsApply || !action || action.status !== "active" || !state.serviceAvailable || disabledForSelection;
    button.title = disabledForSelection
      ? (action && action.selectionRequiredMessage) || getAnalyticsText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
      : normalizeDataSharingReviewText(action && action.title);
  });
}

export function syncDataSharingReviewApplyActionState(state) {
  const supportsApply = dataSharingReviewScopeSupportsApply(state);
  const selectedRecordCount = selectedDataSharingReviewRecordIndices(state).length;
  const disableApplyMenu = state.isRunning || !supportsApply || !state.serviceAvailable || !state.applyButtons.size;
  state.actionMenuButton.disabled = disableApplyMenu;
  if (disableApplyMenu) hideDataSharingReviewApplyActionsMenu(state);
  state.applyButtons.forEach((button, actionId) => {
    const action = state.applyActions.find((item) => item.id === actionId);
    const disabledForSelection = !selectedRecordCount;
    button.disabled = state.isRunning || !supportsApply || !action || action.status !== "active" || !state.serviceAvailable || disabledForSelection;
    button.title = disabledForSelection
      ? (action && action.selectionRequiredMessage) || getAnalyticsText(state.config, "data_sharing_review.apply_selection_required", "Select at least one review row.")
      : normalizeDataSharingReviewText(action && action.title);
  });
  if (state.applyActionMenu && !state.applyActionMenu.hidden) positionDataSharingReviewApplyActionsMenu(state);
}

function normalizeId(value) {
  return normalizeDataSharingReviewText(value).toLowerCase();
}

function actionUi(action) {
  return action && action.ui && typeof action.ui === "object" ? action.ui : {};
}

function actionResult(action) {
  return action && action.result && typeof action.result === "object" ? action.result : {};
}

function normalizeApplyAction(action, index) {
  if (!action || typeof action !== "object") return null;
  const id = normalizeDataSharingReviewText(action.id);
  if (!id) return null;
  const ui = actionUi(action);
  return {
    ...action,
    id,
    status: normalizeId(action.status) || "active",
    label: normalizeDataSharingReviewText(action.label) || id,
    controlId: normalizeDataSharingReviewText(ui.control_id) || `dataSharingReviewApplyAction${index + 1}`,
    controlSelector: normalizeDataSharingReviewText(ui.control_selector) || "",
    activityActionId: normalizeDataSharingReviewText(ui.activity_action_id) || `apply-returned-${id.replace(/_/g, "-")}`,
    selectionRequiredMessage: normalizeDataSharingReviewText(ui.selection_required_message),
    preflightStatus: normalizeDataSharingReviewText(ui.preflight_status),
    runningStatus: normalizeDataSharingReviewText(ui.running_status),
    cancelledStatus: normalizeDataSharingReviewText(ui.cancelled_status),
    successStatus: normalizeDataSharingReviewText(ui.success_status),
    failedStatus: normalizeDataSharingReviewText(ui.failed_status),
    unavailableTitle: normalizeDataSharingReviewText(ui.unavailable_title),
    noChangeCountKey: normalizeDataSharingReviewText(ui.no_change_count_key),
    resultTitle: normalizeDataSharingReviewText(actionResult(action).title),
    countText: normalizeDataSharingReviewText(actionResult(action).count_text),
    countRows: Array.isArray(actionResult(action).count_rows) ? actionResult(action).count_rows : []
  };
}
