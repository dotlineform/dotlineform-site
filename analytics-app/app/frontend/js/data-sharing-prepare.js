import {
  DATA_SHARING_ENDPOINTS,
  configureAnalyticsTransport,
  getJson,
  probeDataSharingHealth
} from "./analytics-transport.js";
import {
  getAnalyticsText,
  loadAnalyticsConfig
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
  showDataSharingPrepareContextModal
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
  prepareSelectsAllMatching,
  usesPrepareDocumentSelection,
  usesPrepareRecordSelection
} from "./data-sharing-prepare-workflow.js";
import {
  loadDataSharingPrepareDocsState
} from "./data-sharing-prepare-docs.js";
import {
  currentDataSharingPrepareSelectedIds,
  renderDataSharingPrepareConfigSelect,
  renderDataSharingPrepareDocList,
  selectedDataSharingPrepareConfig,
  syncDataSharingPrepareListActions,
  supportedUiFormatsForDataSharingPrepareConfig,
  syncDataSharingPrepareCheckboxes,
  syncDataSharingPrepareConfigOptions
} from "./data-sharing-prepare-render.js";
import {
  buildDataSharingPrepareSubmission,
  dataSharingPrepareRunningMessage,
  runDataSharingPreparePackage,
  saveDataSharingPrepareContext
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
  const buttonGroup = node.closest(".dataSharingPreparePage__buttonGroup");
  if (buttonGroup) buttonGroup.classList.remove("dataSharingPreparePage__buttonGroup--result");
  node.textContent = normalizeText(message);
  if (state) {
    node.setAttribute("data-state", state);
  } else {
    node.removeAttribute("data-state");
  }
}

function countUnitLabel(count, unit) {
  const safeCount = Number(count || 0);
  const normalizedUnit = normalizeText(unit) || "document";
  if (normalizedUnit === "record") return safeCount === 1 ? "1 record" : `${safeCount} records`;
  if (normalizedUnit === "file") return safeCount === 1 ? "1 file" : `${safeCount} files`;
  return safeCount === 1 ? "1 document" : `${safeCount} documents`;
}

function setPackageSuccessStatus(state, payload) {
  const node = state.statusNode;
  if (!node) return;
  const outputFile = normalizeText(payload && payload.output_file);
  if (!outputFile) {
    setStatus(node, "success", normalizeText(payload && payload.summary_text));
    return;
  }
  const buttonGroup = node.closest(".dataSharingPreparePage__buttonGroup");
  if (buttonGroup) buttonGroup.classList.add("dataSharingPreparePage__buttonGroup--result");
  const counts = payload && typeof payload.counts === "object" ? payload.counts : {};
  const countText = countUnitLabel(Number(counts.exported || counts.selected || 0), payload && payload.count_unit);
  const action = payload && payload.dry_run ? "Validated" : "Prepared";
  node.textContent = "";
  node.setAttribute("data-state", "success");

  const wrap = document.createElement("span");
  wrap.className = "dataSharingPreparePage__resultStatus";
  const summary = document.createElement("span");
  summary.textContent = `${action} ${countText} in package:`;
  const path = document.createElement("span");
  path.className = "dataSharingPreparePage__resultPath";
  path.textContent = outputFile;
  wrap.append(summary, path);
  node.appendChild(wrap);
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

function defaultPrepareApp(state) {
  const app = (state.apps || []).find((candidate) => (
    candidate
    && candidate.key
    && dataSharingDomainsForApp(state.dataDomains, candidate.key).length
  ));
  return normalizeText(app && app.key) || normalizeText(state.apps && state.apps[0] && state.apps[0].key);
}

function loadPrepareProfilesForDomain(state, adapterRegistry) {
  state.prepareCapability = dataSharingCapabilityForOperation(adapterRegistry, "prepare", state.dataDomain);
  if (state.dataDomain && dataSharingDomainIsActive(state.dataDomains, state.dataDomain)) {
    const capabilityProfiles = prepareProfilesForCapability(state.prepareCapability);
    const exportConfigPayload = { configs: capabilityProfiles };
    state.exportConfigs = enabledPrepareConfigsForDataDomain(exportConfigPayload, state.dataDomain);
  } else {
    state.exportConfigs = [];
  }
}

function selectOnlyPrepareDomainForApp(state, adapterRegistry) {
  const domains = dataSharingDomainsForApp(state.dataDomains, state.app);
  if (domains.length !== 1) return false;
  state.dataDomain = domains[0].key;
  renderDataDomainSelect(state);
  loadPrepareProfilesForDomain(state, adapterRegistry);
  return true;
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

function markDocumentListLoading(state, loading) {
  const isLoading = Boolean(loading);
  state.root.classList.toggle("dataSharingPreparePage--listLoading", isLoading);
  state.listNode.classList.toggle("dataSharingPrepareList--loading", isLoading);
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

function prepareConfigRequiresSelectedRecords(state, config) {
  return Boolean(
    config
    && usesPrepareRecordSelection(state.prepareCapability, config)
    && !prepareSelectsAllMatching(config, usesPrepareDocumentSelection(state.prepareCapability))
  );
}

function currentPrepareSelectionCount(state) {
  return currentDataSharingPrepareSelectedIds(state).length;
}

function clearDocumentSelectionState(state) {
  state.docsIndexError = false;
  state.docs = [];
  state.docsById = new Map();
  state.selectedIds.clear();
  if (state.selectableList) {
    state.selectableList.update({ items: [], selectedIds: [] });
  } else {
    state.listNode.innerHTML = "";
  }
  state.listNode.hidden = false;
  state.selectionSummary.textContent = "";
  const actions = state.filterNode.closest(".dataSharingPreparePage__listActions");
  if (actions) actions.hidden = false;
}

function setProgressiveGroups(state) {
  const complete = selectedDropdownsComplete(state);
  state.formatWrap.hidden = false;
  state.optionsGroup.hidden = !complete;
  state.configSelect.disabled = !state.dataDomain || !state.exportConfigs.length;
  state.formatOptionsNode.disabled = !complete;
  state.contentFormatOptionsNode.disabled = !complete;
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
  markDocumentListLoading(state, true);
  try {
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
    state.docsById = new Map(state.docs.map((doc) => [prepareRecordId(doc), doc]));
    syncDataSharingPrepareListActions(state);
    renderDataSharingPrepareDocList(state);
  } finally {
    markDocumentListLoading(state, false);
  }
}

async function refreshPrepareSelection(state, options = {}) {
  const {
    reloadDocuments = true,
    preserveOptions = false,
    preserveSelection = false
  } = options;
  markBusy(state, true);
  setProgressiveGroups(state);
  syncDataSharingPrepareConfigOptions(state, { preserveOptions, preserveSelection });
  setProgressiveGroups(state);
  try {
    if (reloadDocuments) await loadDocumentsForCurrentSelection(state);
    updateStatus(state);
    markReady(state, true);
  } finally {
    markBusy(state, false);
  }
}

function updateStatus(state) {
  updateContextButton(state);
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
  if (prepareConfigRequiresSelectedRecords(state, config) && currentPrepareSelectionCount(state) === 0) {
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

function selectedProfileSupportsContext(state) {
  const config = selectedDataSharingPrepareConfig(state);
  return Boolean(
    config
    && state.dataDomain === "documents"
    && config.external_context
    && typeof config.external_context === "object"
    && Array.isArray(config.document_fields)
    && config.document_fields.length
  );
}

function updateContextButton(state) {
  if (!state.editContextButton) return;
  const enabled = selectedProfileSupportsContext(state) && !state.isRunning;
  state.editContextButton.disabled = !enabled;
  state.editContextButton.title = enabled
    ? ""
    : getAnalyticsText(
      state.config,
      "data_sharing_prepare.context_disabled_title",
      "Select a documents sharing profile."
    );
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

  state.isRunning = true;
  state.runButton.disabled = true;
  updateContextButton(state);
  markBusy(state, true);
  setStatus(state.statusNode, "", dataSharingPrepareRunningMessage(state));

  try {
    const result = await runDataSharingPreparePackage(state, submission.request);
    if (result.failed) {
      setStatus(state.statusNode, result.statusState, result.statusMessage);
    } else {
      setPackageSuccessStatus(state, result.payload);
    }
  } finally {
    state.isRunning = false;
    state.runButton.disabled = !state.serviceAvailable
      || !selectedDropdownsComplete(state)
      || (prepareConfigRequiresSelectedRecords(state, config) && currentPrepareSelectionCount(state) === 0);
    updateContextButton(state);
    markBusy(state, false);
  }
}

async function openPrepareContextEditor(state) {
  if (state.isRunning || !selectedProfileSupportsContext(state)) {
    updateStatus(state);
    return;
  }
  const config = selectedDataSharingPrepareConfig(state);
  const result = await showDataSharingPrepareContextModal(state, config, async (externalContext) => {
    const payload = await saveDataSharingPrepareContext(state, { config, externalContext });
    if (payload && payload.external_context) {
      config.external_context = payload.external_context;
    }
    return payload;
  });
  if (result && result.confirmed) {
    setStatus(
      state.statusNode,
      "success",
      getAnalyticsText(state.config, "data_sharing_prepare.context_saved", "Context saved.")
    );
  }
  updateContextButton(state);
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
    includeDescendantsWrap: document.getElementById("dataSharingPrepareIncludeDescendantsWrap"),
    includeDescendantsInput: document.getElementById("dataSharingPrepareIncludeDescendants"),
    includeDescendantsLabelNode: document.getElementById("dataSharingPrepareIncludeDescendantsLabel"),
    optionsGroup: document.getElementById("dataSharingPrepareOptionsGroup"),
    formatWrap: document.getElementById("dataSharingPrepareFormatWrap"),
    formatLabelNode: document.getElementById("dataSharingPrepareFormatLabel"),
    formatOptionsNode: document.getElementById("dataSharingPrepareFormatSelect"),
    contentFormatWrap: document.getElementById("dataSharingPrepareContentFormatWrap"),
    contentFormatLabelNode: document.getElementById("dataSharingPrepareContentFormatLabel"),
    contentFormatOptionsNode: document.getElementById("dataSharingPrepareContentFormatSelect"),
    filterNode: document.getElementById("dataSharingPrepareListFilters"),
    selectAllButton: document.getElementById("dataSharingPrepareSelectAll"),
    clearButton: document.getElementById("dataSharingPrepareClear"),
    statusNode: document.getElementById("dataSharingPrepareStatus"),
    selectionSummary: document.getElementById("dataSharingPrepareSelectionSummary"),
    listNode: document.getElementById("dataSharingPrepareList"),
    runButton: document.getElementById("dataSharingPrepareRun"),
    editContextButton: document.getElementById("dataSharingPrepareEditContext"),
    modalHost: null,
    config: null,
    exportConfigs: [],
    docs: [],
    docsById: new Map(),
    selectedIds: new Set(),
    includeDescendants: true,
    targetFormat: "",
    contentFormat: "",
    supportedContentFormats: [],
    docsIndexError: false,
    serviceAvailable: false,
    isRunning: false,
    prepareCapability: null,
    selectableList: null,
    onSelectionChange: null
  };
  state.onSelectionChange = () => updateStatus(state);

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
    state.includeDescendantsWrap,
    state.includeDescendantsInput,
    state.includeDescendantsLabelNode,
    state.optionsGroup,
    state.formatWrap,
    state.formatLabelNode,
    state.formatOptionsNode,
    state.contentFormatWrap,
    state.contentFormatLabelNode,
    state.contentFormatOptionsNode,
    state.filterNode,
    state.selectAllButton,
    state.clearButton,
    state.statusNode,
    state.selectionSummary,
    state.listNode,
    state.runButton,
    state.editContextButton
  ];
  if (requiredNodes.some((node) => !node)) return;
  state.modalHost = createAnalyticsModalHost({ root });

  try {
    markBusy(state, true);
    state.config = await loadAnalyticsConfig();
    configureAnalyticsTransport(state.config);
    const adapterRegistry = await loadAdapterRegistry();
    state.dataDomains = dataSharingDomainsForOperation(adapterRegistry, "prepare", DATA_SHARING_DOMAINS);
    state.docsScopes = docsScopeOptionsFromRegistry(adapterRegistry);
    state.apps = dataSharingAppsForDomains(state.dataDomains, DATA_SHARING_APPS);
    state.app = defaultPrepareApp(state);
    renderAppSelect(state);
    if (!selectOnlyPrepareDomainForApp(state, adapterRegistry)) renderDataDomainSelect(state);
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
    setText(
      state.includeDescendantsLabelNode,
      getAnalyticsText(state.config, "data_sharing_prepare.include_descendants_label", "select descendants with parent")
    );
    setText(state.formatLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.format_label", "format"));
    setText(state.contentFormatLabelNode, getAnalyticsText(state.config, "data_sharing_prepare.content_format_label", "content"));
    setText(state.selectAllButton, getAnalyticsText(state.config, "data_sharing_prepare.select_all", "Select all"));
    setText(state.clearButton, getAnalyticsText(state.config, "data_sharing_prepare.clear", "Clear"));
    setText(state.runButton, getAnalyticsText(state.config, "data_sharing_prepare.run_button", "Prepare package"));
    setText(state.editContextButton, getAnalyticsText(state.config, "data_sharing_prepare.context_button", "Edit context"));
    state.runButton.title = getAnalyticsText(
      state.config,
      "data_sharing_prepare.run_disabled_title",
      "Requires the Studio Data Sharing API."
    );
    state.editContextButton.title = getAnalyticsText(
      state.config,
      "data_sharing_prepare.context_disabled_title",
      "Select a documents sharing profile."
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
      selectOnlyPrepareDomainForApp(state, adapterRegistry);
      renderDataSharingPrepareConfigSelect(state);
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: app change failed", error));
    });
    state.dataDomainSelect.addEventListener("change", () => {
      state.dataDomain = normalizeText(state.dataDomainSelect.value).toLowerCase();
      state.docsScope = "";
      loadPrepareProfilesForDomain(state, adapterRegistry);
      renderDataSharingPrepareConfigSelect(state);
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: data domain change failed", error));
    });
    state.docsScopeSelect.addEventListener("change", () => {
      state.docsScope = normalizeText(state.docsScopeSelect.value).toLowerCase();
      refreshPrepareSelection(state).catch((error) => console.warn("data_sharing_prepare: docs scope change failed", error));
    });
    state.configSelect.addEventListener("change", () => {
      refreshPrepareSelection(state, {
        reloadDocuments: false,
        preserveOptions: true,
        preserveSelection: true
      }).catch((error) => console.warn("data_sharing_prepare: config change failed", error));
    });
    state.formatOptionsNode.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLSelectElement)) return;
      state.targetFormat = normalizeText(target.value);
      updateStatus(state);
    });
    state.contentFormatOptionsNode.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLSelectElement)) return;
      state.contentFormat = normalizeText(target.value);
      updateStatus(state);
    });
    state.missingSummaryOnly.addEventListener("change", () => {
      renderDataSharingPrepareDocList(state);
      updateStatus(state);
    });
    state.includeDescendantsInput.addEventListener("change", () => {
      state.includeDescendants = state.includeDescendantsInput.checked;
      syncDataSharingPrepareCheckboxes(state);
      updateStatus(state);
    });
    state.runButton.addEventListener("click", () => {
      runPreparePackage(state).catch((error) => console.warn("data_sharing_prepare: unexpected run failure", error));
    });
    state.editContextButton.addEventListener("click", () => {
      openPrepareContextEditor(state).catch((error) => console.warn("data_sharing_prepare: context editor failed", error));
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
