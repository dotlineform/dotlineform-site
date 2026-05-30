import { getAnalyticsDataPath, getAnalyticsText, loadAnalyticsConfigWithText } from "./analytics-config.js";
import {
  DATA_SHARING_ENDPOINTS,
  configureAnalyticsTransport,
  getJson,
  postJson,
  probeDataSharingHealth
} from "./analytics-transport.js";
import {
  initializeAnalyticsRouteState,
  setAnalyticsRouteBusy,
  setAnalyticsRouteReady
} from "./analytics-route-state.js";
import {
  showDataSharingReviewResultModal
} from "./data-sharing-review-modals.js";
import { runDataSharingReviewApplyAction } from "./data-sharing-review-apply.js";
import {
  buildDataSharingReviewPreviewRows,
  renderDataSharingReviewPreviewList
} from "./data-sharing-review-render.js";
import {
  workflowCapabilityForOperation,
  workflowDomainIsActive,
  workflowDomainsForOperation
} from "./data-sharing-adapters.js";
import {
  DATA_SHARING_REVIEW_SCOPES,
  clearDataSharingReviewPreviewSelection,
  dataSharingReviewApplyActionsForCapability,
  dataSharingReviewScopeLabel,
  dataSharingReviewScopeSupportsApply,
  dataSharingReviewScopeTitle,
  dataSharingReviewScopeUnavailableMessage,
  escapeDataSharingReviewHtml,
  handleDataSharingReviewPreviewListChange,
  hideDataSharingReviewApplyActionsMenu,
  hideDataSharingReviewResultButton,
  maybeShowDataSharingReviewResultButton,
  normalizeDataSharingReviewText,
  renderDataSharingReviewApplyActions,
  renderDataSharingReviewScopeSelect,
  resetDataSharingReviewResult,
  selectAllDataSharingReviewPreviewRows,
  selectedDataSharingReviewFile,
  setDataSharingReviewControlsDisabled,
  toggleDataSharingReviewApplyActionsMenu,
  updateDataSharingReviewScopeUrl,
  updateDataSharingReviewSelectionState,
  workflowScopeFromDataSharingReviewUrl
} from "./data-sharing-review-workflow.js";

function normalizeText(value) {
  return normalizeDataSharingReviewText(value);
}

function escapeHtml(value) {
  return escapeDataSharingReviewHtml(value);
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

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function loadAdapterRegistry(config) {
  const registryPath = getAnalyticsDataPath(config, "data_sharing_adapters")
    || "/data-sharing/config/adapters.json";
  return loadJson(registryPath);
}

function routeModeForState(state) {
  if (state.previewRows && state.previewRows.length) {
    return "result";
  }
  return "selection";
}

function routeStateDetail(state) {
  if (state && state.root) state.root.dataset.analyticsScope = state.scope;
  return {
    route: "data-sharing-review",
    mode: routeModeForState(state),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.files && state.files.length)
  };
}

function syncRouteBusyState(state) {
  setAnalyticsRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setAnalyticsRouteReady(state.root, ready, routeStateDetail(state));
}

function previewCountRows(state, counts) {
  const safeCounts = counts && typeof counts === "object" ? counts : {};
  return [
    {
      label: getAnalyticsText(state.config, "data_sharing_review.count_records", "records"),
      value: Number(safeCounts.records || 0)
    },
    {
      label: getAnalyticsText(state.config, "data_sharing_review.count_parsed", "parsed"),
      value: Number(safeCounts.parsed_records || 0)
    },
    {
      label: getAnalyticsText(state.config, "data_sharing_review.count_malformed", "malformed"),
      value: Number(safeCounts.malformed_records || 0)
    },
    {
      label: getAnalyticsText(state.config, "data_sharing_review.count_warnings", "warnings"),
      value: Number(safeCounts.warnings || 0)
    },
    {
      label: getAnalyticsText(state.config, "data_sharing_review.count_errors", "errors"),
      value: Number(safeCounts.errors || 0)
    }
  ];
}

function renderResult(state, payload, failed = false) {
  const result = {
    title: getAnalyticsText(
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
  updateDataSharingReviewSelectionState(state);
  state.lastImportResult = failed ? null : result;
  showDataSharingReviewResultModal(state, result, { restoreFocus: state.previewButton });
}

async function loadImportFiles(scope) {
  const url = `${DATA_SHARING_ENDPOINTS.returnedPackages}?data_domain=${encodeURIComponent(scope)}`;
  const payload = await getJson(url);
  return Array.isArray(payload.files) ? payload.files : [];
}

async function runPreview(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedDataSharingReviewFile(state);
  if (!file) {
    hideDataSharingReviewResultButton(state);
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(state.config, "data_sharing_review.file_required", "Select a staged data file first.")
    );
    return;
  }

  resetDataSharingReviewResult(state);
  hideDataSharingReviewResultButton(state);
  state.isRunning = true;
  setDataSharingReviewControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getAnalyticsText(state.config, "data_sharing_review.running_status", "Generating returned package reviews...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.review, {
      data_domain: state.scope,
      operation: "review",
      staged_filename: file.filename
    });
    renderResult(state, payload, false);
    const successMessage = payload.summary_text || getAnalyticsText(state.config, "data_sharing_review.status_success", "Returned package reviews generated.");
    setStatus(
      state.statusNode,
      "success",
      successMessage
    );
    maybeShowDataSharingReviewResultButton(state, successMessage);
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    renderResult(state, payload, true);
    hideDataSharingReviewResultButton(state);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || getAnalyticsText(state.config, "data_sharing_review.status_failed", "Returned package review failed.")
    );
  } finally {
    state.isRunning = false;
    setDataSharingReviewControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

async function init() {
  const bootStatus = document.getElementById("dataSharingReviewBootStatus");
  const root = document.getElementById("dataSharingReviewRoot");
  if (!bootStatus || !root) return;
  initializeAnalyticsRouteState(root, { route: "data-sharing-review", mode: "selection" });

  const state = {
    bootStatus,
    root,
    scope: workflowScopeFromDataSharingReviewUrl(),
    workflowScopes: DATA_SHARING_REVIEW_SCOPES,
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
    state.config = await loadAnalyticsConfigWithText("data_sharing_review");
    configureAnalyticsTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry(state.config);
    state.adapterRegistry = adapterRegistry;
    state.workflowScopes = workflowDomainsForOperation(adapterRegistry, "list_returned", DATA_SHARING_REVIEW_SCOPES);
    state.scope = workflowScopeFromDataSharingReviewUrl(state.workflowScopes);
    state.applyCapability = workflowCapabilityForOperation(adapterRegistry, "apply", state.scope);
    state.applyActions = dataSharingReviewApplyActionsForCapability(state.applyCapability && state.applyCapability.capability)
      .filter((action) => action.status === "active");
    renderDataSharingReviewScopeSelect(state);
    renderDataSharingReviewApplyActions(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());

    setText(state.scopeLabelNode, getAnalyticsText(state.config, "data_sharing_review.scope_label", "scope"));
    setText(state.fileLabelNode, getAnalyticsText(state.config, "data_sharing_review.file_label", "staged file"));
    setText(state.previewButton, getAnalyticsText(state.config, "data_sharing_review.preview_button", "Review package"));
    setText(state.actionMenuButton, getAnalyticsText(state.config, "data_sharing_review.actions_button", "Actions"));
    setText(state.resultButton, getAnalyticsText(state.config, "data_sharing_review.result_button", "results"));
    setText(state.selectAllButton, getAnalyticsText(state.config, "data_sharing_review.select_all", "select all"));
    setText(state.clearButton, getAnalyticsText(state.config, "data_sharing_review.clear", "clear"));
    if (!dataSharingReviewScopeSupportsApply(state)) {
      const unsupportedApplyTitle = getAnalyticsText(
        state.config,
        "data_sharing_review.apply_unsupported_title",
        "{scope_label} source apply actions are not implemented yet.",
        { scope_label: dataSharingReviewScopeTitle(state) }
      );
      state.applyButtons.forEach((button) => {
        button.title = unsupportedApplyTitle;
      });
    }
    renderDataSharingReviewPreviewList(state);
    updateDataSharingReviewSelectionState(state);
    setDataSharingReviewControlsDisabled(state, true);

    root.hidden = false;
    bootStatus.hidden = true;

    state.scopeSelect.addEventListener("change", () => updateDataSharingReviewScopeUrl(state.scopeSelect.value, state.workflowScopes));

    if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
      setDataSharingReviewControlsDisabled(state, true);
      setStatus(state.statusNode, "warn", dataSharingReviewScopeUnavailableMessage(state));
      markRouteReady(state, true);
      return;
    }

    if (!state.serviceAvailable) {
      setDataSharingReviewControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "error",
        getAnalyticsText(
          state.config,
          "data_sharing_review.service_unavailable",
          "Studio Data Sharing API unavailable. Restart Local Studio to review {scope_label} returned packages.",
          { scope_label: dataSharingReviewScopeLabel(state) }
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.files = await loadImportFiles(state.scope);
    if (!state.files.length) {
      setDataSharingReviewControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "warn",
        getAnalyticsText(
          state.config,
          "data_sharing_review.no_files",
          "No staged {scope_label} data files found under var/analytics/data-sharing/{scope}/import-staging/.",
          { scope_label: dataSharingReviewScopeLabel(state), scope: state.scope }
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.fileSelect.innerHTML = state.files.map((file) => {
      const filename = normalizeText(file.filename);
      return `<option value="${escapeHtml(filename)}">${escapeHtml(filename)}</option>`;
    }).join("");
    setDataSharingReviewControlsDisabled(state, false);
    setStatus(
      state.statusNode,
      "",
      getAnalyticsText(
        state.config,
        "data_sharing_review.idle_status",
        "Select a staged {scope_label} data file and generate previews.",
        { scope_label: dataSharingReviewScopeLabel(state) }
      )
    );
    markRouteReady(state, true);

    state.fileSelect.addEventListener("change", () => {
      resetDataSharingReviewResult(state);
      state.lastImportResult = null;
      hideDataSharingReviewResultButton(state);
      setDataSharingReviewControlsDisabled(state, false);
      setStatus(
        state.statusNode,
        "",
        getAnalyticsText(
          state.config,
          "data_sharing_review.idle_status",
          "Select a staged {scope_label} data file and generate previews.",
          { scope_label: dataSharingReviewScopeLabel(state) }
        )
      );
      syncRouteBusyState(state);
    });
    state.previewButton.addEventListener("click", () => {
      runPreview(state).catch((error) => console.warn("data_sharing_review: unexpected preview failure", error));
    });
    state.actionMenuButton.addEventListener("click", () => {
      toggleDataSharingReviewApplyActionsMenu(state);
    });
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Node ? event.target : null;
      if (!target || state.applyActionContainer.contains(target)) return;
      hideDataSharingReviewApplyActionsMenu(state);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") hideDataSharingReviewApplyActionsMenu(state);
    });
    window.addEventListener("scroll", () => hideDataSharingReviewApplyActionsMenu(state), { passive: true });
    window.addEventListener("resize", () => hideDataSharingReviewApplyActionsMenu(state));
    state.resultButton.addEventListener("click", () => {
      if (state.lastImportResult) showDataSharingReviewResultModal(state, state.lastImportResult, { restoreFocus: state.resultButton });
    });
    state.selectAllButton.addEventListener("click", () => {
      selectAllDataSharingReviewPreviewRows(state);
    });
    state.clearButton.addEventListener("click", () => {
      clearDataSharingReviewPreviewSelection(state);
    });
    state.listNode.addEventListener("change", (event) => handleDataSharingReviewPreviewListChange(state, event));
    state.applyActionContainer.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target.closest("[data-data-sharing-apply-action]") : null;
      if (!(target instanceof HTMLButtonElement)) return;
      const actionId = normalizeText(target.dataset.dataSharingApplyAction);
      hideDataSharingReviewApplyActionsMenu(state);
      runDataSharingReviewApplyAction(state, actionId, {
        setControlsDisabled: setDataSharingReviewControlsDisabled,
        syncRouteBusyState
      }).catch((error) => console.warn("data_sharing_review: unexpected apply failure", error));
    });
  } catch (error) {
    console.warn("data_sharing_review: init failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    state.serviceAvailable = false;
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(
        state.config || {},
        "data_sharing_review.load_failed",
        "Failed to load {scope_label} returned package data.",
        { scope_label: state.config ? dataSharingReviewScopeTitle(state) : "Library" }
      )
    );
    markRouteReady(state, true);
  } finally {
    state.isRunning = false;
    syncRouteBusyState(state);
  }
}

init();
