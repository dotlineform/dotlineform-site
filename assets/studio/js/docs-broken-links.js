import { getStudioText, loadStudioConfig } from "./studio-config.js";
import {
  DOCS_MANAGEMENT_ENDPOINTS,
  postJson,
  probeDocsManagementHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

const FILTERS = Object.freeze([
  { key: "all", problem: "", labelKey: "filter_all", fallback: "all" },
  { key: "not_found", problem: "not found", labelKey: "filter_not_found", fallback: "not found" },
  { key: "wrong_title", problem: "wrong title", labelKey: "filter_wrong_title", fallback: "wrong title" }
]);

const DEFAULT_FILTER_KEY = "not_found";
const DEFAULT_SORT_KEY = "fromPage";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["problem", "fromPage", "linkedPage", "link"]);

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
  return {
    route: "docs-broken-links",
    mode: state.entries.length ? "results" : "idle",
    service: state.serviceAvailable ? "available" : "unavailable",
    recordLoaded: state.entries.length > 0
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.root, Boolean(state.isRunning), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.root, ready, routeStateDetail(state));
}

function linkHtml(label, href) {
  const text = normalizeText(label) || normalizeText(href) || "link";
  const url = normalizeText(href) || "#";
  return `<a class="docsBrokenLinksRow__link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`;
}

function problemFilterKey(problem) {
  const normalized = normalizeText(problem);
  const found = FILTERS.find((filter) => filter.problem === normalized);
  return found ? found.key : "";
}

function countEntries(entries) {
  const counts = { all: entries.length, not_found: 0, wrong_title: 0 };
  entries.forEach((entry) => {
    const key = problemFilterKey(entry.problem);
    if (key && key !== "all") counts[key] = (counts[key] || 0) + 1;
  });
  return counts;
}

function filterEntries(entries, filterKey) {
  const filter = FILTERS.find((item) => item.key === filterKey) || FILTERS[1];
  if (!filter.problem) return entries.slice();
  return entries.filter((entry) => normalizeText(entry.problem) === filter.problem);
}

function sortValue(entry, sortKey) {
  if (sortKey === "problem") return normalizeText(entry.problem);
  if (sortKey === "linkedPage") return normalizeText(entry.linked_page_text || entry.linked_page_url);
  if (sortKey === "link") return normalizeText(entry.link_text || entry.link_url);
  return normalizeText(entry.from_page_text || entry.from_page_url);
}

function compareText(left, right) {
  return normalizeText(left).localeCompare(normalizeText(right), undefined, {
    numeric: true,
    sensitivity: "base"
  });
}

function compareEntries(a, b, sortKey, sortDir) {
  const direction = sortDir === "desc" ? -1 : 1;
  const selected = compareText(sortValue(a, sortKey), sortValue(b, sortKey));
  if (selected !== 0) return selected * direction;
  for (const key of SORT_KEYS) {
    if (key === sortKey) continue;
    const fallback = compareText(sortValue(a, key), sortValue(b, key));
    if (fallback !== 0) return fallback;
  }
  return 0;
}

function sortedVisibleEntries(state) {
  return filterEntries(state.entries, state.filterKey)
    .sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));
}

function sortIndicator(state, sortKey) {
  if (state.sortKey !== sortKey) return "";
  const marker = state.sortDir === "desc" ? "↓" : "↑";
  return `<span class="tagStudioList__sortIndicator" aria-hidden="true">${marker}</span>`;
}

function sortButton(state, sortKey, label) {
  const active = state.sortKey === sortKey;
  return `
    <button type="button" class="tagStudioList__sortBtn" data-sort-key="${escapeHtml(sortKey)}" data-state="${active ? "active" : ""}">
      ${escapeHtml(label)}${sortIndicator(state, sortKey)}
    </button>
  `;
}

function renderFilters(state) {
  const counts = countEntries(state.entries);
  state.filterNode.innerHTML = FILTERS.map((filter) => {
    const label = getStudioText(state.config, `docs_broken_links.${filter.labelKey}`, filter.fallback);
    const count = Number(counts[filter.key] || 0);
    const active = state.filterKey === filter.key;
    return `
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-filter-key="${escapeHtml(filter.key)}" data-state="${active ? "active" : ""}" aria-pressed="${active ? "true" : "false"}">
        ${escapeHtml(label)} [${count}]
      </button>
    `;
  }).join("");
  state.filterNode.hidden = false;
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
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.fromPage)}">
          ${linkHtml(entry.from_page_text, entry.from_page_url)}
        </span>
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.linkedPage)}">
          ${linkHtml(entry.linked_page_text, entry.linked_page_url)}
        </span>
        <span class="docsBrokenLinksRow__cell" data-label="${escapeHtml(labels.link)}">
          ${linkHtml(entry.link_text, entry.link_url)}
        </span>
      </li>
    `;
  }).join("");
}

function renderResults(state) {
  renderFilters(state);
  const entries = sortedVisibleEntries(state);
  if (!entries.length) {
    state.listWrap.innerHTML = "";
    state.listWrap.hidden = true;
    setText(
      state.emptyNode,
      getStudioText(state.config, "docs_broken_links.filter_empty_state", "No broken links found for this filter.")
    );
    state.emptyNode.hidden = false;
    return;
  }

  state.emptyNode.hidden = true;
  const problemLabel = getStudioText(state.config, "docs_broken_links.column_problem", "problem");
  const linkedPageLabel = getStudioText(state.config, "docs_broken_links.column_linked_page", "linked page");
  const linkLabel = getStudioText(state.config, "docs_broken_links.column_link", "link");
  const fromPageLabel = getStudioText(state.config, "docs_broken_links.column_from_page", "from page");

  state.listWrap.innerHTML = `
    <div class="tagStudioList__head docsBrokenLinksPage__head">
      ${sortButton(state, "problem", problemLabel)}
      ${sortButton(state, "fromPage", fromPageLabel)}
      ${sortButton(state, "linkedPage", linkedPageLabel)}
      ${sortButton(state, "link", linkLabel)}
    </div>
    <ol class="tagStudioList__rows">${renderRows(state.config, entries)}</ol>
  `;
  state.listWrap.hidden = false;
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
  state.isRunning = true;
  syncRouteBusyState(state);
  state.runButton.disabled = true;
  state.emptyNode.hidden = true;
  state.filterNode.hidden = true;
  state.filterNode.innerHTML = "";
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
    state.entries = entries;
    state.filterKey = DEFAULT_FILTER_KEY;
    state.sortKey = DEFAULT_SORT_KEY;
    state.sortDir = DEFAULT_SORT_DIR;
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
      state.filterNode.hidden = true;
      state.filterNode.innerHTML = "";
      state.listWrap.hidden = true;
      state.listWrap.innerHTML = "";
      return;
    }

    renderResults(state);
    setStatus(
      state.statusNode,
      "warn",
      getStudioText(state.config, "docs_broken_links.status_success", "Audit complete.")
    );
  } catch (error) {
    console.warn("docs_broken_links: audit failed", error);
    state.entries = [];
    state.filterNode.hidden = true;
    state.filterNode.innerHTML = "";
    state.listWrap.hidden = true;
    state.listWrap.innerHTML = "";
    setStatus(
      state.statusNode,
      "error",
      getStudioText(state.config, "docs_broken_links.status_failed", "Failed to run docs broken-links audit.")
    );
  } finally {
    state.isRunning = false;
    state.runButton.disabled = false;
    syncRouteBusyState(state);
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
  const filterNode = document.getElementById("docsBrokenLinksFilters");
  const listWrap = document.getElementById("docsBrokenLinksListWrap");
  const emptyNode = document.getElementById("docsBrokenLinksEmpty");
  if (
    !bootStatus || !root || !introNode || !scopeLabel || !scopeSelect || !runButton || !statusNode || !filterNode || !listWrap || !emptyNode
  ) {
    return;
  }
  initializeStudioRouteState(root, { route: "docs-broken-links" });

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
      filterNode,
      listWrap,
      emptyNode,
      root,
      serviceAvailable,
      isRunning: false,
      entries: [],
      filterKey: DEFAULT_FILTER_KEY,
      sortKey: DEFAULT_SORT_KEY,
      sortDir: DEFAULT_SORT_DIR
    };
    runButton.addEventListener("click", () => {
      runAudit(state).catch((error) => console.warn("docs_broken_links: unexpected run failure", error));
    });
    filterNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-filter-key]") : null;
      if (!button) return;
      const filterKey = normalizeText(button.getAttribute("data-filter-key"));
      if (!FILTERS.some((filter) => filter.key === filterKey)) return;
      state.filterKey = filterKey;
      renderResults(state);
    });
    listWrap.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-sort-key]") : null;
      if (!button) return;
      const sortKey = normalizeText(button.getAttribute("data-sort-key"));
      if (!SORT_KEYS.includes(sortKey)) return;
      if (state.sortKey === sortKey) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = sortKey;
        state.sortDir = "asc";
      }
      renderResults(state);
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
      markRouteReady(state, true);
      return;
    }

    setStatus(
      statusNode,
      "",
      getStudioText(config, "docs_broken_links.idle_status", "Select a scope and run the audit.")
    );
    markRouteReady(state, true);
  } catch (error) {
    console.warn("docs_broken_links: init failed", error);
    bootStatus.textContent = "Failed to load docs broken links.";
    bootStatus.setAttribute("data-state", "error");
    root.hidden = false;
    const fallbackState = {
      root,
      serviceAvailable: false,
      isRunning: false,
      entries: []
    };
    markRouteReady(fallbackState, true);
  }
}

init();
