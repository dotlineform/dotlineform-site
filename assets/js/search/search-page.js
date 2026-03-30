let getStudioTextFn = (_config, _key, fallback = "") => fallback;
let getSearchPolicyPathFn = () => "";
let loadStudioConfigFn = null;
let loadSearchIndexJsonFn = null;
let loadSearchPolicyFn = null;
let getSearchRuntimePolicyFn = null;
let getSearchScopePolicyFn = null;
let getSearchMessageFn = null;
let searchDepsPromise = null;

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
  if (!input || !status || !results || !more) return;

  let config = null;
  let policy = null;

  try {
    await loadSearchDeps();
    config = await loadStudioConfigFn();
    status.textContent = searchText(config, "loading", "loading search index…");
    policy = await loadSearchPolicyFn(getSearchPolicyPathFn(config));

    const scope = resolveScope();
    if (!scope) {
      showMissingScopeState({ root, backLink, scopeLabel, input, status, results, more, policy });
      return;
    }

    const scopePolicy = getSearchScopePolicyFn(policy, scope);
    if (!scopePolicy) {
      showMissingScopeState({ root, backLink, scopeLabel, input, status, results, more, policy });
      return;
    }

    const runtimePolicy = getSearchRuntimePolicyFn(policy);
    applyScopeText({ backLink, scopeLabel, input, config, scopePolicy, inputEnabled: scopePolicy.enabled });

    if (!scopePolicy.enabled) {
      showUnsupportedScopeState({ root, status, results, more, policy });
      return;
    }

    const payload = await loadSearchIndexJsonFn(config, scope);
    const entries = normalizeEntries(payload && Array.isArray(payload.entries) ? payload.entries : []);
    const state = {
      config,
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
      queryText: "",
      debounceId: null,
      visibleCount: runtimePolicy.initialBatchSize
    };
    wireEvents(state);
    renderResults(state);
    root.hidden = false;
    input.focus();
  } catch (error) {
    root.hidden = false;
    status.textContent = searchText(config, "load_failed_error", "Failed to load search data.");
    status.dataset.state = "error";
  }
}

async function loadSearchDeps() {
  if (!searchDepsPromise) {
    const assetVersion = readAssetVersion(import.meta.url);
    searchDepsPromise = Promise.all([
      import(withAssetVersion("../../studio/js/studio-config.js", assetVersion)),
      import(withAssetVersion("../../studio/js/studio-data.js", assetVersion)),
      import(withAssetVersion("./search-policy.js", assetVersion))
    ]).then(([configModule, dataModule, policyModule]) => {
      getStudioTextFn = configModule.getStudioText;
      getSearchPolicyPathFn = configModule.getSearchPolicyPath;
      loadStudioConfigFn = configModule.loadStudioConfig;
      loadSearchIndexJsonFn = dataModule.loadSearchIndexJson;
      loadSearchPolicyFn = policyModule.loadSearchPolicy;
      getSearchRuntimePolicyFn = policyModule.getSearchRuntimePolicy;
      getSearchScopePolicyFn = policyModule.getSearchScopePolicy;
      getSearchMessageFn = policyModule.getSearchMessage;
    });
  }
  return searchDepsPromise;
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

function normalizeEntries(entries) {
  return entries
    .filter((entry) => entry && typeof entry === "object")
    .map((entry) => {
      const kind = normalize(String(entry.kind || ""));
      const id = String(entry.id || "").trim();
      const title = String(entry.title || "").trim();
      const href = String(entry.href || "").trim();
      const displayMeta = String(entry.display_meta || "").trim();
      const seriesTitles = Array.isArray(entry.series_titles) ? entry.series_titles.map((item) => String(item || "").trim()).filter(Boolean) : [];
      const searchTerms = Array.isArray(entry.search_terms) ? entry.search_terms.map((item) => normalize(String(item || ""))).filter(Boolean) : [];
      return {
        kind,
        id,
        title,
        href,
        displayMeta,
        year: Number.isFinite(Number(entry.year)) ? Number(entry.year) : null,
        date: String(entry.date || "").trim(),
        seriesTitles,
        mediumType: String(entry.medium_type || "").trim(),
        storage: String(entry.storage || "").trim(),
        seriesType: String(entry.series_type || "").trim(),
        tagLabels: Array.isArray(entry.tag_labels) ? entry.tag_labels.map((item) => String(item || "").trim()).filter(Boolean) : [],
        searchTerms,
        searchText: normalize(String(entry.search_text || "")),
        titleNorm: normalize(title),
        idNorm: normalize(id),
        titleTokens: normalize(title).split(" ").filter(Boolean),
        seriesTitleNorms: seriesTitles.map(normalize).filter(Boolean),
        mediumTypeNorm: normalize(String(entry.medium_type || "")),
        storageNorm: normalize(String(entry.storage || "")),
        seriesTypeNorm: normalize(String(entry.series_type || ""))
      };
    })
    .filter((entry) => entry.kind && entry.id && entry.title && entry.href);
}

function renderResults(state) {
  const query = normalize(String(state.queryText || state.input.value || ""));
  state.queryText = query;

  if (!query || query.length < state.runtimePolicy.minQueryLength) {
    state.status.dataset.state = "";
    state.status.textContent = searchText(state.config, "prompt", "Enter a search query.");
    state.results.innerHTML = "";
    state.more.innerHTML = "";
    return;
  }

  const matches = [];
  for (const entry of state.entries) {
    if (state.filterKind !== "all" && entry.kind !== state.filterKind) continue;
    const score = scoreEntry(entry, query);
    if (score == null) continue;
    matches.push({ entry, score });
  }

  matches.sort((a, b) => {
    if (a.score !== b.score) return b.score - a.score;
    const titleCmp = a.entry.title.localeCompare(b.entry.title, undefined, { sensitivity: "base", numeric: true });
    if (titleCmp !== 0) return titleCmp;
    return a.entry.id.localeCompare(b.entry.id, undefined, { sensitivity: "base", numeric: true });
  });

  const visible = matches.slice(0, state.visibleCount);
  if (!visible.length) {
    state.status.dataset.state = "";
    state.status.textContent = searchText(state.config, "no_results", "No results.");
    state.results.innerHTML = "";
    state.more.innerHTML = "";
    return;
  }

  state.status.dataset.state = "";
  state.status.textContent = matches.length === 1
    ? searchText(state.config, "results_count_one", "1 result")
    : matches.length > visible.length
      ? searchText(state.config, "results_count_visible", "Showing {visible} of {count} results", {
        visible: String(visible.length),
        count: String(matches.length)
      })
      : searchText(state.config, "results_count", "{count} results", { count: String(matches.length) });
  state.results.innerHTML = visible.map(({ entry }) => renderEntry(state, entry)).join("");
  state.more.innerHTML = matches.length > visible.length
    ? `<button type="button" class="studioSearch__moreBtn" data-role="more">${escapeHtml(searchText(state.config, "load_more", "more"))}</button>`
    : "";
}

function scoreEntry(entry, query) {
  const queryTokens = query.split(" ").filter(Boolean);
  if (!queryTokens.length) return null;
  if (!matchesAllTokens(entry, queryTokens)) return null;

  if (entry.idNorm === query) return 900;
  if (entry.titleNorm === query) return 860;
  if (entry.searchTerms.includes(query)) return 780;
  if (entry.titleNorm.startsWith(query)) return 720;
  if (entry.idNorm.startsWith(query)) return 690;
  if (queryTokens.every((token) => entry.titleTokens.some((candidate) => candidate === token || candidate.startsWith(token)))) return 620;
  if (entry.seriesTitleNorms.some((value) => value.includes(query))) return 480;
  if (entry.mediumTypeNorm && entry.mediumTypeNorm.includes(query)) return 460;
  if (entry.storageNorm && entry.storageNorm.includes(query)) return 440;
  if (entry.seriesTypeNorm && entry.seriesTypeNorm.includes(query)) return 420;
  if (entry.searchText.includes(query)) return 320;
  return null;
}

function matchesAllTokens(entry, queryTokens) {
  return queryTokens.every((token) => {
    if (entry.searchTerms.some((candidate) => candidate === token || candidate.startsWith(token))) {
      return true;
    }
    return entry.searchText.includes(token);
  });
}

function renderEntry(state, entry) {
  const metaParts = [];
  if (entry.displayMeta) metaParts.push(entry.displayMeta);
  if (entry.kind === "work" && entry.mediumType) metaParts.push(entry.mediumType);
  if (entry.kind === "work" && entry.seriesTitles.length) {
    metaParts.push(entry.seriesTitles.join(searchText(state.config, "result_meta_separator", " • ")));
  }
  if (entry.kind === "series" && entry.seriesType) metaParts.push(entry.seriesType);
  const metaText = metaParts.join(searchText(state.config, "result_meta_separator", " • "));
  return `
    <li class="studioSearch__item">
      <div class="studioSearch__itemHead">
        <span class="studioSearch__kind">${escapeHtml(kindLabel(state.config, entry.kind))}</span>
        <a class="studioSearch__title" href="${escapeHtml(withBaseUrl(state.baseurl, entry.href))}">${escapeHtml(entry.title)}</a>
      </div>
      <p class="studioSearch__id">${escapeHtml(entry.id)}</p>
      ${metaText ? `<p class="studioSearch__meta">${escapeHtml(metaText)}</p>` : ""}
    </li>
  `;
}

function resetVisibleCount(state) {
  state.visibleCount = state.runtimePolicy.initialBatchSize;
}

function withBaseUrl(baseurl, href) {
  const cleanBase = String(baseurl || "").replace(/\/+$/, "");
  const cleanHref = String(href || "");
  if (!cleanBase || /^https?:\/\//.test(cleanHref)) return cleanHref;
  if (!cleanHref.startsWith("/")) return cleanHref;
  return `${cleanBase}${cleanHref}`;
}

function kindLabel(config, kind) {
  if (kind === "work") return searchText(config, "result_kind_work", "work");
  if (kind === "series") return searchText(config, "result_kind_series", "series");
  if (kind === "moment") return searchText(config, "result_kind_moment", "moment");
  return kind;
}

function resolveScope() {
  const params = new URLSearchParams(window.location.search);
  return normalize(String(params.get("scope") || ""));
}

function applyScopeText({ backLink, scopeLabel, input, config, scopePolicy, inputEnabled }) {
  if (backLink) {
    if (scopePolicy && scopePolicy.backLabel && scopePolicy.backRouteKey) {
      backLink.hidden = false;
      backLink.textContent = scopePolicy.backLabel;
      backLink.setAttribute("href", routePath(config, scopePolicy.backRouteKey, "/"));
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

function showMissingScopeState({ root, backLink, scopeLabel, input, status, results, more, policy }) {
  applyScopeText({ backLink, scopeLabel, input, config: null, scopePolicy: null, inputEnabled: false });
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

function routePath(config, key, fallback) {
  const routes = config && config.paths && config.paths.routes && typeof config.paths.routes === "object"
    ? config.paths.routes
    : null;
  const value = routes && typeof routes[key] === "string" ? routes[key].trim() : "";
  return value || fallback;
}

function searchText(config, key, fallback, tokens) {
  return getStudioTextFn(config, `search.${key}`, fallback, tokens);
}

function searchMessage(policy, key, fallback) {
  return getSearchMessageFn ? getSearchMessageFn(policy, key, fallback) : fallback;
}

function withAssetVersion(path, assetVersion) {
  const url = new URL(path, import.meta.url);
  if (assetVersion) {
    url.searchParams.set("v", assetVersion);
  }
  return url.href;
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

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
