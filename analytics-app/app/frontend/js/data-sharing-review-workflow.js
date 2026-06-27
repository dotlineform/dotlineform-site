import { getAnalyticsText } from "./analytics-config.js";
import {
  renderDataSharingReviewPreviewList,
  selectableDataSharingReviewPreviewIds,
  selectedDataSharingReviewRecordIndices,
  updateDataSharingReviewSelectionSummary
} from "./data-sharing-review-render.js";
import {
  dataSharingAppForDomain,
  dataSharingAppFromUrl,
  dataSharingDomainForKey,
  dataSharingDomainFromUrl,
  dataSharingDomainsForApp
} from "./data-sharing-adapters.js";

export const DEFAULT_DATA_SHARING_REVIEW_APP = "docs-viewer";
export const DEFAULT_DATA_SHARING_REVIEW_DOMAIN = "documents";
export const DATA_SHARING_REVIEW_APPS = [
  { key: "docs-viewer", labelKey: "app_docs_viewer", fallback: "Docs Viewer" },
  { key: "studio", labelKey: "app_studio", fallback: "Studio" },
  { key: "analytics", labelKey: "app_analytics", fallback: "Analytics" }
];
export const DATA_SHARING_REVIEW_DOMAINS = [
  { key: "documents", app: "docs-viewer", labelKey: "data_domain_documents", fallback: "documents" },
  { key: "series", app: "studio", labelKey: "data_domain_series", fallback: "series" },
  { key: "works", app: "studio", labelKey: "data_domain_works", fallback: "works" },
  { key: "tags", app: "analytics", labelKey: "data_domain_tags", fallback: "tags" }
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

export function dataDomainFromDataSharingReviewUrl(domains = DATA_SHARING_REVIEW_DOMAINS) {
  return dataSharingDomainFromUrl(domains, DEFAULT_DATA_SHARING_REVIEW_DOMAIN);
}

export function dataSharingReviewDataDomainSupportsApply(state) {
  return state.applyActions.some((action) => action.status === "active");
}

export function dataSharingReviewAppLabel(state, app = state.app) {
  const normalizedApp = normalizeDataSharingReviewText(app);
  const item = (state.apps || DATA_SHARING_REVIEW_APPS).find((candidate) => candidate.key === normalizedApp);
  if (!item) return normalizedApp;
  if (item.labelKey) return getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback);
  return normalizeDataSharingReviewText(item.label) || item.fallback || normalizedApp;
}

export function dataSharingReviewDataDomainLabel(state, dataDomain = state.dataDomain) {
  const normalizedDomain = normalizeDataSharingReviewText(dataDomain);
  const item = dataSharingDomainForKey(state.dataDomains, normalizedDomain);
  if (!item) return normalizedDomain;
  if (item.labelKey) return getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback);
  return normalizeDataSharingReviewText(item.label) || item.fallback || normalizedDomain;
}

export function dataSharingReviewDataDomainTitle(state, dataDomain = state.dataDomain) {
  const label = dataSharingReviewDataDomainLabel(state, dataDomain);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : dataDomain;
}

export function dataSharingReviewApplyActionsForCapability(capability) {
  const rawActions = Array.isArray(capability && capability.apply_actions) ? capability.apply_actions : [];
  return rawActions.map(normalizeApplyAction).filter(Boolean);
}

export function renderDataSharingReviewAppSelect(state) {
  state.appSelect.innerHTML = state.apps.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback)
      : (normalizeDataSharingReviewText(item.label) || item.fallback);
    const selected = item.key === state.app ? " selected" : "";
    return `<option value="${escapeDataSharingReviewHtml(item.key)}"${selected}>${escapeDataSharingReviewHtml(label)}</option>`;
  }).join("");
}

export function renderDataSharingReviewDataDomainSelect(state) {
  const domains = dataSharingDomainsForApp(state.dataDomains, state.app);
  state.dataDomainSelect.innerHTML = domains.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_review.${item.labelKey}`, item.fallback)
      : (normalizeDataSharingReviewText(item.label) || item.fallback);
    const selected = item.key === state.dataDomain ? " selected" : "";
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
      : (action.unavailableTitle || dataSharingReviewDataDomainUnavailableMessage(state));
    state.applyActionMenu.appendChild(button);
    state.applyButtons.set(action.id, button);
  });
  hideDataSharingReviewApplyActionsMenu(state);
}

export function updateDataSharingReviewUrl(state, app, dataDomain) {
  const nextApp = normalizeDataSharingReviewText(app).toLowerCase();
  const nextDomain = normalizeDataSharingReviewText(dataDomain).toLowerCase();
  if (!state.apps.some((item) => item.key === nextApp)) return;
  if (!dataSharingDomainsForApp(state.dataDomains, nextApp).some((item) => item.key === nextDomain)) return;
  const url = new URL(window.location.href);
  if (nextApp === DEFAULT_DATA_SHARING_REVIEW_APP) {
    url.searchParams.delete("app");
  } else {
    url.searchParams.set("app", nextApp);
  }
  if (nextDomain === DEFAULT_DATA_SHARING_REVIEW_DOMAIN) {
    url.searchParams.delete("data_domain");
  } else {
    url.searchParams.set("data_domain", nextDomain);
  }
  window.location.href = url.toString();
}

export function dataSharingReviewDataDomainUnavailableMessage(state) {
  const domain = dataSharingDomainForKey(state.dataDomains, state.dataDomain);
  return normalizeDataSharingReviewText(domain && domain.message)
    || getAnalyticsText(
      state.config,
      "data_sharing_review.data_domain_unsupported",
      "{data_domain_label} returned-package review is not implemented yet.",
      { data_domain_label: dataSharingReviewDataDomainTitle(state) }
    );
}

export function dataSharingReviewAppFromUrl(apps, domains, dataDomain) {
  return dataSharingAppFromUrl(apps, dataSharingAppForDomain(domains, dataDomain, DEFAULT_DATA_SHARING_REVIEW_APP));
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

export function setDataSharingReviewControlsDisabled(state, disabled) {
  const supportsApply = dataSharingReviewDataDomainSupportsApply(state);
  const selectedFile = selectedDataSharingReviewFile(state);
  const selectedRecordCount = selectedDataSharingReviewRecordIndices(state).length;
  const selectableRecordCount = selectableDataSharingReviewPreviewIds(state).length;
  const disableApplyMenu = disabled || !supportsApply || !state.serviceAvailable || !state.applyButtons.size;
  state.fileSelect.disabled = disabled || !state.files.length;
  state.previewButton.disabled = disabled || !state.serviceAvailable || !selectedFile || !state.dataDomain;
  state.selectAllButton.disabled = disabled || !selectableRecordCount;
  state.clearButton.disabled = disabled || !state.selectedPreviewIds.size;
  if (state.selectableList) state.selectableList.update({ disabled: Boolean(disabled) });
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
  const supportsApply = dataSharingReviewDataDomainSupportsApply(state);
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
