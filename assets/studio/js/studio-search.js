import {
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadSiteSearchIndexJson
} from "./studio-data.js";

const RESULTS_BATCH_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 140;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStudioSearchPage);
} else {
  initStudioSearchPage();
}

async function initStudioSearchPage() {
  const root = document.getElementById("studioSearchRoot");
  if (!root) return;

  const scopeLabel = document.getElementById("studioSearchScope");
  const input = document.getElementById("studioSearchInput");
  const status = document.getElementById("studioSearchStatus");
  const results = document.getElementById("studioSearchResults");
  const more = document.getElementById("studioSearchMore");
  if (!input || !status || !results || !more) return;

  let config = null;
  try {
    config = await loadStudioConfig();
    status.textContent = searchText(config, "loading", "loading search index…");

    const scope = resolveScope();
    if (!scope) {
      showMissingScopeState({ root, scopeLabel, input, status, results, more, config });
      return;
    }

    applyScopeText({ scopeLabel, input, config, scope });

    const payload = await loadSiteSearchIndexJson(config);
    const entries = normalizeEntries(payload && Array.isArray(payload.entries) ? payload.entries : []);
    const state = {
      config,
      scope,
      baseurl: String(root.dataset.baseurl || ""),
      input,
      status,
      results,
      more,
      entries,
      filterKind: "all",
      queryText: "",
      debounceId: null,
      visibleCount: RESULTS_BATCH_SIZE
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

function wireEvents(state) {
  state.input.addEventListener("input", () => {
    if (state.debounceId != null) {
      window.clearTimeout(state.debounceId);
    }
    state.debounceId = window.setTimeout(() => {
      state.debounceId = null;
      state.queryText = String(state.input.value || "");
      resetVisibleCount(state);
      renderResults(state);
    }, SEARCH_DEBOUNCE_MS);
  });

  state.input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
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
    state.visibleCount += RESULTS_BATCH_SIZE;
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

  if (!query) {
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
  state.visibleCount = RESULTS_BATCH_SIZE;
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
  const scope = String(params.get("scope") || "").trim().toLowerCase();
  return scope === "catalogue" ? scope : "";
}

function applyScopeText({ scopeLabel, input, config, scope }) {
  if (scopeLabel) {
    scopeLabel.textContent = scope === "catalogue"
      ? searchText(config, "scope_catalogue_label", "catalogue")
      : searchText(config, "scope_unavailable_label", "scope unavailable");
  }

  if (scope === "catalogue") {
    input.disabled = false;
    input.setAttribute("aria-label", searchText(config, "search_input_aria_label_catalogue", "Search works, series, and moments"));
    input.setAttribute("placeholder", searchText(config, "search_placeholder_catalogue", "search works, series, moments"));
    return;
  }

  input.disabled = true;
  input.removeAttribute("placeholder");
  input.setAttribute("aria-label", searchText(config, "search_input_aria_label_unavailable", "Search unavailable"));
}

function showMissingScopeState({ root, scopeLabel, input, status, results, more, config }) {
  applyScopeText({ scopeLabel, input, config, scope: "" });
  status.textContent = searchText(config, "missing_scope_error", "Search is unavailable without a valid search scope.");
  status.dataset.state = "error";
  results.innerHTML = "";
  more.innerHTML = "";
  root.hidden = false;
}

function searchText(config, key, fallback, tokens) {
  return getStudioText(config, `search.${key}`, fallback, tokens);
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
