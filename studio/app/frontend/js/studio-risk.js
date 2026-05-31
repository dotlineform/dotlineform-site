import { getStudioText, loadStudioConfigWithText } from "./studio-config.js";
import {
  RISK_API_ENDPOINTS,
  getJson,
  postJson,
  probeRiskApiHealth
} from "./studio-transport.js";
import { initializeStudioRouteState } from "./studio-route-state.js";
import {
  collectOperationalRouteElements,
  markOperationalRouteReady,
  projectOperationalRunButtonState,
  syncOperationalRouteBusyState
} from "./studio-operational-route.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";

const DEFAULT_APPS = Object.freeze(["docs-viewer", "studio", "analytics", "public-site", "all"]);

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value, attribute = false) {
  const text = normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return attribute
    ? text.replace(/"/g, "&quot;").replace(/'/g, "&#39;")
    : text;
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

function studioRiskMode(state) {
  if (!state.serviceAvailable) return "unavailable";
  if (state.isRunning) return "running";
  if (state.summaryLoaded) return "summary";
  return "idle";
}

function routeOptions() {
  return {
    route: "studio-risk",
    mode: studioRiskMode,
    serviceAvailable: (state) => state.serviceAvailable,
    isBusy: (state) => state.isRunning,
    recordLoaded: (state) => state.summaryLoaded
  };
}

function syncBusy(state) {
  syncOperationalRouteBusyState(state, routeOptions());
  const projection = projectOperationalRunButtonState(state, {
    serviceAvailable: (routeState) => routeState.serviceAvailable,
    isBusy: (routeState) => routeState.isRunning,
    canRun: (routeState) => normalizeText(routeState.areaInput.value) !== ""
  });
  state.runButton.disabled = projection.disabled;
  setText(
    state.runButton,
    state.isRunning
      ? getStudioText(state.config, "studio_risk.running_button", "Running...")
      : getStudioText(state.config, "studio_risk.run_button", "Run evidence")
  );
}

function markReady(state, ready) {
  markOperationalRouteReady(state, ready, routeOptions());
}

function runIdSlug(value) {
  return normalizeText(value).toLowerCase().replace(/[^a-z0-9_.-]+/g, "-").replace(/^-+|-+$/g, "") || "risk";
}

function defaultRunId(state) {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "").replace("T", "-");
  return `${stamp}-${runIdSlug(state.appSelect.value)}-${runIdSlug(state.areaInput.value)}`;
}

function renderApps(state, apps) {
  const values = Array.isArray(apps) && apps.length ? apps : DEFAULT_APPS;
  state.appSelect.innerHTML = values.map((app) => {
    const selected = app === "docs-viewer" ? " selected" : "";
    return `<option value="${escapeHtml(app, true)}"${selected}>${escapeHtml(app)}</option>`;
  }).join("");
}

function renderRuns(state, runs) {
  const rows = Array.isArray(runs) ? runs : [];
  if (!rows.length) {
    state.runsNode.innerHTML = `<p class="tagStudio__status">${escapeHtml(getStudioText(state.config, "studio_risk.no_runs", "No risk evidence runs found."))}</p>`;
    return;
  }
  state.runsNode.innerHTML = rows.map((run) => {
    const runId = normalizeText(run && run.run_id);
    const status = normalizeText(run && run.status) || "unknown";
    const app = normalizeText(run && run.app);
    const area = normalizeText(run && run.area);
    const summaryPath = normalizeText(run && run.summary_path);
    return `<button type="button" class="studioRiskRun" data-risk-run-id="${escapeHtml(runId, true)}">
      <span class="studioRiskRun__id">${escapeHtml(runId)}</span>
      <span class="studioRiskRun__meta">${escapeHtml(status)} · ${escapeHtml(app)} / ${escapeHtml(area)}</span>
      ${summaryPath ? `<span class="studioRiskRun__path">${escapeHtml(summaryPath)}</span>` : ""}
    </button>`;
  }).join("");
}

function renderSummary(state, payload) {
  const summary = payload && payload.summary && typeof payload.summary === "object" ? payload.summary : null;
  const markdown = normalizeText(payload && payload.summary_markdown);
  state.summaryLoaded = Boolean(summary || markdown);
  if (!state.summaryLoaded) {
    state.summaryNode.innerHTML = "";
    syncBusy(state);
    return;
  }
  const status = normalizeText(summary && summary.status) || "unknown";
  const runId = normalizeText(summary && summary.run_id);
  const summaryPath = normalizeText(payload && payload.summary_path);
  state.summaryNode.innerHTML = `
    <div class="studioRiskSummaryCard">
      <p class="tagStudio__status studioRiskSummaryCard__status" data-state="${status === "passed" ? "success" : ""}">
        ${escapeHtml(status)}${runId ? ` · ${escapeHtml(runId)}` : ""}
      </p>
      ${summaryPath ? `<p class="studioRiskSummaryCard__path">${escapeHtml(summaryPath)}</p>` : ""}
      ${markdown ? `<pre class="studioRiskSummaryCard__markdown">${escapeHtml(markdown)}</pre>` : ""}
    </div>
  `;
  syncBusy(state);
}

async function refreshRuns(state) {
  if (!state.serviceAvailable) return;
  const payload = await getJson(RISK_API_ENDPOINTS.runs);
  renderRuns(state, payload && payload.runs);
}

async function loadRunSummary(state, runId) {
  if (!runId || !state.serviceAvailable) return;
  const payload = await getJson(RISK_API_ENDPOINTS.runSummary(runId));
  renderSummary(state, payload);
}

function buildRunPayload(state) {
  const runId = normalizeText(state.runIdInput.value) || defaultRunId(state);
  state.runIdInput.value = runId;
  const dryRun = state.dryRunInput.checked;
  const payload = {
    app: state.appSelect.value,
    area: normalizeText(state.areaInput.value),
    run_id: runId,
    dry_run: dryRun,
    include_runtime: state.runtimeInput.checked,
    include_lighthouse: state.lighthouseInput.checked
  };
  if (!dryRun) {
    payload.activity_context = buildStudioActivityContext({
      pageId: "studio-risk",
      actionId: "run-risk-evidence",
      route: "/studio/risk/?mode=manage",
      controlId: "studioRiskRun",
      controlSelector: "#studioRiskRun",
      recordIdField: "run_id",
      recordId: runId
    });
  }
  return payload;
}

async function runRiskEvidence(state) {
  if (state.isRunning || !state.serviceAvailable) return;
  const payload = buildRunPayload(state);
  if (!payload.area) {
    setStatus(state.statusNode, "error", "Area is required.");
    return;
  }
  state.isRunning = true;
  syncBusy(state);
  setStatus(state.statusNode, "", getStudioText(state.config, "studio_risk.status_running", "Running risk evidence..."));
  try {
    const result = await postJson(RISK_API_ENDPOINTS.runs, payload);
    setStatus(
      state.statusNode,
      result.status === "passed" ? "success" : "error",
      result.status === "passed"
        ? getStudioText(state.config, "studio_risk.status_passed", "Risk evidence run completed.")
        : getStudioText(state.config, "studio_risk.status_failed", "Risk evidence run failed.")
    );
    if (result.run_id && !result.dry_run) {
      await loadRunSummary(state, result.run_id);
    } else {
      state.summaryLoaded = false;
      state.summaryNode.innerHTML = "";
    }
    await refreshRuns(state);
  } catch (error) {
    console.warn("studio_risk: risk run failed", error);
    setStatus(state.statusNode, "error", getStudioText(state.config, "studio_risk.status_request_failed", "Risk evidence request failed."));
  } finally {
    state.isRunning = false;
    syncBusy(state);
  }
}

async function init() {
  const bootStatus = document.getElementById("studioRiskBootStatus");
  const root = document.getElementById("studioRiskRoot");
  const introNode = document.getElementById("studioRiskIntro");
  const statusNode = document.getElementById("studioRiskStatus");
  const form = document.getElementById("studioRiskForm");
  const appSelect = document.getElementById("studioRiskApp");
  const areaInput = document.getElementById("studioRiskArea");
  const runIdInput = document.getElementById("studioRiskRunId");
  const dryRunInput = document.getElementById("studioRiskDryRun");
  const runtimeInput = document.getElementById("studioRiskRuntime");
  const lighthouseInput = document.getElementById("studioRiskLighthouse");
  const runButton = document.getElementById("studioRiskRun");
  const summaryNode = document.getElementById("studioRiskSummary");
  const runsNode = document.getElementById("studioRiskRuns");
  const required = collectOperationalRouteElements({
    bootStatus,
    root,
    introNode,
    statusNode,
    form,
    appSelect,
    areaInput,
    runIdInput,
    dryRunInput,
    runtimeInput,
    lighthouseInput,
    runButton,
    summaryNode,
    runsNode
  });
  if (!required.ok) return;

  initializeStudioRouteState(root, { route: "studio-risk", mode: "idle" });

  try {
    const config = await loadStudioConfigWithText("studio_risk");
    const serviceAvailable = await probeRiskApiHealth();
    const state = {
      config,
      root,
      introNode,
      statusNode,
      form,
      appSelect,
      areaInput,
      runIdInput,
      dryRunInput,
      runtimeInput,
      lighthouseInput,
      runButton,
      summaryNode,
      runsNode,
      serviceAvailable,
      isRunning: false,
      summaryLoaded: false
    };

    setText(introNode, getStudioText(config, "studio_risk.intro", "Run and review local risk evidence packs."));
    setText(document.getElementById("studioRiskAppLabel"), getStudioText(config, "studio_risk.app_label", "app"));
    setText(document.getElementById("studioRiskAreaLabel"), getStudioText(config, "studio_risk.area_label", "area"));
    setText(document.getElementById("studioRiskRunIdLabel"), getStudioText(config, "studio_risk.run_id_label", "run id"));
    setText(document.getElementById("studioRiskDryRunLabel"), getStudioText(config, "studio_risk.dry_run_label", "dry run"));
    setText(document.getElementById("studioRiskRuntimeLabel"), getStudioText(config, "studio_risk.runtime_label", "runtime checks"));
    setText(document.getElementById("studioRiskLighthouseLabel"), getStudioText(config, "studio_risk.lighthouse_label", "Lighthouse hook"));
    setText(document.getElementById("studioRiskRunsTitle"), getStudioText(config, "studio_risk.latest_runs_label", "recent runs"));
    setText(document.getElementById("studioRiskSummaryTitle"), getStudioText(config, "studio_risk.summary_label", "summary"));
    setStatus(
      statusNode,
      serviceAvailable ? "" : "error",
      serviceAvailable
        ? getStudioText(config, "studio_risk.idle_status", "Choose an app and area.")
        : getStudioText(config, "studio_risk.service_unavailable", "Risk API unavailable. Start bin/local-studio to run risk evidence.")
    );

    let producers = null;
    if (serviceAvailable) {
      producers = await getJson(RISK_API_ENDPOINTS.producers);
    }
    renderApps(state, producers && producers.apps);
    runIdInput.value = defaultRunId(state);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runRiskEvidence(state).catch((error) => console.warn("studio_risk: unexpected run failure", error));
    });
    for (const input of [appSelect, areaInput]) {
      input.addEventListener("input", () => {
        if (!normalizeText(runIdInput.value)) runIdInput.value = defaultRunId(state);
        syncBusy(state);
      });
    }
    runsNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-risk-run-id]") : null;
      if (!button) return;
      loadRunSummary(state, normalizeText(button.getAttribute("data-risk-run-id"))).catch((error) => {
        console.warn("studio_risk: summary load failed", error);
      });
    });
    syncBusy(state);
    await refreshRuns(state);

    root.hidden = false;
    bootStatus.hidden = true;
    markReady(state, true);
  } catch (error) {
    console.warn("studio_risk: init failed", error);
    bootStatus.textContent = "Failed to load Studio risk.";
    bootStatus.setAttribute("data-state", "error");
    root.hidden = false;
    markReady({ root, serviceAvailable: false, isRunning: false, summaryLoaded: false }, true);
  }
}

init();
