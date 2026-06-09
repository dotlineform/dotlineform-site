import { getAdminText, loadAdminConfigWithText } from "./admin-config.js";
import {
  CHECKS_API_ENDPOINTS,
  deleteJson,
  getJson,
  postJson,
  probeChecksApiHealth
} from "./admin-transport.js";
import { initializeAdminRouteState } from "./admin-route-state.js";
import {
  collectOperationalRouteElements,
  markOperationalRouteReady,
  projectOperationalRunButtonState,
  syncOperationalRouteBusyState
} from "./admin-operational-route.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function setText(node, value) {
  if (!node) return;
  node.textContent = normalizeText(value);
}

function setStatus(node, state, message) {
  if (!node) return;
  node.textContent = normalizeText(message);
  if (state) node.setAttribute("data-state", state);
  else node.removeAttribute("data-state");
}

function checksMode(state) {
  if (!state.serviceAvailable) return "unavailable";
  if (state.isRunning) return "running";
  if (state.loadedRunId) return "report";
  return "idle";
}

function routeOptions() {
  return {
    route: "admin-checks",
    mode: checksMode,
    serviceAvailable: (state) => state.serviceAvailable,
    isBusy: (state) => state.isRunning,
    recordLoaded: (state) => Boolean(state.loadedRunId)
  };
}

function syncBusy(state) {
  syncOperationalRouteBusyState(state, routeOptions());
  const projection = projectOperationalRunButtonState(state, {
    serviceAvailable: (routeState) => routeState.serviceAvailable,
    isBusy: (routeState) => routeState.isRunning,
    canRun: (routeState) => Boolean(routeState.reportSelect.value && routeState.scopeSelect.value)
  });
  state.runButton.disabled = projection.disabled;
  state.deleteButton.disabled = state.isRunning || !state.selectedRunId || !state.serviceAvailable;
  setText(
    state.runButton,
    state.isRunning
      ? getAdminText(state.config, "admin_checks.running_button", "Running...")
      : getAdminText(state.config, "admin_checks.run_button", "Run")
  );
}

function markReady(state, ready) {
  markOperationalRouteReady(state, ready, routeOptions());
}

function optionLabel(item) {
  return normalizeText(item && item.label) || normalizeText(item && item.id);
}

function renderSelect(select, items, options = {}) {
  const includeAll = Boolean(options.includeAll);
  const allLabel = options.allLabel || "< all >";
  const selectedValue = options.selectedValue || "";
  const rows = [];
  if (includeAll) {
    rows.push(new Option(allLabel, "", selectedValue === "", selectedValue === ""));
  }
  for (const item of Array.isArray(items) ? items : []) {
    const id = normalizeText(item && item.id);
    if (!id) continue;
    rows.push(new Option(optionLabel(item), id, id === selectedValue, id === selectedValue));
  }
  select.replaceChildren(...rows);
  if (selectedValue && [...select.options].some((option) => option.value === selectedValue)) {
    select.value = selectedValue;
  }
}

function reportById(state, reportId = state.reportSelect.value) {
  return state.reports.find((report) => report.id === reportId) || null;
}

function renderOptionControls(state) {
  const report = reportById(state);
  const allowed = report && report.allowed_options && typeof report.allowed_options === "object"
    ? report.allowed_options
    : {};
  const defaults = report && report.default_options && typeof report.default_options === "object"
    ? report.default_options
    : {};
  state.optionsNode.textContent = "";
  Object.entries(allowed).forEach(([optionId, schema]) => {
    const field = document.createElement("label");
    field.className = "studioChecksField";
    field.dataset.checksOptionField = optionId;

    const label = document.createElement("span");
    label.textContent = getAdminText(state.config, `admin_checks.option_${optionId}_label`, optionId);
    field.append(label);

    const enumValues = schema && Array.isArray(schema.enum) ? schema.enum : null;
    if (enumValues) {
      const select = document.createElement("select");
      select.className = "tagStudio__input";
      select.dataset.checksOption = optionId;
      enumValues.forEach((value) => {
        select.append(new Option(String(value), String(value), defaults[optionId] === value, defaults[optionId] === value));
      });
      select.value = defaults[optionId] == null ? String(enumValues[0] || "") : String(defaults[optionId]);
      field.append(select);
    } else {
      const input = document.createElement("input");
      input.className = "tagStudio__input";
      input.dataset.checksOption = optionId;
      input.type = schema && schema.type === "integer" ? "number" : "text";
      if (schema && Number.isInteger(schema.minimum)) input.min = String(schema.minimum);
      if (schema && Number.isInteger(schema.maximum)) input.max = String(schema.maximum);
      input.value = defaults[optionId] == null ? "" : String(defaults[optionId]);
      field.append(input);
    }
    state.optionsNode.append(field);
  });
}

function optionValueFromControl(control, schema) {
  if (!control) return undefined;
  if (schema && schema.type === "integer") {
    const value = Number.parseInt(control.value, 10);
    return Number.isFinite(value) ? value : undefined;
  }
  if (schema && schema.type === "boolean") {
    return Boolean(control.checked);
  }
  return normalizeText(control.value);
}

function collectReportOptions(state) {
  const report = reportById(state);
  if (!report) return {};
  const allowed = report.allowed_options && typeof report.allowed_options === "object" ? report.allowed_options : {};
  const options = {};
  Object.entries(allowed).forEach(([optionId, schema]) => {
    const control = state.optionsNode.querySelector(`[data-checks-option="${CSS.escape(optionId)}"]`);
    const value = optionValueFromControl(control, schema);
    if (value !== undefined && value !== "") {
      options[optionId] = value;
    }
  });
  return options;
}

function buildRunPayload(state) {
  const reportId = state.reportSelect.value;
  const options = collectReportOptions(state);
  return {
    scope: state.scopeSelect.value,
    families: state.familySelect.value ? [state.familySelect.value] : [],
    areas: state.areaSelect.value ? [state.areaSelect.value] : [],
    routes: state.routeSelect.value ? [state.routeSelect.value] : [],
    reports: [reportId],
    options: Object.keys(options).length ? { [reportId]: options } : {},
    write: true
  };
}

function resetControls(state) {
  renderSelect(state.reportSelect, state.reports, { selectedValue: state.reports[0] && state.reports[0].id });
  renderSelect(state.scopeSelect, state.scopes, { selectedValue: state.scopes.some((item) => item.id === "docs-viewer") ? "docs-viewer" : state.scopes[0] && state.scopes[0].id });
  renderSelect(state.familySelect, state.families, { includeAll: true, allLabel: state.allLabel });
  renderSelect(state.areaSelect, state.areas, { includeAll: true, allLabel: state.allLabel });
  renderSelect(state.routeSelect, state.routes, { includeAll: true, allLabel: state.allLabel });
  renderOptionControls(state);
}

function clearOutput(state) {
  state.loadedRunId = "";
  state.loadedReportId = "";
  state.artifactPathNode.textContent = "";
  state.markdownNode.textContent = getAdminText(state.config, "admin_checks.markdown_empty", "No report selected.");
}

function setRunListSelection(state, runId) {
  state.selectedRunId = normalizeText(runId);
  state.runsSelect.value = state.selectedRunId;
  syncBusy(state);
}

function renderRuns(state, runs, selectedRunId = "") {
  const rows = Array.isArray(runs) ? runs : [];
  if (!rows.length) {
    state.runsSelect.replaceChildren(new Option(getAdminText(state.config, "admin_checks.no_runs", "No checks runs found."), "", true, true));
    state.runsSelect.disabled = true;
    state.selectedRunId = "";
    syncBusy(state);
    return;
  }
  state.runsSelect.disabled = false;
  const options = [new Option("", "", selectedRunId === "", selectedRunId === "")];
  rows.forEach((run) => {
    const runId = normalizeText(run && run.run_id);
    const status = normalizeText(run && run.status) || "unknown";
    const scope = normalizeText(run && run.scope);
    options.push(new Option(`${runId}  ${status}${scope ? `  ${scope}` : ""}`, runId, runId === selectedRunId, runId === selectedRunId));
  });
  state.runsSelect.replaceChildren(...options);
  setRunListSelection(state, selectedRunId);
}

async function refreshRuns(state, selectedRunId = "") {
  if (!state.serviceAvailable) return;
  const payload = await getJson(CHECKS_API_ENDPOINTS.runs);
  state.runs = Array.isArray(payload && payload.runs) ? payload.runs : [];
  renderRuns(state, state.runs, selectedRunId);
}

function applyTargetsToControls(state, targets) {
  if (!targets || typeof targets !== "object") return;
  if (targets.scope) state.scopeSelect.value = normalizeText(targets.scope);
  state.familySelect.value = Array.isArray(targets.families) && targets.families[0] ? normalizeText(targets.families[0]) : "";
  state.areaSelect.value = Array.isArray(targets.areas) && targets.areas[0] ? normalizeText(targets.areas[0]) : "";
  state.routeSelect.value = Array.isArray(targets.routes) && targets.routes[0] ? normalizeText(targets.routes[0]) : "";
}

function firstReportId(summary, fallback) {
  const reports = summary && Array.isArray(summary.reports) ? summary.reports : [];
  const first = reports.find((report) => report && report.report_id);
  return normalizeText(first && first.report_id) || fallback;
}

function renderArtifact(state, payload) {
  const markdown = normalizeText(payload && payload.report_markdown);
  const path = normalizeText(payload && payload.report_markdown_path);
  state.artifactPathNode.textContent = path
    ? `${getAdminText(state.config, "admin_checks.artifact_path_label", "artifact")}: ${path}`
    : "";
  state.markdownNode.textContent = markdown || getAdminText(state.config, "admin_checks.markdown_empty", "No report selected.");
}

async function loadRun(state, runId) {
  if (!runId || !state.serviceAvailable) return;
  const summaryPayload = await getJson(CHECKS_API_ENDPOINTS.runSummary(runId));
  const summary = summaryPayload && summaryPayload.summary && typeof summaryPayload.summary === "object"
    ? summaryPayload.summary
    : {};
  const reportId = firstReportId(summary, state.reportSelect.value);
  state.loadedRunId = runId;
  state.loadedReportId = reportId;
  if (reportId) state.reportSelect.value = reportId;
  applyTargetsToControls(state, summary.targets);
  renderOptionControls(state);
  const reportPayload = reportId ? await getJson(CHECKS_API_ENDPOINTS.report(runId, reportId)) : null;
  renderArtifact(state, reportPayload || summaryPayload);
  setRunListSelection(state, runId);
}

async function runChecks(state) {
  if (state.isRunning || !state.serviceAvailable) return;
  state.isRunning = true;
  syncBusy(state);
  setStatus(state.statusNode, "", getAdminText(state.config, "admin_checks.status_running", "Running checks..."));
  try {
    const result = await postJson(CHECKS_API_ENDPOINTS.runs, buildRunPayload(state), { allowApiFailure: true });
    const status = normalizeText(result && result.status);
    setStatus(
      state.statusNode,
      status === "passed" ? "success" : "error",
      status === "passed"
        ? getAdminText(state.config, "admin_checks.status_passed", "Checks run completed.")
        : getAdminText(state.config, "admin_checks.status_failed", "Checks run failed.")
    );
    const runId = normalizeText(result && result.summary && result.summary.run_id);
    await refreshRuns(state, runId);
    if (runId) {
      await loadRun(state, runId);
    }
  } catch (error) {
    console.warn("admin_checks: run failed", error);
    setStatus(state.statusNode, "error", getAdminText(state.config, "admin_checks.status_request_failed", "Checks request failed."));
  } finally {
    state.isRunning = false;
    syncBusy(state);
  }
}

async function deleteSelectedRun(state) {
  const runId = state.selectedRunId;
  if (state.isRunning || !runId || !state.serviceAvailable) return;
  const confirmTemplate = getAdminText(state.config, "admin_checks.delete_confirm", "Delete checks snapshot {run_id}?");
  if (!window.confirm(confirmTemplate.replace("{run_id}", runId))) return;

  state.isRunning = true;
  syncBusy(state);
  setStatus(state.statusNode, "", getAdminText(state.config, "admin_checks.delete_status_running", "Deleting snapshot..."));
  try {
    await deleteJson(CHECKS_API_ENDPOINTS.run(runId));
    resetControls(state);
    clearOutput(state);
    setRunListSelection(state, "");
    setStatus(state.statusNode, "success", getAdminText(state.config, "admin_checks.delete_status_deleted", "Checks snapshot deleted."));
    await refreshRuns(state, "");
  } catch (error) {
    console.warn("admin_checks: delete failed", error);
    setStatus(state.statusNode, "error", getAdminText(state.config, "admin_checks.delete_status_failed", "Checks snapshot delete failed."));
  } finally {
    state.isRunning = false;
    syncBusy(state);
  }
}

function normalizeMetadata(payload) {
  return {
    reports: Array.isArray(payload && payload.reports) ? payload.reports : [],
    scopes: Array.isArray(payload && payload.scopes) ? payload.scopes : [],
    families: Array.isArray(payload && payload.families) ? payload.families : [],
    areas: Array.isArray(payload && payload.areas) ? payload.areas : [],
    routes: Array.isArray(payload && payload.routes)
      ? payload.routes.filter((route) => normalizeText(route && route.status) === "mapped")
      : []
  };
}

async function init() {
  const bootStatus = document.getElementById("studioChecksBootStatus");
  const root = document.getElementById("studioChecksRoot");
  const statusNode = document.getElementById("studioChecksStatus");
  const form = document.getElementById("studioChecksForm");
  const reportSelect = document.getElementById("studioChecksReport");
  const scopeSelect = document.getElementById("studioChecksScope");
  const familySelect = document.getElementById("studioChecksFamily");
  const areaSelect = document.getElementById("studioChecksArea");
  const routeSelect = document.getElementById("studioChecksRoute");
  const optionsNode = document.getElementById("studioChecksOptions");
  const runButton = document.getElementById("studioChecksRun");
  const runsTitle = document.getElementById("studioChecksRunsTitle");
  const runsSelect = document.getElementById("studioChecksRuns");
  const deleteButton = document.getElementById("studioChecksDelete");
  const artifactPathNode = document.getElementById("studioChecksArtifactPath");
  const markdownNode = document.getElementById("studioChecksMarkdown");
  const required = collectOperationalRouteElements({
    bootStatus,
    root,
    statusNode,
    form,
    reportSelect,
    scopeSelect,
    familySelect,
    areaSelect,
    routeSelect,
    optionsNode,
    runButton,
    runsTitle,
    runsSelect,
    deleteButton,
    artifactPathNode,
    markdownNode
  });
  if (!required.ok) return;

  initializeAdminRouteState(root, { route: "admin-checks", mode: "idle" });

  try {
    const config = await loadAdminConfigWithText("admin_checks");
    const serviceAvailable = await probeChecksApiHealth();
    const metadata = serviceAvailable ? normalizeMetadata(await getJson(CHECKS_API_ENDPOINTS.reports)) : normalizeMetadata(null);
    const state = {
      config,
      root,
      statusNode,
      form,
      reportSelect,
      scopeSelect,
      familySelect,
      areaSelect,
      routeSelect,
      optionsNode,
      runButton,
      runsTitle,
      runsSelect,
      deleteButton,
      artifactPathNode,
      markdownNode,
      serviceAvailable,
      isRunning: false,
      loadedRunId: "",
      loadedReportId: "",
      selectedRunId: "",
      runs: [],
      allLabel: getAdminText(config, "admin_checks.all_option", "< all >"),
      ...metadata
    };

    setText(document.getElementById("studioChecksReportLabel"), getAdminText(config, "admin_checks.report_label", "report"));
    setText(document.getElementById("studioChecksScopeLabel"), getAdminText(config, "admin_checks.scope_label", "scope"));
    setText(document.getElementById("studioChecksFamilyLabel"), getAdminText(config, "admin_checks.family_label", "family"));
    setText(document.getElementById("studioChecksAreaLabel"), getAdminText(config, "admin_checks.area_label", "area"));
    setText(document.getElementById("studioChecksRouteLabel"), getAdminText(config, "admin_checks.route_label", "route"));
    setText(runsTitle, getAdminText(config, "admin_checks.runs_label", "run folders"));
    setText(deleteButton, getAdminText(config, "admin_checks.delete_button", "Delete"));
    resetControls(state);
    clearOutput(state);
    setStatus(
      statusNode,
      serviceAvailable ? "" : "error",
      serviceAvailable
        ? getAdminText(config, "admin_checks.idle_status", "Choose a report and target filters.")
        : getAdminText(config, "admin_checks.service_unavailable", "Checks API unavailable. Start bin/local-admin to run checks.")
    );

    reportSelect.addEventListener("change", () => {
      renderOptionControls(state);
      syncBusy(state);
    });
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runChecks(state).catch((error) => console.warn("admin_checks: unexpected run failure", error));
    });
    runsSelect.addEventListener("change", () => {
      const runId = normalizeText(runsSelect.value);
      setRunListSelection(state, runId);
      if (!runId) {
        clearOutput(state);
        return;
      }
      loadRun(state, runId).catch((error) => {
        console.warn("admin_checks: run load failed", error);
        setStatus(state.statusNode, "error", "Checks run load failed.");
      });
    });
    deleteButton.addEventListener("click", () => {
      deleteSelectedRun(state).catch((error) => console.warn("admin_checks: unexpected delete failure", error));
    });

    syncBusy(state);
    await refreshRuns(state);
    root.hidden = false;
    bootStatus.hidden = true;
    markReady(state, true);
  } catch (error) {
    console.warn("admin_checks: init failed", error);
    bootStatus.textContent = "Failed to load Admin checks.";
    bootStatus.setAttribute("data-state", "error");
    root.hidden = false;
    markReady({ root, serviceAvailable: false, isRunning: false, loadedRunId: "" }, true);
  }
}

init();
