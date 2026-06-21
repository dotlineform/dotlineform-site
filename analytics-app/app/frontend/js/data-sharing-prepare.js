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
  dataSharingAppForDomain,
  dataSharingAppFromUrl,
  dataSharingAppsForDomains,
  dataSharingCapabilityForOperation,
  dataSharingDomainForKey,
  dataSharingDomainFromUrl,
  dataSharingDomainIsActive,
  dataSharingDomainsForApp,
  dataSharingDomainsForOperation
} from "./data-sharing-adapters.js";
import {
  enabledPrepareConfigsForDataDomain,
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

const DEFAULT_APP = "docs-viewer";
const DEFAULT_DATA_DOMAIN = "library";
const DATA_SHARING_APPS = [
  { key: "docs-viewer", labelKey: "app_docs_viewer", fallback: "Docs Viewer" },
  { key: "studio", labelKey: "app_studio", fallback: "Studio" },
  { key: "analytics", labelKey: "app_analytics", fallback: "Analytics" }
];
const DATA_SHARING_DOMAINS = [
  { key: "library", app: "docs-viewer", labelKey: "data_domain_library", fallback: "library" },
  { key: "analysis", app: "docs-viewer", labelKey: "data_domain_analysis", fallback: "analysis" },
  { key: "studio", app: "docs-viewer", labelKey: "data_domain_studio", fallback: "studio" },
  { key: "series", app: "studio", labelKey: "data_domain_series", fallback: "series" },
  { key: "works", app: "studio", labelKey: "data_domain_works", fallback: "works" },
  { key: "tags", app: "analytics", labelKey: "data_domain_tags", fallback: "tags" },
  { key: "tag_assignments", app: "analytics", labelKey: "data_domain_tag_assignments", fallback: "tag assignments" }
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

function dataDomainFromUrl(domains = DATA_SHARING_DOMAINS) {
  return dataSharingDomainFromUrl(domains, DEFAULT_DATA_DOMAIN);
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
}

function renderDataDomainSelect(state) {
  const domains = dataSharingDomainsForApp(state.dataDomains, state.app);
  state.dataDomainSelect.innerHTML = domains.map((item) => {
    const label = item.labelKey
      ? getAnalyticsText(state.config, `data_sharing_prepare.${item.labelKey}`, item.fallback)
      : (normalizeText(item.label) || item.fallback);
    const selected = item.key === state.dataDomain ? " selected" : "";
    return `<option value="${escapeHtml(item.key)}"${selected}>${escapeHtml(label)}</option>`;
  }).join("");
}

function updateDataSharingUrl(state, app, dataDomain) {
  const nextApp = normalizeText(app).toLowerCase();
  const nextDomain = normalizeText(dataDomain).toLowerCase();
  if (!state.apps.some((item) => item.key === nextApp)) return;
  if (!dataSharingDomainsForApp(state.dataDomains, nextApp).some((item) => item.key === nextDomain)) return;
  const url = new URL(window.location.href);
  if (nextApp === DEFAULT_APP) {
    url.searchParams.delete("app");
  } else {
    url.searchParams.set("app", nextApp);
  }
  if (nextDomain === DEFAULT_DATA_DOMAIN) {
    url.searchParams.delete("data_domain");
  } else {
    url.searchParams.set("data_domain", nextDomain);
  }
  window.location.href = url.toString();
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

function updateStatus(state) {
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
  if (usesPrepareDocumentSelection(state.prepareCapability) && state.docsIndexError) {
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
    app: DEFAULT_APP,
    dataDomain: DEFAULT_DATA_DOMAIN,
    apps: DATA_SHARING_APPS,
    dataDomains: DATA_SHARING_DOMAINS,
    appLabelNode: document.getElementById("dataSharingPrepareAppLabel"),
    appSelect: document.getElementById("dataSharingPrepareAppSelect"),
    dataDomainLabelNode: document.getElementById("dataSharingPrepareDataDomainLabel"),
    dataDomainSelect: document.getElementById("dataSharingPrepareDataDomainSelect"),
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
    state.appLabelNode,
    state.appSelect,
    state.dataDomainLabelNode,
    state.dataDomainSelect,
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
  state.modalHost = createAnalyticsModalHost({ root });

  try {
    markBusy(state, true);
    state.config = await loadAnalyticsConfigWithText("data_sharing_prepare");
    configureAnalyticsTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry();
    state.dataDomains = dataSharingDomainsForOperation(adapterRegistry, "prepare", DATA_SHARING_DOMAINS);
    state.apps = dataSharingAppsForDomains(state.dataDomains, DATA_SHARING_APPS);
    state.dataDomain = dataDomainFromUrl(state.dataDomains);
    state.app = dataSharingAppFromUrl(state.apps, dataSharingAppForDomain(state.dataDomains, state.dataDomain, DEFAULT_APP));
    const appDomains = dataSharingDomainsForApp(state.dataDomains, state.app);
    if (!appDomains.some((item) => item.key === state.dataDomain)) {
      state.dataDomain = appDomains[0] ? appDomains[0].key : DEFAULT_DATA_DOMAIN;
    }
    state.prepareCapability = dataSharingCapabilityForOperation(adapterRegistry, "prepare", state.dataDomain);
    renderAppSelect(state);
    renderDataDomainSelect(state);
    state.serviceAvailable = Boolean(await probeDataSharingHealth());
    if (dataSharingDomainIsActive(state.dataDomains, state.dataDomain)) {
      const capabilityProfiles = prepareProfilesForCapability(state.prepareCapability);
      const exportConfigPayload = { configs: capabilityProfiles };
      state.exportConfigs = enabledPrepareConfigsForDataDomain(exportConfigPayload, state.dataDomain);
    }

    const docsState = await loadDataSharingPrepareDocsState({
      config: state.config,
      dataDomain: state.dataDomain,
      serviceAvailable: state.serviceAvailable,
      prepareCapability: state.prepareCapability,
      workflowActive: dataSharingDomainIsActive(state.dataDomains, state.dataDomain),
      exportConfigCount: state.exportConfigs.length,
      loadJson,
      onError: (error) => console.warn("data_sharing_prepare: selectable records load failed", state.dataDomain, error)
    });
    state.docsIndexError = docsState.docsIndexError;
    state.docs = docsState.docs;
    state.childrenByParent = docsState.childrenByParent;
    state.depthById = docsState.depthById;
    state.docsById = new Map(state.docs.map((doc) => [normalizeText(doc.doc_id), doc]));

    setText(state.appLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.app_label", "app"));
    setText(state.dataDomainLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.data_domain_label", "data domain"));
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
    syncDataSharingPrepareConfigOptions(state);
    updateStatus(state);

    state.appSelect.addEventListener("change", () => {
      const appDomains = dataSharingDomainsForApp(state.dataDomains, state.appSelect.value);
      const nextDomain = appDomains[0] ? appDomains[0].key : state.dataDomain;
      updateDataSharingUrl(state, state.appSelect.value, nextDomain);
    });
    state.dataDomainSelect.addEventListener("change", () => updateDataSharingUrl(state, state.app, state.dataDomainSelect.value));
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
