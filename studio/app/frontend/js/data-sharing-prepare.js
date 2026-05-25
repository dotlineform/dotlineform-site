import {
  configureStudioTransport,
  probeDataSharingHealth
} from "./studio-transport.js";
import {
  getStudioDataPath,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  createStudioModalHost
} from "./studio-modal.js";
import {
  clearDataSharingPrepareResultModal,
  showDataSharingPrepareResultModal
} from "./data-sharing-prepare-modals.js";
import {
  workflowCapabilityForOperation,
  workflowDomainForKey,
  workflowDomainFromUrl,
  workflowDomainIsActive,
  workflowScopeParamForKey,
  workflowDomainsForOperation
} from "./data-sharing-adapters.js";
import {
  enabledPrepareConfigsForScope,
  prepareProfilesForCapability,
  prepareSelectionModel,
  usesPrepareDocumentSelection
} from "./data-sharing-prepare-workflow.js";
import {
  loadDataSharingPrepareDocsState
} from "./data-sharing-prepare-docs.js";
import {
  applyDataSharingPrepareSelectionFilter,
  dataSharingPrepareListFilters,
  renderDataSharingPrepareConfigSelect,
  renderDataSharingPrepareDocList,
  renderDataSharingPrepareFormatOptions,
  renderDataSharingPrepareListFilters,
  selectableDataSharingPrepareDocIds,
  selectedDataSharingPrepareConfig,
  supportedUiFormatsForDataSharingPrepareConfig,
  syncDataSharingPrepareCheckboxes,
  syncDataSharingPrepareConfigOptions,
  updateDataSharingPrepareSelectionFromChange,
  updateDataSharingPrepareSelectionSummary
} from "./data-sharing-prepare-render.js";
import {
  buildDataSharingPrepareSubmission,
  dataSharingPrepareRunningMessage,
  runDataSharingPreparePackage
} from "./data-sharing-prepare-service.js";

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

function scopeLabel(state, scope = state.scope) {
  const item = workflowDomainForKey(state.workflowScopes, scope) || WORKFLOW_SCOPES[0];
  if (item.labelKey) return getStudioText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item.label) || item.fallback || scope;
}

function scopeTitle(state, scope = state.scope) {
  const label = scopeLabel(state, scope);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : scope;
}

function renderScopeSelect(state) {
  state.scopeSelect.innerHTML = state.workflowScopes.map((item) => {
    const label = item.labelKey
      ? getStudioText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback);
    const selected = item.key === state.scope ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
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

async function loadAdapterRegistry(config) {
  const registryPath = getStudioDataPath(config, "data_sharing_adapters")
    || "/studio/data/config/data-sharing/data-sharing-adapters.json";
  return loadJson(registryPath);
}

function scopeUnavailableMessage(state) {
  const domain = workflowDomainForKey(state.workflowScopes, state.scope);
  return normalizeText(domain && domain.message)
    || getStudioText(
      state.config,
      "data_sharing_prepare.scope_unsupported",
      "{scope_label} package preparation is not implemented yet.",
      { scope_label: scopeTitle(state) }
    );
}

function routeStateDetail(state) {
  if (state && state.root) state.root.dataset.studioScope = state.scope;
  return {
    route: "data-sharing-prepare",
    mode: prepareSelectionModel(state.prepareCapability),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.docs.length || state.exportConfigs.length)
  };
}

function markBusy(state, busy) {
  setStudioRouteBusy(state.root, busy, routeStateDetail(state));
}

function markReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function updateStatus(state) {
  if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
    setStatus(state.statusNode, "warn", scopeUnavailableMessage(state));
    state.runButton.disabled = true;
    return;
  }
  const config = selectedDataSharingPrepareConfig(state);
  if (!config) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.no_config",
        "No enabled {scope_label} sharing profiles found.",
        { scope_label: scopeTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (usesPrepareDocumentSelection(state.prepareCapability) && state.docsIndexError) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.docs_index_unavailable",
        "No generated {scope_label} data index is available for this sharing profile.",
        { scope_label: scopeTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (!state.serviceAvailable) {
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.service_unavailable",
        "Docs Viewer service unavailable. Start docs-viewer/bin/docs-viewer to prepare packages."
      )
    );
    state.runButton.disabled = true;
    return;
  }
  state.runButton.disabled = false;
  setStatus(
    state.statusNode,
    "",
    getStudioText(
      state.config,
      "data_sharing_prepare.idle_status",
      ""
    )
  );
}

function resetResult(state) {
  clearDataSharingPrepareResultModal(state);
}

async function runPreparePackage(state) {
  if (!state.serviceAvailable || state.isRunning) return;
  if (!workflowDomainIsActive(state.workflowScopes, state.scope)) {
    updateStatus(state);
    return;
  }
  const config = selectedDataSharingPrepareConfig(state);
  if (!config) {
    updateStatus(state);
    return;
  }
  const submission = buildDataSharingPrepareSubmission(state, {
    config,
    supportedFormats: supportedUiFormatsForDataSharingPrepareConfig(config)
  });
  if (!submission.ok) {
    setStatus(state.statusNode, submission.statusState, submission.statusMessage);
    return;
  }

  resetResult(state);
  state.isRunning = true;
  state.runButton.disabled = true;
  markBusy(state, true);
  setStatus(state.statusNode, "", dataSharingPrepareRunningMessage(state));

  try {
    const result = await runDataSharingPreparePackage(state, submission.request);
    showDataSharingPrepareResultModal(state, result.payload, result.failed);
    setStatus(state.statusNode, result.statusState, result.statusMessage);
  } finally {
    state.isRunning = false;
    state.runButton.disabled = !state.serviceAvailable;
    markBusy(state, false);
  }
}

async function init() {
  const bootStatus = document.getElementById("dataSharingPrepareBootStatus");
  const root = document.getElementById("dataSharingPrepareRoot");
  if (!bootStatus || !root) return;
  initializeStudioRouteState(root, { route: "data-sharing-prepare", mode: "selection" });

  const state = {
    bootStatus,
    root,
    scope: workflowScopeFromUrl(),
    workflowScopes: WORKFLOW_SCOPES,
    scopeLabelNode: document.getElementById("dataSharingPrepareScopeLabel"),
    scopeSelect: document.getElementById("dataSharingPrepareScopeSelect"),
    configLabelNode: document.getElementById("dataSharingPrepareConfigLabel"),
    configSelect: document.getElementById("dataSharingPrepareConfigSelect"),
    missingSummaryOnlyWrap: document.getElementById("dataSharingPrepareMissingSummaryWrap"),
    missingSummaryOnly: document.getElementById("dataSharingPrepareMissingSummaryOnly"),
    missingSummaryLabelNode: document.getElementById("dataSharingPrepareMissingSummaryLabel"),
    formatLabelNode: document.getElementById("dataSharingPrepareFormatLabel"),
    formatOptionsNode: document.getElementById("dataSharingPrepareFormatOptions"),
    filterNode: document.getElementById("dataSharingPrepareListFilters"),
    selectAllButton: document.getElementById("dataSharingPrepareSelectAll"),
    clearButton: document.getElementById("dataSharingPrepareClear"),
    statusNode: document.getElementById("dataSharingPrepareStatus"),
    selectionSummary: document.getElementById("dataSharingPrepareSelectionSummary"),
    listNode: document.getElementById("dataSharingPrepareList"),
    runButton: document.getElementById("dataSharingPrepareRun"),
    modalHost: null,
    config: null,
    exportConfigs: [],
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    depthById: new Map(),
    selectedIds: new Set(),
    listFilter: "all",
    targetFormat: "",
    docsIndexError: false,
    serviceAvailable: false,
    isRunning: false,
    prepareCapability: null
  };

  const requiredNodes = [
    state.scopeLabelNode,
    state.scopeSelect,
    state.configLabelNode,
    state.configSelect,
    state.missingSummaryOnlyWrap,
    state.missingSummaryOnly,
    state.missingSummaryLabelNode,
    state.formatLabelNode,
    state.formatOptionsNode,
    state.filterNode,
    state.selectAllButton,
    state.clearButton,
    state.statusNode,
    state.selectionSummary,
    state.listNode,
    state.runButton
  ];
  if (requiredNodes.some((node) => !node)) return;
  state.modalHost = createStudioModalHost({ root });

  try {
    markBusy(state, true);
    state.config = await loadStudioConfigWithText("data_sharing_prepare");
    configureStudioTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry(state.config);
    state.workflowScopes = workflowDomainsForOperation(adapterRegistry, "prepare", WORKFLOW_SCOPES);
    state.scope = workflowScopeFromUrl(state.workflowScopes);
    state.prepareCapability = workflowCapabilityForOperation(adapterRegistry, "prepare", state.scope);
    renderScopeSelect(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());
    if (workflowDomainIsActive(state.workflowScopes, state.scope)) {
      const capabilityProfiles = prepareProfilesForCapability(state.prepareCapability);
      const exportConfigPayload = capabilityProfiles.length
        ? { configs: capabilityProfiles }
        : await loadJson(
          getStudioDataPath(state.config, "library_export_configs")
            || "/studio/data/config/data-sharing/library-export-configs.json"
        );
      state.exportConfigs = enabledPrepareConfigsForScope(exportConfigPayload, state.scope);
    }

    const docsState = await loadDataSharingPrepareDocsState({
      config: state.config,
      scope: state.scope,
      serviceAvailable: state.serviceAvailable,
      prepareCapability: state.prepareCapability,
      workflowActive: workflowDomainIsActive(state.workflowScopes, state.scope),
      exportConfigCount: state.exportConfigs.length,
      loadJson,
      onError: (error) => console.warn("data_sharing_prepare: docs index load failed", state.scope, error)
    });
    state.docsIndexError = docsState.docsIndexError;
    state.docs = docsState.docs;
    state.childrenByParent = docsState.childrenByParent;
    state.depthById = docsState.depthById;
    state.docsById = new Map(state.docs.map((doc) => [normalizeText(doc.doc_id), doc]));

    setText(state.scopeLabelNode, getStudioText(state.config, "data_sharing_prepare.scope_label", "scope"));
    setText(state.configLabelNode, getStudioText(state.config, "data_sharing_prepare.config_label", "sharing profile"));
    setText(
      state.missingSummaryLabelNode,
      getStudioText(state.config, "data_sharing_prepare.missing_summary_label", "missing summaries only")
    );
    setText(state.formatLabelNode, getStudioText(state.config, "data_sharing_prepare.format_label", "format"));
    setText(state.selectAllButton, getStudioText(state.config, "data_sharing_prepare.select_all", "Select all"));
    setText(state.clearButton, getStudioText(state.config, "data_sharing_prepare.clear", "Clear"));
    setText(state.runButton, getStudioText(state.config, "data_sharing_prepare.run_button", "Prepare package"));
    state.runButton.title = getStudioText(
      state.config,
      "data_sharing_prepare.run_disabled_title",
      "Requires the local Docs Viewer service."
    );

    renderDataSharingPrepareConfigSelect(state);
    syncDataSharingPrepareConfigOptions(state);
    updateStatus(state);

    state.scopeSelect.addEventListener("change", () => updateScopeUrl(state.scopeSelect.value, state.workflowScopes));
    state.configSelect.addEventListener("change", () => {
      syncDataSharingPrepareConfigOptions(state);
      updateStatus(state);
    });
    state.formatOptionsNode.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement) || target.name !== "dataSharingPrepareFormat") return;
      state.targetFormat = normalizeText(target.value);
      renderDataSharingPrepareFormatOptions(state);
      updateStatus(state);
    });
    state.missingSummaryOnly.addEventListener("change", () => {
      applyDataSharingPrepareSelectionFilter(state);
      renderDataSharingPrepareListFilters(state);
      renderDataSharingPrepareDocList(state);
      updateStatus(state);
    });
    state.filterNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest
        ? event.target.closest("[data-data-sharing-prepare-filter]")
        : null;
      if (!button) return;
      const filter = normalizeText(button.getAttribute("data-data-sharing-prepare-filter"));
      if (!dataSharingPrepareListFilters().includes(filter)) return;
      state.listFilter = filter;
      renderDataSharingPrepareListFilters(state);
      renderDataSharingPrepareDocList(state);
      updateStatus(state);
    });
    state.selectAllButton.addEventListener("click", () => {
      selectableDataSharingPrepareDocIds(state, { visibleOnly: true }).forEach((docId) => state.selectedIds.add(docId));
      syncDataSharingPrepareCheckboxes(state);
      updateDataSharingPrepareSelectionSummary(state);
    });
    state.clearButton.addEventListener("click", () => {
      state.selectedIds.clear();
      syncDataSharingPrepareCheckboxes(state);
      updateDataSharingPrepareSelectionSummary(state);
    });
    state.listNode.addEventListener("change", (event) => {
      if (!updateDataSharingPrepareSelectionFromChange(state, event)) return;
      syncDataSharingPrepareCheckboxes(state);
      updateDataSharingPrepareSelectionSummary(state);
    });
    state.runButton.addEventListener("click", () => {
      runPreparePackage(state).catch((error) => console.warn("data_sharing_prepare: unexpected run failure", error));
    });

    root.hidden = false;
    bootStatus.hidden = true;
    markReady(state, true);
  } catch (error) {
    console.warn("data_sharing_prepare: load failed", error);
    root.hidden = false;
    bootStatus.hidden = true;
    setStatus(
      state.statusNode,
      "error",
      getStudioText(
        state.config,
        "data_sharing_prepare.load_failed",
        "Failed to load {scope_label} package data.",
        { scope_label: state.config ? scopeTitle(state) : "Library" }
      )
    );
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

init();
