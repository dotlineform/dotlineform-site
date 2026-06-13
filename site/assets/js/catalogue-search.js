import {
  createCatalogueSearchResultCollator,
  createCatalogueSearchResultsProjection,
  normalizeCatalogueSearchEntries
} from "./search/catalogue-search-runtime.js";

let loadSearchPolicyFn = null;
let getSearchRuntimePolicyFn = null;
let getSearchScopePolicyFn = null;
let getSearchMessageFn = null;
let searchDepsPromise = null;
let createSearchPerformanceInstrumentationFn = null;
let estimatePayloadBytesFn = estimatePayloadBytesFallback;
let searchPerformanceDepsPromise = null;

const SITE_BASE_PATH = deriveSiteBasePath(import.meta.url);
const SEARCH_PERFORMANCE_STORAGE_KEY = "dlf.search.performance";
const SEARCH_PERFORMANCE_ENABLED_VALUES = new Set(["1", "true", "on", "yes", "panel", "console", "log"]);

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSearchPage);
} else {
  initSearchPage();
}

async function initSearchPage() {
  const root = document.getElementById("studioSearchRoot");
  if (!root) return;

  const backLink = document.getElementById("studioSearchBackLink");
  const scopeLabel = document.getElementById("studioSearchScope");
  const input = document.getElementById("studioSearchInput");
  const status = document.getElementById("studioSearchStatus");
  const results = document.getElementById("studioSearchResults");
  const more = document.getElementById("studioSearchMore");
  const performancePanel = document.getElementById("studioSearchPerformance");
  const performanceSummary = document.getElementById("studioSearchPerformanceSummary");
  const performanceReport = document.getElementById("studioSearchPerformanceReport");
  if (!input || !status || !results || !more) return;

  const instrumentation = await createSearchInstrumentation({
    panel: performancePanel,
    summary: performanceSummary,
    report: performanceReport
  });
  let policy = null;

  try {
    const depsTimer = instrumentation.timer();
    await loadSearchDeps();
    instrumentation.markPhase("dependencies", depsTimer.end());

    const policyTimer = instrumentation.timer();
    policy = await loadSearchPolicyFn(searchPolicyUrl());
    instrumentation.markPhase("policy", policyTimer.end());
    applyPerformanceText({ policy, performanceSummary });
    status.textContent = searchText(policy, "loading", "loading search index…");

    const scope = "catalogue";
    applyNavScopeState(scope);
    const scopePolicy = getSearchScopePolicyFn(policy, scope);
    if (!scopePolicy) {
      applyScopeText({ backLink, scopeLabel, input, scopePolicy: null, inputEnabled: false });
      showUnsupportedScopeState({ root, status, results, more, policy });
      return;
    }

    const runtimePolicy = getSearchRuntimePolicyFn(policy);
    applyScopeText({ backLink, scopeLabel, input, scopePolicy, inputEnabled: scopePolicy.enabled });

    if (!scopePolicy.enabled) {
      showUnsupportedScopeState({ root, status, results, more, policy });
      return;
    }

    const entries = await loadScopedSearchEntries(scopePolicy, instrumentation);
    const initialQuery = resolveQuery();
    input.value = initialQuery;
    const state = {
      policy,
      scope,
      scopePolicy,
      runtimePolicy,
      baseurl: String(root.dataset.baseurl || ""),
      input,
      status,
      results,
      more,
      entries,
      filterKind: "all",
      queryText: initialQuery,
      debounceId: null,
      visibleCount: runtimePolicy.initialBatchSize,
      matchCache: null,
        resultCollator: createCatalogueSearchResultCollator(),
        instrumentation
    };
    wireEvents(state);
    renderResults(state);
    root.hidden = false;
    input.focus();
  } catch (error) {
    root.hidden = false;
    status.textContent = searchText(policy, "load_failed_error", "Failed to load search data.");
    status.dataset.state = "error";
  }
}

async function loadScopedSearchEntries(scopePolicy, instrumentation) {
  const scope = scopePolicy ? scopePolicy.scope : "";
  try {
    const payloadResult = await loadSearchIndexPayload(scopePolicy, instrumentation);
    const payload = payloadResult.payload;
    const rawEntries = payload && Array.isArray(payload.entries) ? payload.entries : [];
    const normalizeTimer = instrumentation.timer();
    const entries = normalizeCatalogueSearchEntries(rawEntries, scopePolicy);
    const normalizeMs = normalizeTimer.end();
    instrumentation.recordScope({
      scope,
      source: payloadResult.source,
      status: "loaded",
      payloadBytes: payloadResult.payloadBytes,
      loadMs: payloadResult.loadMs,
      parseMs: payloadResult.parseMs,
      normalizeMs,
      rawEntries: rawEntries.length,
      normalizedEntries: entries.length
    });
    return entries;
  } catch (error) {
    instrumentation.recordScope({
      scope,
      source: "unknown",
      status: "failed",
      error
    });
    throw error;
  }
}

async function loadSearchIndexPayload(scopePolicy, instrumentation) {
  if (!instrumentation.enabled) {
    const loadTimer = instrumentation.timer();
    const payload = await loadSearchIndexJson(scopePolicy);
    return {
      payload,
      source: "static",
      payloadBytes: 0,
      loadMs: loadTimer.end(),
      parseMs: 0
    };
  }
  return loadStaticSearchIndexPayload(scopePolicy, instrumentation);
}

async function loadStaticSearchIndexPayload(scopePolicy, instrumentation) {
  const url = searchScopeIndexUrl(scopePolicy);
  if (!url) throw new Error(`Missing search index path for ${scopePolicy ? scopePolicy.scope : "scope"}`);
  const loadTimer = instrumentation.timer();
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  const text = await response.text();
  const loadMs = loadTimer.end();
  const parseTimer = instrumentation.timer();
  const payload = JSON.parse(text);
  return {
    payload,
    source: "static",
    payloadBytes: estimatePayloadBytesFn(text),
    loadMs,
    parseMs: parseTimer.end()
  };
}

async function loadSearchIndexJson(scopePolicy) {
  const url = searchScopeIndexUrl(scopePolicy);
  if (!url) throw new Error(`Missing search index path for ${scopePolicy ? scopePolicy.scope : "scope"}`);
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

function searchScopeIndexUrl(scopePolicy) {
  const path = scopePolicy && typeof scopePolicy.indexPath === "string" ? scopePolicy.indexPath.trim() : "";
  if (!path) return "";
  return withAssetVersion(resolveSiteAssetPath(path), readAssetVersion(import.meta.url));
}

async function loadSearchDeps() {
  if (!searchDepsPromise) {
    const assetVersion = readAssetVersion(import.meta.url);
    searchDepsPromise = import(withAssetVersion("./search/search-policy.js", assetVersion)).then((policyModule) => {
      loadSearchPolicyFn = policyModule.loadSearchPolicy;
      getSearchRuntimePolicyFn = policyModule.getSearchRuntimePolicy;
      getSearchScopePolicyFn = policyModule.getSearchScopePolicy;
      getSearchMessageFn = policyModule.getSearchMessage;
    });
  }
  return searchDepsPromise;
}

async function createSearchInstrumentation(options) {
  if (!shouldLoadSearchPerformanceDeps()) {
    if (options.panel) options.panel.hidden = true;
    return createDisabledSearchInstrumentation();
  }

  try {
    await loadSearchPerformanceDeps();
    return createSearchPerformanceInstrumentationFn(options);
  } catch (error) {
    console.warn("search_performance: disabled after instrumentation load failure", error);
    if (options.panel) options.panel.hidden = true;
    return createDisabledSearchInstrumentation();
  }
}

async function loadSearchPerformanceDeps() {
  if (!searchPerformanceDepsPromise) {
    const assetVersion = readAssetVersion(import.meta.url);
    searchPerformanceDepsPromise = import(withAssetVersion("./search/search-performance.js", assetVersion)).then((performanceModule) => {
      createSearchPerformanceInstrumentationFn = performanceModule.createSearchPerformanceInstrumentation;
      estimatePayloadBytesFn = performanceModule.estimatePayloadBytes;
    });
  }
  return searchPerformanceDepsPromise;
}

function shouldLoadSearchPerformanceDeps() {
  const location = typeof window !== "undefined" ? window.location : null;
  const params = new URLSearchParams(location && location.search ? location.search : "");
  const flag = firstNonEmpty([
    params.get("searchPerf"),
    params.get("search_performance"),
    params.get("perf")
  ]);
  if (flag && SEARCH_PERFORMANCE_ENABLED_VALUES.has(flag.toLowerCase())) {
    return true;
  }
  if (params.get("debug") === "search-performance") {
    return true;
  }

  try {
    const storage = typeof window !== "undefined" ? window.localStorage : null;
    const stored = storage ? String(storage.getItem(SEARCH_PERFORMANCE_STORAGE_KEY) || "").trim().toLowerCase() : "";
    return SEARCH_PERFORMANCE_ENABLED_VALUES.has(stored);
  } catch (_error) {
    return false;
  }
}

function createDisabledSearchInstrumentation() {
  return {
    enabled: false,
    mode: "",
    getSnapshot: () => ({ enabled: false, mode: "", elapsedMs: 0, phases: [], scopes: [], queries: [] }),
    markPhase: () => {},
    recordScope: () => {},
    recordQuery: () => {},
    timer: () => ({ end: () => 0 })
  };
}

function wireEvents(state) {
  state.input.addEventListener("input", () => {
    state.queryText = String(state.input.value || "");
    if (!state.runtimePolicy.liveSearch) return;

    if (state.debounceId != null) {
      window.clearTimeout(state.debounceId);
    }
    state.debounceId = window.setTimeout(() => {
      state.debounceId = null;
      resetVisibleCount(state);
      renderResults(state);
    }, state.runtimePolicy.debounceMs);
  });

  state.input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || !state.runtimePolicy.enterRunsSearch) return;
    if (state.debounceId != null) {
      window.clearTimeout(state.debounceId);
      state.debounceId = null;
    }
    state.queryText = String(state.input.value || "");
    resetVisibleCount(state);
    renderResults(state);
  });

  state.more.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-role='more']");
    if (!button) return;
    state.visibleCount += state.runtimePolicy.batchIncrementSize;
    renderResults(state);
  });
}

function renderResults(state) {
  const projection = createCatalogueSearchResultsProjection({
    policy: state.policy,
    entries: state.entries,
    queryText: state.queryText || state.input.value,
    filterKind: state.filterKind,
    visibleCount: state.visibleCount,
    runtimePolicy: state.runtimePolicy,
    baseurl: state.baseurl,
    matchCache: state.matchCache,
    resultCollator: state.resultCollator,
    timer: () => state.instrumentation.timer(),
    text: (key, fallback, tokens) => searchText(state.policy, key, fallback, tokens)
  });
  state.queryText = projection.query;
  state.matchCache = projection.matchCache;
  state.status.dataset.state = projection.status.state || "";
  state.status.textContent = projection.status.text;
  state.results.innerHTML = projection.resultsHtml;
  state.more.innerHTML = projection.moreHtml;
  if (projection.metrics) {
    state.instrumentation.recordQuery(projection.metrics);
  }
}

function resetVisibleCount(state) {
  state.visibleCount = state.runtimePolicy.initialBatchSize;
}

function resolveQuery() {
  const params = new URLSearchParams(window.location.search);
  return String(params.get("q") || "");
}

function applyScopeText({ backLink, scopeLabel, input, scopePolicy, inputEnabled }) {
  if (backLink) {
    if (scopePolicy && scopePolicy.backLabel && (scopePolicy.backHref || scopePolicy.backRouteKey)) {
      backLink.hidden = false;
      backLink.textContent = scopePolicy.backLabel;
      backLink.setAttribute("href", scopePolicy.backHref || routePath(scopePolicy.backRouteKey, "/"));
      backLink.removeAttribute("aria-disabled");
      backLink.tabIndex = 0;
    } else {
      backLink.hidden = true;
      backLink.removeAttribute("href");
      backLink.setAttribute("aria-disabled", "true");
      backLink.tabIndex = -1;
    }
  }

  if (scopeLabel) {
    scopeLabel.hidden = false;
    scopeLabel.textContent = scopePolicy ? scopePolicy.scopeLabel : "scope unavailable";
  }

  input.disabled = !inputEnabled;
  if (scopePolicy) {
    input.setAttribute("aria-label", scopePolicy.inputAriaLabel);
    if (inputEnabled && scopePolicy.inputPlaceholder) {
      input.setAttribute("placeholder", scopePolicy.inputPlaceholder);
    } else {
      input.removeAttribute("placeholder");
    }
    return;
  }

  input.removeAttribute("placeholder");
  input.setAttribute("aria-label", "Search unavailable");
}

function applyNavScopeState(scope) {
  const navItems = Array.from(document.querySelectorAll(".site-nav .nav-item"));
  if (!navItems.length) return;

  for (const item of navItems) {
    item.classList.remove("is-active");
    if (item.tagName === "A") {
      item.removeAttribute("aria-current");
    }
  }

  let activeHref = "";
  if (scope === "catalogue") activeHref = "/series/";
  if (!activeHref) return;

  const activeItem = navItems.find((item) => {
    if (item.tagName !== "A") return false;
    return item.getAttribute("href") === activeHref;
  });
  if (!activeItem) return;

  activeItem.classList.add("is-active");
  activeItem.setAttribute("aria-current", "page");
}

function applyPerformanceText({ policy, performanceSummary }) {
  if (!performanceSummary) return;
  performanceSummary.textContent = searchText(policy, "performance_summary", "Search performance");
}

function showMissingScopeState({ root, backLink, scopeLabel, input, status, results, more, policy }) {
  applyScopeText({ backLink, scopeLabel, input, scopePolicy: null, inputEnabled: false });
  status.textContent = searchMessage(policy, "missing_scope_error", "Search is unavailable without a valid search scope.");
  status.dataset.state = "error";
  results.innerHTML = "";
  more.innerHTML = "";
  root.hidden = false;
}

function showUnsupportedScopeState({ root, status, results, more, policy }) {
  status.textContent = searchMessage(policy, "unsupported_scope_error", "Search is not yet available for this scope.");
  status.dataset.state = "error";
  results.innerHTML = "";
  more.innerHTML = "";
  root.hidden = false;
}

function routePath(key, fallback) {
  const routes = {
    series_page_base: "/series/"
  };
  return routes[key] || fallback;
}

function searchText(policy, key, fallback, tokens) {
  const source = searchMessage(policy, key, fallback);
  return applyTextTokens(source, tokens);
}

function searchPolicyUrl() {
  return withAssetVersion(resolveSiteAssetPath("/assets/data/search/policy.json"), readAssetVersion(import.meta.url));
}

function applyTextTokens(text, tokens) {
  const template = String(text || "");
  if (!tokens || typeof tokens !== "object") return template;
  return template.replace(/\{([a-z0-9_]+)\}/gi, (match, key) => {
    if (!(key in tokens)) return match;
    const value = tokens[key];
    return value == null ? "" : String(value);
  });
}

function searchMessage(policy, key, fallback) {
  return getSearchMessageFn ? getSearchMessageFn(policy, key, fallback) : fallback;
}

function estimatePayloadBytesFallback(text) {
  return String(text || "").length;
}

function firstNonEmpty(values) {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text) return text;
  }
  return "";
}

function withAssetVersion(path, assetVersion) {
  if (!path) return "";
  const url = new URL(path, import.meta.url);
  if (assetVersion) {
    url.searchParams.set("v", assetVersion);
  }
  return url.href;
}

function deriveSiteBasePath(importUrl) {
  const pathname = new URL(importUrl).pathname || "";
  const marker = "/assets/js/";
  const index = pathname.indexOf(marker);
  if (index < 0) return "";
  return pathname.slice(0, index).replace(/\/+$/, "");
}

function resolveSiteAssetPath(path) {
  if (!path) return "";
  if (/^[a-z]+:\/\//i.test(path)) return path;
  const cleanPath = `/${String(path).replace(/^\/+/, "")}`;
  return `${SITE_BASE_PATH}${cleanPath}`.replace(/\/{2,}/g, "/");
}

function readAssetVersion(importUrl = "") {
  try {
    const importVersion = new URL(importUrl).searchParams.get("v");
    if (importVersion) return importVersion;
  } catch (_error) {
    // Ignore malformed import URLs and continue to DOM-based lookup.
  }

  if (typeof document !== "undefined") {
    const meta = document.querySelector('meta[name="dlf-asset-version"]');
    const value = meta ? String(meta.getAttribute("content") || "").trim() : "";
    if (value) return value;
  }

  return "";
}
