import { getStudioText, loadStudioConfig } from "./studio-config.js";
import {
  AUDIT_SERVICE_ENDPOINTS,
  getJson,
  postJson,
  probeAuditServiceHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

const FALLBACK_AUDITS = Object.freeze([
  {
    audit_id: "studio-ready-state",
    label: "Studio ready state",
    description: "Checks Studio route-ready template contracts and static-route drift."
  }
]);

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

function routeStateDetail(state) {
  let mode = "summary";
  if (!state.serviceAvailable) {
    mode = "unavailable";
  } else if (state.isRunning) {
    mode = "running";
  } else if (state.lastResults.size) {
    mode = "result";
  }
  return {
    route: "studio-audits",
    mode,
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: state.lastResults.size > 0
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function normalizeAudits(rawAudits) {
  const audits = Array.isArray(rawAudits) ? rawAudits : [];
  const out = [];
  const seen = new Set();
  audits.forEach((raw) => {
    if (!raw || typeof raw !== "object") return;
    const auditId = normalizeText(raw.audit_id);
    if (!auditId || seen.has(auditId)) return;
    seen.add(auditId);
    out.push({
      audit_id: auditId,
      label: normalizeText(raw.label) || auditId,
      description: normalizeText(raw.description)
    });
  });
  return out.length ? out : FALLBACK_AUDITS.slice();
}

function formatCounts(result) {
  const summary = result && result.summary && typeof result.summary === "object" ? result.summary : {};
  const errors = Number(summary.errors || 0);
  const warnings = Number(summary.warnings || 0);
  return `${errors} error${errors === 1 ? "" : "s"}, ${warnings} warning${warnings === 1 ? "" : "s"}`;
}

function resultState(result) {
  const status = normalizeText(result && result.status).toLowerCase();
  if (status === "passed") return "success";
  if (status === "failed") return "error";
  return "";
}

function renderFindings(findings) {
  const rows = Array.isArray(findings) ? findings : [];
  if (!rows.length) return "";
  const items = rows.map((finding) => {
    const severity = normalizeText(finding && finding.severity);
    const path = normalizeText(finding && finding.path);
    const message = normalizeText(finding && finding.message);
    return `
      <li class="studioAuditsFinding">
        <span class="studioAuditsFinding__severity" data-severity="${escapeHtml(severity)}">${escapeHtml(severity)}</span>
        <span class="studioAuditsFinding__path">${escapeHtml(path)}</span>
        <span class="studioAuditsFinding__message">${escapeHtml(message)}</span>
      </li>
    `;
  }).join("");
  return `<ol class="studioAuditsFindingList">${items}</ol>`;
}

function renderResult(config, result) {
  if (!result) return "";
  const state = resultState(result);
  const status = normalizeText(result.status) || "unknown";
  const finished = normalizeText(result.finished_at);
  const counts = formatCounts(result);
  const exitCode = Number.isFinite(Number(result.exit_code)) ? Number(result.exit_code) : "";
  const stdout = normalizeText(result.stdout);
  return `
    <div class="studioAuditsResult" data-state="${escapeHtml(state)}">
      <p class="tagStudio__status studioAuditsResult__summary" data-state="${escapeHtml(state)}">
        ${escapeHtml(status)} · ${escapeHtml(counts)}${exitCode !== "" ? ` · exit ${escapeHtml(exitCode)}` : ""}
      </p>
      ${finished ? `<p class="studioAuditsResult__meta">${escapeHtml(finished)}</p>` : ""}
      ${renderFindings(result.findings)}
      ${stdout ? `
        <details class="studioAuditsResult__details">
          <summary>${escapeHtml(getStudioText(config, "studio_audits.output_label", "output"))}</summary>
          <pre>${escapeHtml(stdout)}</pre>
        </details>
      ` : ""}
    </div>
  `;
}

function renderAudits(state) {
  state.listNode.innerHTML = state.audits.map((audit) => {
    const result = state.lastResults.get(audit.audit_id);
    const runningThis = state.isRunning && state.runningAuditId === audit.audit_id;
    const disabled = state.isRunning || !state.serviceAvailable;
    return `
      <article class="tagStudio__panel tagStudio__panel--compact studioAuditsItem" data-audit-id="${escapeHtml(audit.audit_id)}">
        <div class="studioAuditsItem__body">
          <h3>${escapeHtml(audit.label)}</h3>
          ${audit.description ? `<p>${escapeHtml(audit.description)}</p>` : ""}
        </div>
        <div class="studioAuditsItem__actions">
          <button
            type="button"
            class="tagStudio__button tagStudio__button--defaultWidth"
            data-run-audit="${escapeHtml(audit.audit_id)}"
            ${disabled ? "disabled" : ""}
          >${escapeHtml(runningThis ? getStudioText(state.config, "studio_audits.running_button", "Running...") : getStudioText(state.config, "studio_audits.run_button", "Run audit"))}</button>
        </div>
        ${renderResult(state.config, result)}
      </article>
    `;
  }).join("");
}

async function runAudit(state, auditId) {
  if (state.isRunning || !state.serviceAvailable) return;
  state.isRunning = true;
  state.runningAuditId = auditId;
  syncRouteBusyState(state);
  renderAudits(state);
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "studio_audits.status_running", "Running audit...")
  );

  try {
    const result = await postJson(AUDIT_SERVICE_ENDPOINTS.run, { audit_id: auditId });
    state.lastResults.set(auditId, result);
    const stateName = resultState(result);
    setStatus(
      state.statusNode,
      stateName,
      stateName === "success"
        ? getStudioText(state.config, "studio_audits.status_passed", "Audit passed.")
        : getStudioText(state.config, "studio_audits.status_failed", "Audit failed.")
    );
  } catch (error) {
    console.warn("studio_audits: audit run failed", error);
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "studio_audits.status_request_failed", "Audit request failed.")
    );
  } finally {
    state.isRunning = false;
    state.runningAuditId = "";
    syncRouteBusyState(state);
    renderAudits(state);
  }
}

async function loadAudits(serviceAvailable) {
  if (!serviceAvailable) return FALLBACK_AUDITS.slice();
  const payload = await getJson(AUDIT_SERVICE_ENDPOINTS.audits);
  return normalizeAudits(payload && payload.audits);
}

async function init() {
  const bootStatus = document.getElementById("studioAuditsBootStatus");
  const root = document.getElementById("studioAuditsRoot");
  const introNode = document.getElementById("studioAuditsIntro");
  const statusNode = document.getElementById("studioAuditsStatus");
  const listNode = document.getElementById("studioAuditsList");
  if (!bootStatus || !root || !introNode || !statusNode || !listNode) return;

  initializeStudioRouteState(root, { route: "studio-audits", mode: "summary" });

  try {
    const config = await loadStudioConfig();
    const serviceAvailable = await probeAuditServiceHealth();
    const audits = await loadAudits(serviceAvailable);
    const state = {
      config,
      root,
      introNode,
      statusNode,
      listNode,
      serviceAvailable,
      audits,
      isRunning: false,
      runningAuditId: "",
      lastResults: new Map()
    };

    setText(
      introNode,
      getStudioText(config, "studio_audits.intro", "Run local Studio maintenance audits.")
    );
    setStatus(
      statusNode,
      serviceAvailable ? "" : "error",
      serviceAvailable
        ? getStudioText(config, "studio_audits.idle_status", "Select an audit to run.")
        : getStudioText(config, "studio_audits.service_unavailable", "Audit service unavailable. Start bin/dev-studio to run audits.")
    );
    renderAudits(state);
    listNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-run-audit]") : null;
      if (!button) return;
      const auditId = normalizeText(button.getAttribute("data-run-audit"));
      runAudit(state, auditId).catch((error) => console.warn("studio_audits: unexpected run failure", error));
    });

    root.hidden = false;
    bootStatus.hidden = true;
    markRouteReady(state, true);
  } catch (error) {
    console.warn("studio_audits: init failed", error);
    bootStatus.textContent = "Failed to load Studio audits.";
    bootStatus.setAttribute("data-state", "error");
    root.hidden = false;
    const fallbackState = {
      root,
      serviceAvailable: false,
      isRunning: false,
      lastResults: new Map()
    };
    markRouteReady(fallbackState, true);
  }
}

init();
