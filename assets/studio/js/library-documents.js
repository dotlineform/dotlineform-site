import {
  getDocsScopeDataPath,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  DOCS_MANAGEMENT_ENDPOINTS
} from "./studio-transport.js";

const DOCS_SCOPE = "library";
const DEFAULT_SORT_KEY = "doc_id";
const VALID_SORT_KEYS = {
  doc_id: true,
  added_date: true,
  title: true
};
const FILTERS = [
  { key: "viewable", labelKey: "filter_viewable", fallback: "viewable [{count}]" },
  { key: "parent", labelKey: "filter_parent", fallback: "parent [{count}]" }
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

function routeDetail(mode, recordLoaded) {
  return {
    route: "library-documents",
    mode,
    recordLoaded: Boolean(recordLoaded)
  };
}

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function docsGeneratedIndexUrl(scope) {
  const url = new URL(DOCS_MANAGEMENT_ENDPOINTS.generatedIndex);
  url.searchParams.set("scope", scope);
  return url.href;
}

function staticDocsIndexUrl(config, scope) {
  return getDocsScopeDataPath(config, scope, "index") || `/assets/data/docs/scopes/${scope}/index.json`;
}

function shouldPreferDocsManagementIndex() {
  const localHosts = new Set(["127.0.0.1", "localhost", "::1"]);
  return localHosts.has(window.location.hostname) && (window.location.port === "4000" || window.location.port === "");
}

async function loadDocsIndex(config, scope) {
  const staticUrl = staticDocsIndexUrl(config, scope);
  const generatedUrl = docsGeneratedIndexUrl(scope);
  const urls = shouldPreferDocsManagementIndex()
    ? [generatedUrl, staticUrl]
    : [staticUrl, generatedUrl];
  let lastError = null;
  for (const url of urls) {
    try {
      return await loadJson(url);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("No Library documents index available.");
}

function docId(doc) {
  return normalizeText(doc && doc.doc_id);
}

function docTitle(doc) {
  return normalizeText(doc && doc.title) || docId(doc);
}

function docAddedDate(doc) {
  return normalizeText(doc && doc.added_date);
}

function docIsViewable(doc) {
  return doc && doc.viewable === true;
}

function buildParentIdSet(docs) {
  const ids = new Set(docs.map(docId).filter(Boolean));
  const parentIds = new Set();
  docs.forEach((doc) => {
    const parentId = normalizeText(doc && doc.parent_id);
    if (parentId && ids.has(parentId)) parentIds.add(parentId);
  });
  return parentIds;
}

function docIsParent(state, doc) {
  return state.parentIds.has(docId(doc));
}

function docManageHref(doc, id) {
  const href = normalizeText(doc && doc.viewer_url) || `/library/?doc=${encodeURIComponent(id)}`;
  const url = new URL(href, window.location.origin);
  url.searchParams.set("mode", "manage");
  if (!normalizeText(url.searchParams.get("doc")) && id) {
    url.searchParams.set("doc", id);
  }
  if (url.origin === window.location.origin) {
    return `${url.pathname}${url.search}${url.hash}`;
  }
  return url.href;
}

function filterCounts(state) {
  return {
    viewable: state.docs.filter((doc) => docIsViewable(doc)).length,
    parent: state.docs.filter((doc) => docIsParent(state, doc)).length
  };
}

function docMatchesFilters(state, doc) {
  if (state.filters.viewable && !docIsViewable(doc)) return false;
  if (state.filters.parent && !docIsParent(state, doc)) return false;
  return true;
}

function compareDocs(state, a, b) {
  const key = state.sortKey;
  let av = "";
  let bv = "";
  if (key === "added_date") {
    av = docAddedDate(a);
    bv = docAddedDate(b);
  } else if (key === "title") {
    av = docTitle(a);
    bv = docTitle(b);
  } else {
    av = docId(a);
    bv = docId(b);
  }
  const primary = state.collator.compare(av, bv);
  if (primary !== 0) return state.sortDir === "asc" ? primary : -primary;
  return state.collator.compare(docId(a), docId(b));
}

function renderFilters(state) {
  const counts = filterCounts(state);
  state.filterNode.innerHTML = FILTERS.map((filter) => {
    const active = Boolean(state.filters[filter.key]);
    const count = Number(counts[filter.key] || 0);
    const label = getStudioText(state.config, `library_documents.${filter.labelKey}`, filter.fallback, { count });
    return `
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-library-documents-filter="${escapeHtml(filter.key)}" data-state="${active ? "active" : ""}" aria-pressed="${active ? "true" : "false"}">
        ${escapeHtml(label)}
      </button>
    `;
  }).join("");
}

function updateHeaderState(state) {
  state.sortButtons.forEach((button) => {
    const key = normalizeText(button.getAttribute("data-library-documents-sort"));
    const active = key === state.sortKey;
    const indicator = button.querySelector(".tagStudioList__sortIndicator");
    if (active) {
      button.dataset.state = "active";
    } else {
      delete button.dataset.state;
    }
    if (indicator) indicator.textContent = active ? (state.sortDir === "asc" ? "▲" : "▼") : "";
  });
}

function renderRows(state) {
  const docs = state.docs
    .filter((doc) => docMatchesFilters(state, doc))
    .slice()
    .sort((a, b) => compareDocs(state, a, b));

  state.rowsNode.innerHTML = docs.map((doc) => {
    const id = docId(doc);
    const title = docTitle(doc);
    const addedDate = docAddedDate(doc);
    const href = docManageHref(doc, id);
    const viewable = docIsViewable(doc);
    const parent = docIsParent(state, doc);
    return `
      <li class="tagStudioList__row tagStudioList__row--start libraryDocumentsList__row" data-library-document="${escapeHtml(id)}">
        <a class="tagStudioList__cellLink libraryDocumentsList__docId" href="${escapeHtml(href)}">${escapeHtml(id)}</a>
        <span class="tagStudioList__cellMeta libraryDocumentsList__date">${escapeHtml(addedDate)}</span>
        <span class="libraryDocumentsList__parentTick" aria-label="${parent ? "parent document" : ""}">${parent ? "✓" : ""}</span>
        <span class="libraryDocumentsList__viewable${viewable ? " is-viewable" : ""}" aria-label="${viewable ? "viewable" : "not viewable"}"></span>
        <a class="tagStudioList__cellLink tagStudioList__cellTitle libraryDocumentsList__title" href="${escapeHtml(href)}">${escapeHtml(title)}</a>
      </li>
    `;
  }).join("");

  const statusKey = docs.length === 1 ? "status_one" : "status";
  const fallback = docs.length === 1 ? "1 document" : "{count} documents";
  setText(state.statusNode, getStudioText(state.config, `library_documents.${statusKey}`, fallback, { count: docs.length }));
}

function persistSort(state) {
  const url = new URL(window.location.href);
  if (state.sortKey === DEFAULT_SORT_KEY && state.sortDir === "asc") {
    url.searchParams.delete("sort");
    url.searchParams.delete("dir");
  } else {
    url.searchParams.set("sort", state.sortKey);
    url.searchParams.set("dir", state.sortDir);
  }
  window.history.replaceState({}, "", url.toString());
}

function attachEvents(state) {
  state.sortButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const key = normalizeText(button.getAttribute("data-library-documents-sort"));
      if (!VALID_SORT_KEYS[key]) return;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      renderRows(state);
      updateHeaderState(state);
      persistSort(state);
    });
  });

  state.filterNode.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const button = event.target.closest("[data-library-documents-filter]");
    if (!button) return;
    const key = normalizeText(button.getAttribute("data-library-documents-filter"));
    if (!Object.prototype.hasOwnProperty.call(state.filters, key)) return;
    state.filters[key] = !state.filters[key];
    renderFilters(state);
    renderRows(state);
  });
}

async function initLibraryDocumentsPage() {
  const root = document.getElementById("libraryDocumentsRoot");
  const bootStatus = document.getElementById("libraryDocumentsBootStatus");
  const statusNode = document.getElementById("libraryDocumentsStatus");
  const filterNode = document.getElementById("libraryDocumentsFilters");
  const rowsNode = document.getElementById("libraryDocumentsRows");
  if (!root || !statusNode || !filterNode || !rowsNode) return;

  initializeStudioRouteState(root, routeDetail("list", false));
  setStudioRouteBusy(root, true, routeDetail("list", false));

  const params = new URLSearchParams(window.location.search);
  let sortKey = normalizeText(params.get("sort")).toLowerCase();
  if (!VALID_SORT_KEYS[sortKey]) sortKey = DEFAULT_SORT_KEY;
  let sortDir = normalizeText(params.get("dir")).toLowerCase();
  if (sortDir !== "asc" && sortDir !== "desc") sortDir = "asc";

  const state = {
    root,
    bootStatus,
    statusNode,
    filterNode,
    rowsNode,
    sortButtons: Array.from(root.querySelectorAll("[data-library-documents-sort]")),
    config: null,
    docs: [],
    parentIds: new Set(),
    filters: {
      viewable: false,
      parent: false
    },
    sortKey,
    sortDir,
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
  };

  try {
    const config = await loadStudioConfig().catch(() => null);
    state.config = config;
    const payload = await loadDocsIndex(state.config, DOCS_SCOPE);
    state.docs = Array.isArray(payload && payload.docs)
      ? payload.docs.filter((doc) => docId(doc))
      : [];
    state.parentIds = buildParentIdSet(state.docs);
    renderFilters(state);
    renderRows(state);
    updateHeaderState(state);
    attachEvents(state);
    root.hidden = false;
    if (bootStatus) bootStatus.hidden = true;
    setStudioRouteBusy(root, false, routeDetail(state.docs.length ? "list" : "empty", state.docs.length > 0));
    setStudioRouteReady(root, true, routeDetail(state.docs.length ? "list" : "empty", state.docs.length > 0));
  } catch (error) {
    console.error("library_documents: load failed", error);
    root.hidden = false;
    if (bootStatus) bootStatus.hidden = true;
    setText(statusNode, getStudioText(state.config, "library_documents.load_failed", "Failed to load Library documents."));
    setStudioRouteBusy(root, false, routeDetail("empty", false));
    setStudioRouteReady(root, true, routeDetail("empty", false));
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLibraryDocumentsPage);
} else {
  initLibraryDocumentsPage();
}
