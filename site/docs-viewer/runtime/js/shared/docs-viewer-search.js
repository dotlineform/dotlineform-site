export function normalizeSearchText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function normalizeSearchEntries(entries) {
  return entries
    .filter(function (entry) {
      return entry && typeof entry === "object";
    })
    .map(function (entry) {
      var kind = normalizeSearchText(String(entry.kind || ""));
      var id = String(entry.id || "").trim();
      var title = String(entry.title || "").trim();
      var href = String(entry.href || "").trim();
      var displayMeta = String(entry.display_meta || "").trim();
      var parentTitle = String(entry.parent_title || "").trim();
      var searchTerms = Array.isArray(entry.search_terms)
        ? entry.search_terms.map(function (item) { return normalizeSearchText(String(item || "")); }).filter(Boolean)
        : [];
      return {
        kind: kind,
        id: id,
        title: title,
        href: href,
        displayMeta: displayMeta,
        parentTitle: parentTitle,
        lastUpdated: String(entry.last_updated || "").trim(),
        searchTerms: searchTerms,
        searchText: normalizeSearchText(String(entry.search_text || "")),
        titleNorm: normalizeSearchText(title),
        idNorm: normalizeSearchText(id),
        titleTokens: normalizeSearchText(title).split(" ").filter(Boolean),
        parentTitleNorm: normalizeSearchText(parentTitle)
      };
    })
    .filter(function (entry) {
      return entry.kind === "doc" && entry.id && entry.title;
    });
}

export function normalizeRecentEntries(entries) {
  return entries
    .filter(function (entry) {
      return entry && typeof entry === "object";
    })
    .map(function (entry) {
      return {
        doc_id: String(entry.doc_id || "").trim(),
        title: String(entry.title || "").trim(),
        content_url: String(entry.content_url || "").trim(),
        timestamp: String(entry.timestamp || "").trim(),
        parent_id: String(entry.parent_id || "").trim(),
        parent_title: String(entry.parent_title || "").trim()
      };
    })
    .filter(function (entry) {
      return entry.doc_id && entry.title && entry.timestamp;
    });
}

export function scoreSearchEntry(entry, query, queryTokens) {
  if (entry.idNorm === query) return 900;
  if (entry.titleNorm === query) return 860;
  if (entry.searchTerms.indexOf(query) >= 0) return 780;
  if (entry.titleNorm.indexOf(query) === 0) return 720;
  if (entry.idNorm.indexOf(query) === 0) return 690;
  if (queryTokens.every(function (token) {
    return entry.titleTokens.some(function (candidate) {
      return candidate === token || candidate.indexOf(token) === 0;
    });
  })) return 620;
  if (entry.parentTitleNorm && entry.parentTitleNorm.indexOf(query) >= 0) return 460;
  if (entry.searchText.indexOf(query) >= 0) return 320;
  return null;
}

export function matchesAllTokens(entry, queryTokens) {
  return queryTokens.every(function (token) {
    if (entry.searchTerms.some(function (candidate) { return candidate === token || candidate.indexOf(token) === 0; })) {
      return true;
    }
    return entry.searchText.indexOf(token) >= 0;
  });
}

export function collectSearchMatches(entries, query) {
  var queryTokens = query.split(" ").filter(Boolean);
  if (!queryTokens.length) return [];

  var matches = [];
  entries.forEach(function (entry) {
    if (!matchesAllTokens(entry, queryTokens)) return;
    var score = scoreSearchEntry(entry, query, queryTokens);
    if (score == null) return;
    matches.push({ entry: entry, score: score });
  });

  matches.sort(function (left, right) {
    if (left.score !== right.score) return right.score - left.score;
    var titleCmp = left.entry.title.localeCompare(right.entry.title, undefined, { sensitivity: "base", numeric: true });
    if (titleCmp !== 0) return titleCmp;
    return left.entry.id.localeCompare(right.entry.id, undefined, { sensitivity: "base", numeric: true });
  });

  return matches;
}

export function compareRecentDocs(left, right) {
  var leftDate = String(left.timestamp || "");
  var rightDate = String(right.timestamp || "");
  if (leftDate !== rightDate) return rightDate.localeCompare(leftDate);
  var titleCmp = String(left.title || "").localeCompare(String(right.title || ""), undefined, { sensitivity: "base", numeric: true });
  if (titleCmp !== 0) return titleCmp;
  return String(left.doc_id || "").localeCompare(String(right.doc_id || ""), undefined, { sensitivity: "base", numeric: true });
}

export function collectRecentDocs(docs, recentLimit) {
  return docs
    .filter(function (doc) {
      return doc && doc.doc_id;
    })
    .slice()
    .sort(compareRecentDocs)
    .slice(0, recentLimit);
}
