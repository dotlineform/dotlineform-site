export function normalizeSearchText(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

const SEARCH_INDEX_V2_SCHEMA = "docs_viewer_search_index_v2";
const SEARCH_V2_STOP_WORDS = new Set([
  "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
  "in", "is", "it", "of", "on", "or", "that", "the", "to", "with"
]);
const SEARCH_V2_FILE_EXTENSIONS = new Set([
  "css", "gif", "htm", "html", "jpeg", "jpg", "js", "json", "md",
  "mjs", "pdf", "png", "py", "svg", "ts", "txt", "webp", "yaml", "yml"
]);
const SEARCH_V2_EXACT_FIELDS = new Set(["identity", "last_updated"]);
const SEARCH_V2_CONTENT_HASH = /^[0-9a-f]{64}$/;

export function tokenizeSearchValue(value) {
  var terms = [];
  var seen = new Set();
  var text = String(value || "")
    .normalize("NFKC")
    .replace(/(?:https?:\/\/|www\.)\S+|(?:[\\/][^\s]+)+|<[^>]+>/giu, " ");
  (text.match(/[\p{L}\p{N}]+(?:[._-][\p{L}\p{N}]+)*/gu) || []).forEach(function (token) {
    var normalizedToken = normalizeSearchText(token);
    if (/^d-\d{8}-\d{6}-[0-9a-f]{6}$/.test(normalizedToken)
      || SEARCH_V2_CONTENT_HASH.test(normalizedToken)) return;
    var derived = [normalizedToken];
    var segments = token.split(/[._-]+/);
    var hasFileExtension = token.includes(".")
      && SEARCH_V2_FILE_EXTENSIONS.has(normalizeSearchText(segments[segments.length - 1]));
    segments.forEach(function (segment, index) {
      if (hasFileExtension && index === segments.length - 1) return;
      derived.push(...segment
        .replace(/(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/g, " ")
        .split(/\s+/));
    });
    derived.forEach(function (candidate) {
      var term = normalizeSearchText(candidate).replace(/^[._-]+|[._-]+$/g, "");
      var useful = term.length >= 2
        && !SEARCH_V2_STOP_WORDS.has(term)
        && /[\p{L}]/u.test(term)
        && !/^d-\d{8}-\d{6}-[0-9a-f]{6}$/.test(term)
        && !SEARCH_V2_CONTENT_HASH.test(term);
      if (!useful || seen.has(term)) return;
      seen.add(term);
      terms.push(term);
    });
  });
  return terms;
}

function searchConstraintMatchesV2(index, queryTerm, fields) {
  var allowedFields = new Set(fields);
  var matches = new Map();
  Object.keys(index.terms).forEach(function (indexedTerm) {
    if (indexedTerm !== queryTerm && !(queryTerm.length >= 3 && indexedTerm.indexOf(queryTerm) === 0)) return;
    Object.keys(index.terms[indexedTerm]).forEach(function (field) {
      if (!allowedFields.has(field)) return;
      index.terms[indexedTerm][field].forEach(function (position) {
        if (!matches.has(position)) matches.set(position, new Set());
        matches.get(position).add(field);
      });
    });
  });
  return matches;
}

function searchScoreV2(index, position, query, matchedFields) {
  var document = index.docs[position];
  var id = normalizeSearchText(document.id);
  var title = normalizeSearchText(document.title);
  if (id === query) return 1000;
  if (title === query) return 900;
  if (matchedFields.has("title")) return 800;
  if (matchedFields.has("heading")) return 700;
  if (matchedFields.has("parent_title")) return 500;
  if (matchedFields.has("body") || matchedFields.has("code")) return 400;
  if (matchedFields.has("last_updated")) return 300;
  return 100;
}

export function collectSearchMatches(index, rawQuery) {
  if (!index || !index.header || index.header.schema !== SEARCH_INDEX_V2_SCHEMA) {
    throw new Error("Docs Viewer v2 search index has an unsupported schema.");
  }
  var query = normalizeSearchText(rawQuery);
  if (!query) return [];
  var fields = Array.isArray(index.fields) ? index.fields : [];
  var queryTerms = tokenizeSearchValue(rawQuery);
  var constraints = queryTerms.map(function (term) {
    return searchConstraintMatchesV2(index, term, fields.filter(function (field) {
      return !SEARCH_V2_EXACT_FIELDS.has(field);
    }));
  });
  if (!queryTerms.length) {
    constraints = [searchConstraintMatchesV2(index, query, fields.filter(function (field) {
      return SEARCH_V2_EXACT_FIELDS.has(field);
    }))];
  }
  if (!constraints.length || constraints.some(function (matches) { return !matches.size; })) return [];

  var positions = Array.from(constraints[0].keys()).filter(function (position) {
    return constraints.slice(1).every(function (matches) { return matches.has(position); });
  });
  return positions.map(function (position) {
    var matchedFields = new Set();
    constraints.forEach(function (matches) {
      (matches.get(position) || []).forEach(function (field) { matchedFields.add(field); });
    });
    return {
      entry: index.docs[position],
      score: searchScoreV2(index, position, query, matchedFields)
    };
  }).sort(function (left, right) {
    if (left.score !== right.score) return right.score - left.score;
    var titleCmp = left.entry.title.localeCompare(right.entry.title, undefined, { sensitivity: "base", numeric: true });
    if (titleCmp !== 0) return titleCmp;
    return left.entry.id.localeCompare(right.entry.id, undefined, { sensitivity: "base", numeric: true });
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
