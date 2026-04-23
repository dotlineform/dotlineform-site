import { getStudioText, loadStudioConfig } from "./studio-config.js";
import {
  DOCS_MANAGEMENT_ENDPOINTS,
  postJson,
  probeDocsManagementHealth
} from "./studio-transport.js";

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

function linkHtml(label, href) {
  const text = normalizeText(label) || normalizeText(href) || "link";
  const url = normalizeText(href) || "#";
  return `<a class="docsBrokenLinksRow__link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`;
}

function renderRows(config, entries) {
  const labels = {
    problem: getStudioText(config, "docs_broken_links.column_problem", "problem"),
    linkedPage: getStudioText(config, "docs_broken_links.column_linked_page", "linked page"),
    link: getStudioText(config, "docs_broken_links.column_link", "link"),
    fromPage: getStudioText(config, "docs_broken_links.column_from_page", "from page")
  };

  return entries.map((entry) => {
    const problem = normalizeText(entry.problem);
    return `
      <li class="tagStudioList__row docsBrokenLinksRow">
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.problem)}">
          <span class="docsBrokenLinksRow__problem" data-problem="${escapeHtml(problem)}">${escapeHtml(problem)}</span>
        </span>
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.linkedPage)}">
          ${linkHtml(entry.linked_page_text, entry.linked_page_url)}
        </span>
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.link)}">
          ${linkHtml(entry.link_text, entry.link_url)}
        </span>
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.fromPage)}">
          ${linkHtml(entry.from_page_text, entry.from_page_url)}
        </span>
      </li>
    `;
  }).join("");
}

function renderResults(config, mountNode, payload) {
  const entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
  if (!entries.length) {
    mountNode.innerHTML = "";
    mountNode.hidden = true;
    return;
  }

  const problemLabel = getStudioText(config, "docs_broken_links.column_problem", "problem");
  const linkedPageLabel = getStudioText(config, "docs_broken_links.column_linked_page", "linked page");
  const linkLabel = getStudioText(config, "docs_broken_links.column_link", "link");
  const fromPageLabel = getStudioText(config, "docs_broken_links.column_from_page", "from page");

  mountNode.innerHTML = `
    <div class="tagStudioList__head docsBrokenLinksPage__head">
      <span class="tagStudioList__headLabel">${escapeHtml(problemLabel)}</span>
      <span class="tagStudioList__headLabel">${escapeHtml(linkedPageLabel)}</span>
      <span class="tagStudioList__headLabel">${escapeHtml(linkLabel)}</span>
      <span class="tagStudioList__headLabel">${escapeHtml(fromPageLabel)}</span>
    </div>
    <ol class="tagStudioList__rows">${renderRows(config, entries)}</ol>
  `;
  mountNode.hidden = false;
}

function summaryText(config, payload) {
  const summary = payload && payload.summary && typeof payload.summary === "object" ? payload.summary : {};
  const total = Number(summary.total || 0);
  const notFound = Number(summary.not_found || 0);
  const wrongTitle = Number(summary.wrong_title || 0);
  if (!total) {
    return getStudioText(config, "docs_broken_links.meta_summary_zero", "No broken links found.");
  }
  return getStudioText(
    config,
    "docs_broken_links.meta_summary",
    "{count} issue(s): {not_found} not found, {wrong_title} wrong title.",
    {
      count: total,
      not_found: notFound,
      wrong_title: wrongTitle
    }
  );
}

function selectedScopeFromUrl() {
  try {
    const url = new URL(window.location.href);
    const scope = normalizeText(url.searchParams.get("scope")).toLowerCase();
    return scope === "library" ? "library" : "studio";
  } catch (_error) {
    return "studio";
  }
}

function persistSelectedScope(scope) {
  try {
    const url = new URL(window.location.href);
    url.searchParams.set("scope", scope);
    window.history.replaceState({}, "", url.toString());
  } catch (_error) {
    // Ignore URL sync errors in constrained runtimes.
  }
}

async function runAudit(state) {
  const scope = normalizeText(state.scopeSelect.value).toLowerCase() === "library" ? "library" : "studio";
  persistSelectedScope(scope);
  state.runButton.disabled = true;
  state.emptyNode.hidden = true;
  setText(state.metaNode, "");
  state.listWrap.hidden = true;
  state.listWrap.innerHTML = "";
  setStatus(
    state.statusNode,
    "",
    getStudioText(state.config, "docs_broken_links.status_running", "Running docs broken-links audit…")
  );

  try {
    const payload = await postJson(DOCS_MANAGEMENT_ENDPOINTS.brokenLinks, { scope });
    const entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
    setText(state.metaNode, summaryText(state.config, payload));
    if (!entries.length) {
      setStatus(
        state.statusNode,
        "success",
        getStudioText(state.config, "docs_broken_links.status_success_empty", "No broken links found.")
      );
      setText(
        state.emptyNode,
        getStudioText(state.config, "docs_broken_links.empty_state", "No broken links found for this scope.")
      );
      state.emptyNode.hidden = false;
      state.listWrap.hidden = true;
      state.listWrap.innerHTML = "";
      return;
    }

    renderResults(state.config, state.listWrap, payload);
    setStatus(
      state.statusNode,
      "warn",
      getStudioText(state.config, "docs_broken_links.status_success", "Audit complete.")
    );
  } catch (error) {
    console.warn("docs_broken_links: audit failed", error);
    setText(state.metaNode, "");
    state.listWrap.hidden = true;
    state.listWrap.innerHTML = "";
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "docs_broken_links.status_failed", "Failed to run docs broken-links audit.")
    );
  } finally {
    state.runButton.disabled = false;
  }
}

async function init() {
  const bootStatus = document.getElementById("docsBrokenLinksBootStatus");
  const root = document.getElementById("docsBrokenLinksRoot");
  const introNode = document.getElementById("docsBrokenLinksIntro");
  const scopeLabel = document.getElementById("docsBrokenLinksScopeLabel");
  const scopeSelect = document.getElementById("docsBrokenLinksScope");
  const runButton = document.getElementById("docsBrokenLinksRun");
  const statusNode = document.getElementById("docsBrokenLinksStatus");
  const metaNode = document.getElementById("docsBrokenLinksMeta");
  const listWrap = document.getElementById("docsBrokenLinksListWrap");
  const emptyNode = document.getElementById("docsBrokenLinksEmpty");
  if (
    !bootStatus || !root || !introNode || !scopeLabel || !scopeSelect || !runButton || !statusNode || !metaNode || !listWrap || !emptyNode
  ) {
    return;
  }

  try {
    const config = await loadStudioConfig();
    const serviceAvailable = await probeDocsManagementHealth();

    setText(
      introNode,
      getStudioText(
        config,
        "docs_broken_links.intro",
        "Run a strict docs-viewer link audit for Studio or Library docs."
      )
    );
    setText(scopeLabel, getStudioText(config, "docs_broken_links.scope_label", "scope"));
    setText(runButton, getStudioText(config, "docs_broken_links.run_button", "Run broken links"));
    scopeSelect.innerHTML = `
      <option value="studio">${escapeHtml(getStudioText(config, "docs_broken_links.scope_option_studio", "studio"))}</option>
      <option value="library">${escapeHtml(getStudioText(config, "docs_broken_links.scope_option_library", "library"))}</option>
    `;
    scopeSelect.value = selectedScopeFromUrl();
    scopeSelect.addEventListener("change", () => {
      persistSelectedScope(scopeSelect.value);
    });

    const state = {
      config,
      scopeSelect,
      runButton,
      statusNode,
      metaNode,
      listWrap,
      emptyNode
    };
    runButton.addEventListener("click", () => {
      runAudit(state).catch((error) => console.warn("docs_broken_links: unexpected run failure", error));
    });

    root.hidden = false;
    bootStatus.hidden = true;

    if (!serviceAvailable) {
      runButton.disabled = true;
      setStatus(
        statusNode,
        "error",
        getStudioText(
          config,
          "docs_broken_links.service_unavailable",
          "Docs management service unavailable. Start bin/dev-studio to run the audit."
        )
      );
      return;
    }

    setStatus(
      statusNode,
      "",
      getStudioText(config, "docs_broken_links.idle_status", "Select a scope and run the audit.")
    );
  } catch (error) {
    console.warn("docs_broken_links: init failed", error);
    bootStatus.textContent = "Failed to load docs broken links.";
    bootStatus.setAttribute("data-state", "error");
  }
}

init();
