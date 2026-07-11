import { getAnalyticsText, loadAnalyticsConfig } from "./analytics-config.js";
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
import { runDataSharingReviewApplyAction } from "./data-sharing-review-apply.js";
import {
  buildDataSharingReviewPreviewRows,
  renderDataSharingReviewPreviewList
} from "./data-sharing-review-render.js";
import {
  dataSharingAppsForDomains,
  dataSharingCapabilityForOperation,
  dataSharingDomainsForOperation
} from "./data-sharing-adapters.js";
import {
  DATA_SHARING_REVIEW_APPS,
  DATA_SHARING_REVIEW_DOMAINS,
  dataSharingReviewApplyActionsForCapability,
  dataSharingReviewAppLabel,
  dataSharingReviewDataDomainLabel,
  escapeDataSharingReviewHtml,
  hideDataSharingReviewApplyActionsMenu,
  normalizeDataSharingReviewText,
  renderDataSharingReviewApplyActions,
  resetDataSharingReviewResult,
  selectedDataSharingReviewFile,
  setDataSharingReviewControlsDisabled,
  toggleDataSharingReviewApplyActionsMenu,
  updateDataSharingReviewSelectionState
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

async function loadAdapterRegistry() {
  return getJson(DATA_SHARING_ENDPOINTS.config);
}

function routeModeForState(state) {
  if (state.previewRows && state.previewRows.length) {
    return "result";
  }
  return "selection";
}

function routeStateDetail(state) {
  if (state && state.root) {
    state.root.dataset.analyticsApp = state.app;
    state.root.dataset.analyticsDataDomain = state.dataDomain;
  }
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

function renderResult(state, payload, failed = false) {
  state.previewRows = failed ? [] : buildDataSharingReviewPreviewRows(state, payload);
  state.selectedPreviewIds.clear();
  renderDataSharingReviewPreviewList(state);
  updateDataSharingReviewSelectionState(state);
}

function sourceFolderStatusMessage(state, payload) {
  const counts = payload && payload.counts && typeof payload.counts === "object" ? payload.counts : {};
  const skipped = Number(counts.skipped_records || 0);
  const warnings = Number(counts.warnings || 0);
  const details = [];
  if (skipped > 0) details.push(`${skipped} skipped`);
  if (warnings > 0) details.push(`${warnings} ${warnings === 1 ? "warning" : "warnings"}`);
  const message = payload.summary_text || getAnalyticsText(state.config, "data_sharing_review.source_folder_success", "Import review source folder created.");
  return details.length ? `${message} ${details.join("; ")}.` : message;
}

function sourceFolderStatusState(payload) {
  const counts = payload && payload.counts && typeof payload.counts === "object" ? payload.counts : {};
  return Number(counts.skipped_records || 0) > 0 || Number(counts.warnings || 0) > 0 ? "warn" : "success";
}

const REVIEW_ACTIONS = [
  { id: "content", label: "Content" },
  { id: "summaries", label: "Summaries" },
  { id: "hierarchy", label: "Hierarchy" }
];

function positionReviewMenu(state) {
  if (!state || !state.reviewMenu || !state.previewButton) return;
  const triggerRect = state.previewButton.getBoundingClientRect();
  state.reviewMenu.style.left = "0px";
  state.reviewMenu.style.top = "0px";
  state.reviewMenu.style.minWidth = `${Math.max(triggerRect.width, 176)}px`;
  const menuRect = state.reviewMenu.getBoundingClientRect();
  const maxLeft = Math.max(8, window.innerWidth - menuRect.width - 8);
  const maxTop = Math.max(8, window.innerHeight - menuRect.height - 8);
  state.reviewMenu.style.left = `${Math.min(triggerRect.left, maxLeft)}px`;
  state.reviewMenu.style.top = `${Math.min(triggerRect.bottom + 6, maxTop)}px`;
}

function hideReviewMenu(state) {
  if (!state || !state.reviewMenu || !state.previewButton) return;
  state.reviewMenu.hidden = true;
  state.reviewMenu.style.left = "";
  state.reviewMenu.style.top = "";
  state.reviewMenu.style.minWidth = "";
  state.previewButton.setAttribute("aria-expanded", "false");
}

function showReviewMenu(state) {
  if (!state || !state.reviewMenu || !state.previewButton || state.previewButton.disabled) return;
  state.reviewMenu.hidden = false;
  state.previewButton.setAttribute("aria-expanded", "true");
  positionReviewMenu(state);
}

function toggleReviewMenu(state) {
  if (!state || !state.reviewMenu || state.reviewMenu.hidden) {
    showReviewMenu(state);
    return;
  }
  hideReviewMenu(state);
}

function renderReviewMenu(state) {
  state.reviewMenu.innerHTML = "";
  REVIEW_ACTIONS.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dataSharingReviewPage__actionMenuItem";
    button.setAttribute("role", "menuitem");
    button.dataset.dataSharingReviewAction = action.id;
    button.textContent = action.label;
    state.reviewMenu.appendChild(button);
  });
  hideReviewMenu(state);
}

function selectedFileSelection(state) {
  return state.dataDomain === "documents" && state.docsScope ? { docs_scope: state.docsScope } : {};
}

async function loadImportFiles() {
  const payload = await getJson(DATA_SHARING_ENDPOINTS.returnedPackages);
  return Array.isArray(payload.files) ? payload.files : [];
}

function resolvedMetadataValue(value) {
  return normalizeText(value) || "unresolved";
}

function setFilePickerVisible(state, visible) {
  if (!state.filePickerNode) return;
  state.filePickerNode.hidden = !visible;
}

function selectedFileIdleStatus(state) {
  const file = selectedDataSharingReviewFile(state);
  if (file && !file.metadata_ok) {
    const error = normalizeText(file.metadata_error);
    const filename = normalizeText(file.filename);
    return {
      state: "warn",
      message: error
        ? `${filename} is missing valid export metadata: ${error}`
        : `${filename} is missing valid export metadata.`
    };
  }
  return {
    state: "",
    message: getAnalyticsText(
      state.config,
      "data_sharing_review.idle_status",
      "Select a staged {data_domain_label} data file.",
      { data_domain_label: state.dataDomain ? dataSharingReviewDataDomainLabel(state) : "returned package" }
    )
  };
}

function syncSelectedFileMetadata(state) {
  const file = selectedDataSharingReviewFile(state);
  if (!file) {
    state.reviewReady = false;
    state.app = "";
    state.dataDomain = "";
    state.docsScope = "";
    state.applyCapability = null;
    state.applyActions = [];
    renderDataSharingReviewApplyActions(state);
    if (state.resolvedContextNode) state.resolvedContextNode.hidden = true;
    setText(state.appValueNode, "");
    setText(state.dataDomainValueNode, "");
    setText(state.scopeValueNode, "");
    if (state.scopeRow) state.scopeRow.hidden = true;
    syncRouteBusyState(state);
    return;
  }

  state.app = normalizeText(file && file.app).toLowerCase();
  state.dataDomain = normalizeText(file && file.data_domain).toLowerCase();
  state.docsScope = normalizeText(file && file.scope).toLowerCase();
  state.applyCapability = state.dataDomain
    ? dataSharingCapabilityForOperation(state.adapterRegistry, "apply", state.dataDomain)
    : null;
  state.applyActions = dataSharingReviewApplyActionsForCapability(state.applyCapability && state.applyCapability.capability)
    .filter((action) => action.status === "active");
  renderDataSharingReviewApplyActions(state);

  if (state.resolvedContextNode) state.resolvedContextNode.hidden = false;
  setText(state.appValueNode, state.app ? dataSharingReviewAppLabel(state, state.app) : "unresolved");
  setText(state.dataDomainValueNode, state.dataDomain ? dataSharingReviewDataDomainLabel(state, state.dataDomain) : "unresolved");
  if (state.scopeRow) {
    const showScope = state.dataDomain === "documents";
    state.scopeRow.hidden = !showScope;
    if (showScope) setText(state.scopeValueNode, resolvedMetadataValue(state.docsScope));
    if (!showScope) setText(state.scopeValueNode, "");
  }
  syncRouteBusyState(state);
}

async function loadSelectedFileRows(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedDataSharingReviewFile(state);
  state.reviewReady = false;
  if (!file || !state.dataDomain || !file.metadata_ok) {
    renderResult(state, {}, true);
    return;
  }

  state.isRunning = true;
  setDataSharingReviewControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getAnalyticsText(state.config, "data_sharing_review.records_loading_status", "Loading staged documents...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.returnedRecords, {
      data_domain: state.dataDomain,
      staged_filename: file.filename,
      selection: selectedFileSelection(state)
    });
    renderResult(state, payload, false);
    const rowCount = state.previewRows.length;
    const loadedMessage = payload.summary_text || getAnalyticsText(
      state.config,
      rowCount === 1
        ? "data_sharing_review.records_loaded_status_one"
        : "data_sharing_review.records_loaded_status",
      rowCount === 1 ? "Loaded 1 staged document." : "Loaded {count} staged documents.",
      { count: rowCount }
    );
    setStatus(state.statusNode, "success", loadedMessage);
  } catch (error) {
    const payload = error && error.payload ? error.payload : {};
    renderResult(state, payload, true);
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || getAnalyticsText(state.config, "data_sharing_review.records_load_failed", "Failed to load staged documents.")
    );
  } finally {
    state.isRunning = false;
    setDataSharingReviewControlsDisabled(state, false);
    syncRouteBusyState(state);
  }
}

async function runDocumentReview(state, reviewAction) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedDataSharingReviewFile(state);
  if (!file) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(state.config, "data_sharing_review.file_required", "Select a staged data file first.")
    );
    return;
  }
  if (!state.dataDomain) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(state.config, "data_sharing_review.metadata_required", "Selected staged file is missing valid export metadata.")
    );
    return;
  }
  state.isRunning = true;
  setDataSharingReviewControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getAnalyticsText(state.config, "data_sharing_review.running_status", "Generating document review...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.review, {
      data_domain: state.dataDomain,
      operation: "review",
      review_action: reviewAction,
      staged_filename: file.filename,
      selection: selectedFileSelection(state)
    });
    state.reviewReady = true;
    const successMessage = payload.summary_text || getAnalyticsText(state.config, "data_sharing_review.status_success", "Document review generated.");
    setStatus(
      state.statusNode,
      "success",
      successMessage
    );
  } catch (error) {
    state.reviewReady = false;
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

async function createSourceFolder(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  const file = selectedDataSharingReviewFile(state);
  if (!file || state.dataDomain !== "documents") {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(state.config, "data_sharing_review.source_folder_file_required", "Select a staged documents file first.")
    );
    return;
  }
  if (!file.metadata_ok) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(state.config, "data_sharing_review.source_folder_metadata_required", "Selected staged file is missing valid export metadata.")
    );
    return;
  }

  state.isRunning = true;
  setDataSharingReviewControlsDisabled(state, true);
  syncRouteBusyState(state);
  setStatus(
    state.statusNode,
    "",
    getAnalyticsText(state.config, "data_sharing_review.source_folder_running_status", "Creating import review source folder...")
  );

  try {
    const payload = await postJson(DATA_SHARING_ENDPOINTS.review, {
      data_domain: state.dataDomain,
      operation: "review",
      review_action: "content",
      staged_filename: file.filename,
      selection: selectedFileSelection(state)
    });
    setStatus(
      state.statusNode,
      sourceFolderStatusState(payload),
      sourceFolderStatusMessage(state, payload)
    );
  } catch (error) {
    setStatus(
      state.statusNode,
      "error",
      normalizeText(error && error.message) || getAnalyticsText(state.config, "data_sharing_review.source_folder_failed", "Import review source folder creation failed.")
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
    app: "",
    dataDomain: "",
    docsScope: "",
    apps: DATA_SHARING_REVIEW_APPS,
    dataDomains: DATA_SHARING_REVIEW_DOMAINS,
    adapterRegistry: null,
    applyCapability: null,
    applyActions: [],
    applyButtons: new Map(),
    appValueNode: document.getElementById("dataSharingReviewAppValue"),
    dataDomainValueNode: document.getElementById("dataSharingReviewDataDomainValue"),
    scopeValueNode: document.getElementById("dataSharingReviewScopeValue"),
    scopeRow: document.getElementById("dataSharingReviewScopeRow"),
    fileLabelNode: document.getElementById("dataSharingReviewFileLabel"),
    fileSelect: document.getElementById("dataSharingReviewFileSelect"),
    filePickerNode: null,
    resolvedContextNode: document.getElementById("dataSharingReviewResolvedContext"),
    previewButton: document.getElementById("dataSharingReviewRun"),
    reviewMenu: document.getElementById("dataSharingReviewMenu"),
    sourceFolderButton: null,
    applyActionContainer: document.getElementById("dataSharingReviewApplyActions"),
    actionMenuButton: document.getElementById("dataSharingReviewActionsButton"),
    applyActionMenu: document.getElementById("dataSharingReviewActionsMenu"),
    statusNode: document.getElementById("dataSharingReviewStatus"),
    selectionSummary: document.getElementById("dataSharingReviewSelectionSummary"),
    listNode: document.getElementById("dataSharingReviewList"),
    config: null,
    files: [],
    previewRows: [],
    selectedPreviewIds: new Set(),
    selectableList: null,
    onPreviewSelectionChange: null,
    reviewReady: false,
    serviceAvailable: false,
    isRunning: false
  };
  state.filePickerNode = state.fileSelect
    ? state.fileSelect.closest(".dataSharingReviewPage__dropdownGroup")
    : null;
  state.onPreviewSelectionChange = () => {
    state.reviewReady = false;
    updateDataSharingReviewSelectionState(state);
  };

  const requiredNodes = [
    state.appValueNode,
    state.dataDomainValueNode,
    state.scopeValueNode,
    state.scopeRow,
    state.fileLabelNode,
    state.fileSelect,
    state.resolvedContextNode,
    state.previewButton,
    state.reviewMenu,
    state.applyActionContainer,
    state.actionMenuButton,
    state.applyActionMenu,
    state.statusNode,
    state.selectionSummary,
    state.listNode
  ];
  if (requiredNodes.some((node) => !node)) return;

  try {
    state.config = await loadAnalyticsConfig();
    configureAnalyticsTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry();
    state.adapterRegistry = adapterRegistry;
    state.dataDomains = dataSharingDomainsForOperation(adapterRegistry, "list_returned", DATA_SHARING_REVIEW_DOMAINS);
    state.apps = dataSharingAppsForDomains(state.dataDomains, DATA_SHARING_REVIEW_APPS);
    renderReviewMenu(state);
    renderDataSharingReviewApplyActions(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());

    setText(state.appValueNode, "unresolved");
    setText(state.dataDomainValueNode, "unresolved");
    setText(state.scopeValueNode, "unresolved");
    setText(state.fileLabelNode, getAnalyticsText(state.config, "data_sharing_review.file_label", "staged file"));
    setText(state.previewButton, getAnalyticsText(state.config, "data_sharing_review.preview_button", "Review"));
    setText(state.actionMenuButton, getAnalyticsText(state.config, "data_sharing_review.actions_button", "Actions"));
    setFilePickerVisible(state, false);
    syncSelectedFileMetadata(state);
    renderDataSharingReviewPreviewList(state);
    updateDataSharingReviewSelectionState(state);
    setDataSharingReviewControlsDisabled(state, true);

    root.hidden = false;
    bootStatus.hidden = true;

    if (!state.serviceAvailable) {
      setDataSharingReviewControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "error",
        getAnalyticsText(
          state.config,
          "data_sharing_review.service_unavailable",
          "Studio Data Sharing API unavailable. Restart Local Studio to review returned packages."
        )
      );
      markRouteReady(state, true);
      return;
    }

    state.files = await loadImportFiles();
    if (!state.files.length) {
      state.fileSelect.innerHTML = "";
      setFilePickerVisible(state, false);
      syncSelectedFileMetadata(state);
      setDataSharingReviewControlsDisabled(state, true);
      setStatus(
        state.statusNode,
        "warn",
        getAnalyticsText(
          state.config,
          "data_sharing_review.no_files",
          "No staged returned package files found under $DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/."
        )
      );
      markRouteReady(state, true);
      return;
    }

    setFilePickerVisible(state, true);
    state.fileSelect.innerHTML = state.files.map((file, index) => {
      const filename = normalizeText(file.filename);
      const selected = index === 0 ? " selected" : "";
      return `<option value="${escapeHtml(filename)}"${selected}>${escapeHtml(filename)}</option>`;
    }).join("");
    if (state.fileSelect.selectedIndex < 0 && state.fileSelect.options.length) {
      state.fileSelect.selectedIndex = 0;
    }
    syncSelectedFileMetadata(state);
    setDataSharingReviewControlsDisabled(state, false);
    const initialStatus = selectedFileIdleStatus(state);
    setStatus(state.statusNode, initialStatus.state, initialStatus.message);
    await loadSelectedFileRows(state);
    markRouteReady(state, true);

    state.fileSelect.addEventListener("change", () => {
      resetDataSharingReviewResult(state);
      syncSelectedFileMetadata(state);
      setDataSharingReviewControlsDisabled(state, false);
      const status = selectedFileIdleStatus(state);
      setStatus(state.statusNode, status.state, status.message);
      syncRouteBusyState(state);
      loadSelectedFileRows(state).catch((error) => console.warn("data_sharing_review: unexpected records load failure", error));
    });
    state.previewButton.addEventListener("click", () => {
      hideDataSharingReviewApplyActionsMenu(state);
      toggleReviewMenu(state);
    });
    state.actionMenuButton.addEventListener("click", () => {
      hideReviewMenu(state);
      toggleDataSharingReviewApplyActionsMenu(state);
    });
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Node ? event.target : null;
      if (!target || state.applyActionContainer.contains(target)) return;
      hideDataSharingReviewApplyActionsMenu(state);
      hideReviewMenu(state);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hideDataSharingReviewApplyActionsMenu(state);
        hideReviewMenu(state);
      }
    });
    window.addEventListener("scroll", () => {
      hideDataSharingReviewApplyActionsMenu(state);
      hideReviewMenu(state);
    }, { passive: true });
    window.addEventListener("resize", () => {
      hideDataSharingReviewApplyActionsMenu(state);
      hideReviewMenu(state);
    });
    state.applyActionContainer.addEventListener("click", (event) => {
      const reviewTarget = event.target instanceof Element ? event.target.closest("[data-data-sharing-review-action]") : null;
      if (reviewTarget instanceof HTMLButtonElement) {
        const reviewAction = normalizeText(reviewTarget.dataset.dataSharingReviewAction);
        hideReviewMenu(state);
        if (reviewAction === "content") {
          createSourceFolder(state).catch((error) => console.warn("data_sharing_review: unexpected source folder failure", error));
        } else {
          runDocumentReview(state, reviewAction).catch((error) => console.warn("data_sharing_review: unexpected review failure", error));
        }
        return;
      }
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
        "Failed to load returned package data."
      )
    );
    markRouteReady(state, true);
  } finally {
    state.isRunning = false;
    syncRouteBusyState(state);
  }
}

init();
