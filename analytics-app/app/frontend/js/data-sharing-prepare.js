import {
  DATA_SHARING_ENDPOINTS,
  configureAnalyticsTransport,
  getJson,
  probeDataSharingHealth
} from "./analytics-transport.js";
import {
  getAnalyticsText,
  loadAnalyticsConfigWithText
} from "./analytics-config.js";
import {
  initializeAnalyticsRouteState,
  setAnalyticsRouteBusy,
  setAnalyticsRouteReady
} from "./analytics-route-state.js";
import {
  createAnalyticsModalHost
} from "./analytics-modal.js";
import {
  clearDataSharingPrepareResultModal,
  showDataSharingPrepareResultModal
} from "./data-sharing-prepare-modals.js";
import {
  dataSharingAppsForDomains,
  dataSharingCapabilityForOperation,
  dataSharingDomainForKey,
  dataSharingDomainIsActive,
  dataSharingDomainsForApp,
  dataSharingDomainsForOperation
} from "./data-sharing-adapters.js";
import {
  enabledPrepareConfigsForDataDomain,
  prepareProfilesForCapability,
  prepareSelectionModel,
  usesPrepareDocumentSelection,
  usesPrepareRecordSelection
} from "./data-sharing-prepare-workflow.js";
import {
  loadDataSharingPrepareDocsState
} from "./data-sharing-prepare-docs.js";
import {
  applyDataSharingPrepareSelectionFilter,
  renderDataSharingPrepareConfigSelect,
  renderDataSharingPrepareDocList,
  renderDataSharingPrepareFormatOptions,
  selectableDataSharingPrepareDocIds,
  selectedDataSharingPrepareConfig,
  syncDataSharingPrepareListActions,
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

const DATA_SHARING_APPS = [
  { key: "docs-viewer", labelKey: "app_docs_viewer", fallback: "Docs Viewer" },
  { key: "studio", labelKey: "app_studio", fallback: "Studio" },
  { key: "analytics", labelKey: "app_analytics", fallback: "Analytics" }
];
const DATA_SHARING_DOMAINS = [
  { key: "documents", app: "docs-viewer", labelKey: "data_domain_documents", fallback: "documents" },
  { key: "series", app: "studio", labelKey: "data_domain_series", fallback: "series" },
  { key: "works", app: "studio", labelKey: "data_domain_works", fallback: "works" },
  { key: "tags", app: "analytics", labelKey: "data_domain_tags", fallback: "tags" }
];
function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function prepareRecordId(record) {
  return normalizeText(record && record.id);
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

function docsScopeOptionsFromRegistry(registry) {
  const scopes = Array.isArray(registry && registry.docs_scopes) ? registry.docs_scopes : [];
  return scopes.map((scope) => {
    const key = normalizeText(scope && (scope.id || scope.scope_id)).toLowerCase();
    if (!key) return null;
    return {
      key,
      label: normalizeText(scope && scope.label) || key.replace(/[-_]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
    };
  }).filter(Boolean);
}

function selectPlaceholder(state) {
  return getAnalyticsText(state.config, "data_sharing_prepare.select_placeholder", "Select...");
}

function appLabel(state, app = state.app) {
  const item = (state.apps || DATA_SHARING_APPS).find((candidate) => candidate.key === app) || DATA_SHARING_APPS[0];
  if (item.labelKey) return getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item.label) || item.fallback || app;
}

function dataDomainLabel(state, dataDomain = state.dataDomain) {
  const item = dataSharingDomainForKey(state.dataDomains, dataDomain) || DATA_SHARING_DOMAINS[0];
  if (item.labelKey) return getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback);
  return normalizeText(item.label) || item.fallback || dataDomain;
}

function dataDomainTitle(state, dataDomain = state.dataDomain) {
  const label = dataDomainLabel(state, dataDomain);
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : dataDomain;
}

function renderAppSelect(state) {
  state.appSelect.innerHTML = state.apps.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback || item.key);
    const selected = item.key === state.app ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
  if (!state.app) state.appSelect.selectedIndex = -1;
}

function renderDataDomainSelect(state) {
  if (!state.app) {
    state.dataDomainSelect.innerHTML = "";
    state.dataDomainSelect.disabled = true;
    state.dataDomainSelect.selectedIndex = -1;
    return;
  }
  const domains = dataSharingDomainsForApp(state.dataDomains, state.app);
  state.dataDomainSelect.disabled = false;
  state.dataDomainSelect.innerHTML = domains.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback);
    const selected = item.key === state.dataDomain ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
  if (!state.dataDomain) state.dataDomainSelect.selectedIndex = -1;
}

function renderDocsScopeSelect(state) {
  const scopes = Array.isArray(state.docsScopes) ? state.docsScopes : [];
  const placeholder = selectPlaceholder(state);
  state.docsScopeSelect.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>` + scopes.map((item) => {
    const selected = item.key === state.docsScope ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(item.label || item.key)}</option>`;
  }).join("");
  state.docsScopeSelect.value = state.docsScope;
  state.docsScopeField.hidden = !usesPrepareDocumentSelection(state.prepareCapability);
}

async function loadAdapterRegistry() {
  return getJson(DATA_SHARING_ENDPOINTS.config);
}

function dataDomainUnavailableMessage(state) {
  const domain = dataSharingDomainForKey(state.dataDomains, state.dataDomain);
  return normalizeText(domain && domain.message)
    || getAnalyticsText(
      state.config,
      "data_sharing_prepare.data_domain_unsupported",
      "{data_domain_label} package preparation is not implemented yet.",
      { data_domain_label: dataDomainTitle(state) }
    );
}

function routeStateDetail(state) {
  if (state && state.root) {
    state.root.dataset.analyticsApp = state.app;
    state.root.dataset.analyticsDataDomain = state.dataDomain;
  }
  return {
    route: "data-sharing-prepare",
    mode: prepareSelectionModel(state.prepareCapability),
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.docs.length || state.exportConfigs.length)
  };
}

function markBusy(state, busy) {
  setAnalyticsRouteBusy(state.root, busy, routeStateDetail(state));
}

function markReady(state, ready) {
  setAnalyticsRouteReady(state.root, ready, routeStateDetail(state));
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function selectedDropdownsComplete(state) {
  return Boolean(state.app && state.dataDomain && selectedDataSharingPrepareConfig(state));
}

function clearDocumentSelectionState(state) {
  state.docsIndexError = false;
  state.docs = [];
  state.childrenByParent = new Map();
  state.depthById = new Map();
  state.docsById = new Map();
  state.selectedIds.clear();
  state.listNode.innerHTML = "";
  state.listNode.hidden = true;
  state.selectionSummary.textContent = "";
  const actions = state.filterNode.closest(".dataSharingPreparePage__listActions");
  if (actions) actions.hidden = true;
}

function setProgressiveGroups(state) {
  const complete = selectedDropdownsComplete(state);
  state.formatWrap.hidden = !complete;
  state.optionsGroup.hidden = !complete;
  state.configSelect.disabled = !state.dataDomain || !state.exportConfigs.length;
  state.formatOptionsNode.disabled = !complete;
  state.docsScopeSelect.disabled = !complete || !usesPrepareDocumentSelection(state.prepareCapability);
  renderDocsScopeSelect(state);
}

async function loadDocumentsForCurrentSelection(state) {
  clearDocumentSelectionState(state);
  if (!selectedDropdownsComplete(state)) return;
  const config = selectedDataSharingPrepareConfig(state);
  if (!usesPrepareRecordSelection(state.prepareCapability, config)) {
    syncDataSharingPrepareListActions(state);
    renderDataSharingPrepareDocList(state);
    return;
  }
  if (usesPrepareDocumentSelection(state.prepareCapability) && !state.docsScope) return;
  const docsState = await loadDataSharingPrepareDocsState({
    dataDomain: state.dataDomain,
    docsScope: state.docsScope,
    config,
    serviceAvailable: state.serviceAvailable,
    prepareCapability: state.prepareCapability,
    workflowActive: dataSharingDomainIsActive(state.dataDomains, state.dataDomain),
    exportConfigCount: state.exportConfigs.length,
    loadJson,
    onError: (error) => console.warn("data_sharing_prepare: selectable records load failed", state.dataDomain, state.docsScope, error)
  });
  state.docsIndexError = docsState.docsIndexError;
  state.docs = docsState.docs;
  state.childrenByParent = docsState.childrenByParent;
  state.depthById = docsState.depthById;
  state.docsById = new Map(state.docs.map((doc) => [prepareRecordId(doc), doc]));
  syncDataSharingPrepareListActions(state);
  renderDataSharingPrepareDocList(state);
}

async function refreshPrepareSelection(state) {
  markBusy(state, true);
  setProgressiveGroups(state);
  syncDataSharingPrepareConfigOptions(state);
  setProgressiveGroups(state);
  try {
    await loadDocumentsForCurrentSelection(state);
    updateStatus(state);
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

function updateStatus(state) {
  if (!state.app || !state.dataDomain || !selectedDataSharingPrepareConfig(state)) {
    setStatus(state.statusNode, "", getAnalyticsText(state.config, "data_sharing_prepare.idle_status", ""));
    state.runButton.disabled = true;
    return;
  }
  if (!dataSharingDomainIsActive(state.dataDomains, state.dataDomain)) {
    setStatus(state.statusNode, "warn", dataDomainUnavailableMessage(state));
    state.runButton.disabled = true;
    return;
  }
  const config = selectedDataSharingPrepareConfig(state);
  if (!config) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(
        state.config,
        "data_sharing_prepare.no_config",
        "No enabled {data_domain_label} sharing profiles found.",
        { data_domain_label: dataDomainTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (!state.serviceAvailable) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(
        state.config,
        "data_sharing_prepare.service_unavailable",
        "Studio Data Sharing API unavailable. Restart Local Studio to prepare packages."
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (usesPrepareRecordSelection(state.prepareCapability, config) && state.docsIndexError) {
    setStatus(
      state.statusNode,
      "error",
      getAnalyticsText(
        state.config,
        "data_sharing_prepare.docs_index_unavailable",
        "No generated {data_domain_label} data index is available for this sharing profile.",
        { data_domain_label: dataDomainTitle(state) }
      )
    );
    state.runButton.disabled = true;
    return;
  }
  if (usesPrepareDocumentSelection(state.prepareCapability) && !state.docsScope) {
    setStatus(state.statusNode, "", getAnalyticsText(state.config, "data_sharing_prepare.idle_status", ""));
    state.runButton.disabled = true;
    return;
  }
  state.runButton.disabled = false;
  setStatus(
    state.statusNode,
    "",
    getAnalyticsText(
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
  if (!selectedDropdownsComplete(state)) {
    updateStatus(state);
    return;
  }
  if (!dataSharingDomainIsActive(state.dataDomains, state.dataDomain)) {
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
  initializeAnalyticsRouteState(root, { route: "data-sharing-prepare", mode: "selection" });

  const state = {
    bootStatus,
    root,
    app: "",
    dataDomain: "",
    docsScope: "",
    apps: DATA_SHARING_APPS,
    dataDomains: DATA_SHARING_DOMAINS,
    docsScopes: [],
    appLabelNode: document.getElementById("dataSharingPrepareAppLabel"),
    appSelect: document.getElementById("dataSharingPrepareAppSelect"),
    dataDomainLabelNode: document.getElementById("dataSharingPrepareDataDomainLabel"),
    dataDomainSelect: document.getElementById("dataSharingPrepareDataDomainSelect"),
    docsScopeField: document.querySelector(".dataSharingPreparePage__docsScopeField"),
    docsScopeLabelNode: document.getElementById("dataSharingPrepareDocsScopeLabel"),
    docsScopeSelect: document.getElementById("dataSharingPrepareDocsScopeSelect"),
    configLabelNode: document.getElementById("dataSharingPrepareConfigLabel"),
    configSelect: document.getElementById("dataSharingPrepareConfigSelect"),
    missingSummaryOnlyWrap: document.getElementById("dataSharingPrepareMissingSummaryWrap"),
    missingSummaryOnly: document.getElementById("dataSharingPrepareMissingSummaryOnly"),
    missingSummaryLabelNode: document.getElementById("dataSharingPrepareMissingSummaryLabel"),
    optionsGroup: document.getElementById("dataSharingPrepareOptionsGroup"),
    formatWrap: document.getElementById("dataSharingPrepareFormatWrap"),
    formatLabelNode: document.getElementById("dataSharingPrepareFormatLabel"),
    formatOptionsNode: document.getElementById("dataSharingPrepareFormatSelect"),
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
    targetFormat: "",
    docsIndexError: false,
    serviceAvailable: false,
    isRunning: false,
    prepareCapability: null
  };

  const requiredNodes = [
    state.appLabelNode,
    state.appSelect,
    state.dataDomainLabelNode,
    state.dataDomainSelect,
    state.docsScopeField,
    state.docsScopeLabelNode,
    state.docsScopeSelect,
    state.configLabelNode,
    state.configSelect,
    state.missingSummaryOnlyWrap,
    state.missingSummaryOnly,
    state.missingSummaryLabelNode,
    state.optionsGroup,
    state.formatWrap,
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
  state.modalHost = createAnalyticsModalHost({ root });

  try {
    markBusy(state, true);
    state.config = await loadAnalyticsConfigWithText("data_sharing_prepare");
    configureAnalyticsTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry();
    state.dataDomains = dataSharingDomainsForOperation(adapterRegistry, "prepare", DATA_SHARING_DOMAINS);
    state.docsScopes = docsScopeOptionsFromRegistry(adapterRegistry);
    state.apps = dataSharingAppsForDomains(state.dataDomains, DATA_SHARING_APPS);
    renderAppSelect(state);
    renderDataDomainSelect(state);
    renderDocsScopeSelect(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());

    setText(state.appLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.app_label", "app"));
    setText(state.dataDomainLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.data_domain_label", "data domain"));
    setText(state.docsScopeLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.docs_scope_label", "Docs Viewer scope"));
    setText(state.configLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.config_label", "sharing profile"));
    setText(
      state.missingSummaryLabelNode,
      getAnalyticsText(state.config, "data_sharing_prepare.missing_summary_label", "missing summaries only")
    );
    setText(state.formatLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.format_label", "format"));
    setText(state.selectAllButton, getAnalyticsText(state.config, "data_sharing_prepare.select_all", "Select all"));
    setText(state.clearButton, getAnalyticsText(state.config, "data_sharing_prepare.clear", "Clear"));
    setText(state.runButton, getAnalyticsText(state.config, "data_sharing_prepare.run_button", "Prepare package"));
    state.runButton.title = getAnalyticsText(
      state.config,
      "data_sharing_prepare.run_disabled_title",
      "Requires the Studio Data Sharing API."
    );

    renderDataSharingPrepareConfigSelect(state);
    setProgressiveGroups(state);
    updateStatus(state);

    state.appSelect.addEventListener("change", () => {
      state.app = normalizeText(state.appSelect.value).toLowerCase();
      state.dataDomain = "";
      state.docsScope = "";
      state.prepareCapability = null;
      state.exportConfigs = [];
      renderDataDomainSelect(state);
      renderDataSharingPrepareConfigSelect(state);
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: app change failed", error));
    });
    state.dataDomainSelect.addEventListener("change", () => {
      state.dataDomain = normalizeText(state.dataDomainSelect.value).toLowerCase();
      state.docsScope = "";
      state.prepareCapability = dataSharingCapabilityForOperation(adapterRegistry, "prepare", state.dataDomain);
      if (state.dataDomain && dataSharingDomainIsActive(state.dataDomains, state.dataDomain)) {
        const capabilityProfiles = prepareProfilesForCapability(state.prepareCapability);
        const exportConfigPayload = { configs: capabilityProfiles };
        state.exportConfigs = enabledPrepareConfigsForDataDomain(exportConfigPayload, state.dataDomain);
      } else {
        state.exportConfigs = [];
      }
      renderDataSharingPrepareConfigSelect(state);
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: data domain change failed", error));
    });
    state.docsScopeSelect.addEventListener("change", () => {
      state.docsScope = normalizeText(state.docsScopeSelect.value).toLowerCase();
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: docs scope change failed", error));
    });
    state.configSelect.addEventListener("change", () => {
      state.docsScope = "";
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: config change failed", error));
    });
    state.formatOptionsNode.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLSelectElement)) return;
      state.targetFormat = normalizeText(target.value);
      updateStatus(state);
    });
    state.missingSummaryOnly.addEventListener("change", () => {
      applyDataSharingPrepareSelectionFilter(state);
      renderDataSharingPrepareDocList(state);
      updateStatus(state);
    });
    state.selectAllButton.addEventListener("click", () => {
      selectableDataSharingPrepareDocIds(state).forEach((docId) => state.selectedIds.add(docId));
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
      getAnalyticsText(
        state.config,
        "data_sharing_prepare.load_failed",
        "Failed to load {data_domain_label} package data.",
        { data_domain_label: state.config ? dataDomainTitle(state) : "Library" }
      )
    );
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

init();
