export function normalizeCatalogueSearchEntries(entries, scopePolicy) {
  const scope = scopePolicy ? scopePolicy.scope : "";
  const scopeLabel = scopePolicy ? scopePolicy.scopeLabel : "";
  return (Array.isArray(entries) ? entries : [])
    .filter((entry) => entry && typeof entry === "object")
    .map((entry) => {
      const kind = normalizeCatalogueSearchText(String(entry.kind || ""));
      const id = String(entry.id || "").trim();
      const title = String(entry.title || "").trim();
      const href = String(entry.href || "").trim();
      const displayMeta = String(entry.display_meta || "").trim();
      const parentTitle = String(entry.parent_title || "").trim();
      const seriesIds = Array.isArray(entry.series_ids) ? entry.series_ids.map((item) => String(item || "").trim()).filter(Boolean) : [];
      const seriesTitles = Array.isArray(entry.series_titles) ? entry.series_titles.map((item) => String(item || "").trim()).filter(Boolean) : [];
      const searchTerms = Array.isArray(entry.search_terms) ? entry.search_terms.map((item) => normalizeCatalogueSearchText(String(item || ""))).filter(Boolean) : [];
      return {
        kind,
        id,
        title,
        href,
        displayMeta,
        parentTitle,
        year: Number.isFinite(Number(entry.year)) ? Number(entry.year) : null,
        date: String(entry.date || "").trim(),
        seriesIds,
        seriesTitles,
        mediumType: String(entry.medium_type || "").trim(),
        seriesType: String(entry.series_type || "").trim(),
        tagLabels: Array.isArray(entry.tag_labels) ? entry.tag_labels.map((item) => String(item || "").trim()).filter(Boolean) : [],
        scope,
        scopeLabel,
        searchTerms,
        searchText: normalizeCatalogueSearchText(String(entry.search_text || "")),
        titleNorm: normalizeCatalogueSearchText(title),
        idNorm: normalizeCatalogueSearchText(id),
        titleTokens: normalizeCatalogueSearchText(title).split(" ").filter(Boolean),
        parentTitleNorm: normalizeCatalogueSearchText(parentTitle),
        seriesTitleNorms: seriesTitles.map(normalizeCatalogueSearchText).filter(Boolean),
        mediumTypeNorm: normalizeCatalogueSearchText(String(entry.medium_type || "")),
        seriesTypeNorm: normalizeCatalogueSearchText(String(entry.series_type || ""))
      };
    })
    .filter((entry) => entry.kind && entry.id && entry.title && (entry.href || isCatalogueRouteKind(entry.kind)));
}

export function createCatalogueSearchResultsProjection(options = {}) {
  const timer = typeof options.timer === "function" ? options.timer : disabledTimer;
  const totalTimer = timer();
  const query = normalizeCatalogueSearchText(String(options.queryText || ""));
  const queryTokens = query.split(" ").filter(Boolean);
  const runtimePolicy = options.runtimePolicy || {};
  const minQueryLength = Number(runtimePolicy.minQueryLength || 1);
  const entries = Array.isArray(options.entries) ? options.entries : [];
  const text = typeof options.text === "function" ? options.text : (_key, fallback) => fallback;

  if (!query || query.length < minQueryLength || !queryTokens.length) {
    return {
      query,
      status: { state: "", text: text("prompt", "Enter a search query.") },
      resultsHtml: "",
      moreHtml: "",
      matchCache: options.matchCache || null,
      metrics: null
    };
  }

  const matchResult = getSortedMatches({
    entries,
    query,
    queryTokens,
    filterKind: options.filterKind || "all",
    matchCache: options.matchCache || null,
    resultCollator: options.resultCollator || null,
    timer
  });
  const visibleCount = Math.max(0, Number(options.visibleCount || 0));
  const visible = matchResult.matches.slice(0, visibleCount);
  const renderTimer = timer();
  let status;
  let resultsHtml = "";
  let moreHtml = "";

  if (!visible.length) {
    status = { state: "", text: text("no_results", "No results.") };
  } else {
    status = {
      state: "",
      text: resultCountText(text, matchResult.matches.length, visible.length)
    };
    resultsHtml = visible.map(({ entry }) => renderCatalogueSearchEntry(entry, {
      policy: options.policy,
      text,
      baseurl: options.baseurl || ""
    })).join("");
    moreHtml = matchResult.matches.length > visible.length
      ? `<button type="button" class="studioSearch__moreBtn" data-role="more">${escapeHtml(text("load_more", "more"))}</button>`
      : "";
  }

  const renderMs = renderTimer.end();
  return {
    query,
    status,
    resultsHtml,
    moreHtml,
    matchCache: matchResult.matchCache,
    metrics: {
      queryLength: query.length,
      entryCount: entries.length,
      matchCount: matchResult.matches.length,
      visibleCount: visible.length,
      evaluateMs: matchResult.evaluateMs,
      sortMs: matchResult.sortMs,
      renderMs,
      totalMs: totalTimer.end()
    }
  };
}

export function createCatalogueSearchResultCollator() {
  try {
    if (typeof Intl !== "undefined" && typeof Intl.Collator === "function") {
      return new Intl.Collator(undefined, { sensitivity: "base", numeric: true });
    }
  } catch (_error) {
    // Fall back to localeCompare if Intl.Collator is unavailable.
  }
  return null;
}

export function normalizeCatalogueSearchText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function getSortedMatches(options) {
  const cache = options.matchCache;
  if (cache && cache.query === options.query && cache.filterKind === options.filterKind) {
    return {
      matches: cache.matches,
      matchCache: cache,
      evaluateMs: 0,
      sortMs: 0
    };
  }

  const matches = [];
  const evaluateTimer = options.timer();
  for (const entry of options.entries) {
    if (options.filterKind !== "all" && entry.kind !== options.filterKind) continue;
    const score = scoreEntry(entry, options.query, options.queryTokens);
    if (score == null) continue;
    matches.push({ entry, score });
  }
  const evaluateMs = evaluateTimer.end();

  const sortTimer = options.timer();
  matches.sort((a, b) => compareSearchMatches(a, b, options.resultCollator));
  const sortMs = sortTimer.end();

  const matchCache = {
    query: options.query,
    filterKind: options.filterKind,
    matches
  };
  return { matches, matchCache, evaluateMs, sortMs };
}

function scoreEntry(entry, query, queryTokens) {
  if (!matchesAllTokens(entry, queryTokens)) return null;

  if (entry.idNorm === query) return 900;
  if (entry.titleNorm === query) return 860;
  if (entry.searchTerms.includes(query)) return 780;
  if (entry.titleNorm.startsWith(query)) return 720;
  if (entry.idNorm.startsWith(query)) return 690;
  if (queryTokens.every((token) => entry.titleTokens.some((candidate) => candidate === token || candidate.startsWith(token)))) return 620;
  if (entry.seriesTitleNorms.some((value) => value.includes(query))) return 480;
  if (entry.mediumTypeNorm && entry.mediumTypeNorm.includes(query)) return 460;
  if (entry.seriesTypeNorm && entry.seriesTypeNorm.includes(query)) return 420;
  if (entry.searchText.includes(query)) return 320;
  return null;
}

function compareSearchMatches(a, b, collator) {
  if (a.score !== b.score) return b.score - a.score;
  const titleCmp = compareSearchText(a.entry.title, b.entry.title, collator);
  if (titleCmp !== 0) return titleCmp;
  return compareSearchText(a.entry.id, b.entry.id, collator);
}

function compareSearchText(a, b, collator) {
  if (collator && typeof collator.compare === "function") {
    return collator.compare(String(a || ""), String(b || ""));
  }
  return String(a || "").localeCompare(String(b || ""));
}

function matchesAllTokens(entry, queryTokens) {
  return queryTokens.every((token) => {
    if (entry.searchTerms.some((candidate) => candidate === token || candidate.startsWith(token))) {
      return true;
    }
    return entry.searchText.includes(token);
  });
}

function resultCountText(text, matchCount, visibleCount) {
  if (matchCount === 1) return text("results_count_one", "1 result");
  if (matchCount > visibleCount) {
    return text("results_count_visible", "Showing {visible} of {count} results", {
      visible: String(visibleCount),
      count: String(matchCount)
    });
  }
  return text("results_count", "{count} results", { count: String(matchCount) });
}

function renderCatalogueSearchEntry(entry, options) {
  const metaParts = [];
  const separator = options.text("result_meta_separator", " • ");
  if (entry.displayMeta) metaParts.push(escapeHtml(entry.displayMeta));
  if (entry.kind === "work" && entry.mediumType) metaParts.push(escapeHtml(entry.mediumType));
  if (entry.kind === "work" && entry.seriesTitles.length) {
    metaParts.push(renderSeriesLinks(entry, options).join(escapeHtml(separator)));
  }
  if (entry.kind === "series" && entry.seriesType) metaParts.push(escapeHtml(entry.seriesType));
  const metaHtml = metaParts.join(escapeHtml(separator));
  const linkAttrs = catalogueEntryTargetAttrs(entry);
  const href = catalogueEntryHref(entry, options.baseurl);
  return `
    <li class="studioSearch__item">
      <div class="studioSearch__itemHead">
        <span class="studioSearch__kind">${escapeHtml(kindLabel(options.text, entry.kind))}</span>
        <a class="studioSearch__title" href="${escapeHtml(href)}"${linkAttrs}>${escapeHtml(entry.title)}</a>
      </div>
      <p class="studioSearch__id">${escapeHtml(entry.id)}</p>
      ${metaHtml ? `<p class="studioSearch__meta">${metaHtml}</p>` : ""}
    </li>
  `;
}

function renderSeriesLinks(entry, options) {
  return entry.seriesTitles.map((title, index) => {
    const seriesId = String(entry.seriesIds[index] || "").trim();
    if (!seriesId) return escapeHtml(title);
    const href = withBaseUrl(options.baseurl, `/series/?series=${encodeURIComponent(seriesId)}`);
    return `<a class="studioSearch__metaLink" href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(title)}</a>`;
  });
}

function catalogueEntryHref(entry, baseurl) {
  if (entry.kind === "series") return withBaseUrl(baseurl, `/series/?series=${encodeURIComponent(entry.id)}`);
  if (entry.kind === "work") return withBaseUrl(baseurl, `/works/?work=${encodeURIComponent(entry.id)}`);
  if (entry.kind === "moment") return withBaseUrl(baseurl, `/moments/?moment=${encodeURIComponent(entry.id)}`);
  return withBaseUrl(baseurl, entry.href);
}

function isCatalogueRouteKind(kind) {
  return kind === "series" || kind === "work" || kind === "moment";
}

function catalogueEntryTargetAttrs(entry) {
  return entry.kind === "work" || entry.kind === "series" || entry.kind === "moment"
    ? ' target="_blank" rel="noopener"'
    : "";
}

function withBaseUrl(baseurl, href) {
  const cleanBase = String(baseurl || "").replace(/\/+$/, "");
  const cleanHref = String(href || "");
  if (!cleanBase || /^https?:\/\//.test(cleanHref)) return cleanHref;
  if (!cleanHref.startsWith("/")) return cleanHref;
  return `${cleanBase}${cleanHref}`;
}

function kindLabel(text, kind) {
  if (kind === "work") return text("result_kind_work", "work");
  if (kind === "series") return text("result_kind_series", "series");
  if (kind === "moment") return text("result_kind_moment", "moment");
  return kind;
}

function disabledTimer() {
  return { end: () => 0 };
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
