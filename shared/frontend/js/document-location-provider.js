const DOCUMENT_LOCATION_SCHEMA_VERSION = "docs_document_locations_v1";
const IMMUTABLE_DOC_ID = "d-\\d{8}-\\d{6}-[a-f0-9]{6}";

export const SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS = Object.freeze([
  "analysis",
  "library"
]);

const SCOPE_ROUTE_PATTERNS = Object.freeze({
  analysis: new RegExp(`^/analysis/\\?doc=${IMMUTABLE_DOC_ID}(?:&subdoc=${IMMUTABLE_DOC_ID})?$`),
  library: new RegExp(`^/library/\\?doc=${IMMUTABLE_DOC_ID}(?:&subdoc=${IMMUTABLE_DOC_ID})?$`)
});
const DOCS_SCOPE_ROUTE_PATTERN = new RegExp(
  `^/docs/\\?scope=(analysis|studio)&doc=${IMMUTABLE_DOC_ID}(?:&subdoc=${IMMUTABLE_DOC_ID})?$`
);

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function exactRecordKeys(record) {
  return Object.keys(record).sort().join(",");
}

function projectionUrl(scopeId) {
  return `/assets/data/search/${scopeId}/document-locations.json`;
}

/**
 * Validate the explicit consumer allowlist used for one provider operation.
 * There is deliberately no implicit all-supported-scopes mode.
 */
export function normalizeDocumentLocationScopeIds(scopeIds) {
  if (!Array.isArray(scopeIds) || !scopeIds.length) {
    throw new Error("document locations require a non-empty scopeIds allowlist");
  }
  const normalized = [];
  const seen = new Set();
  scopeIds.forEach((value) => {
    const scopeId = normalizeText(value).toLowerCase();
    if (!SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS.includes(scopeId)) {
      throw new Error(`unsupported document-location scope: ${scopeId || "(empty)"}`);
    }
    if (!seen.has(scopeId)) {
      seen.add(scopeId);
      normalized.push(scopeId);
    }
  });
  if (!normalized.length) {
    throw new Error("document locations require a non-empty scopeIds allowlist");
  }
  return normalized;
}

function normalizeProjectionRecord(rawRecord, scopeId, index) {
  const field = `document locations ${scopeId}.records[${index}]`;
  if (!rawRecord || typeof rawRecord !== "object" || Array.isArray(rawRecord)) {
    throw new Error(`${field} must be an object`);
  }
  if (exactRecordKeys(rawRecord) !== "document_title,report_title,scope_id,url") {
    throw new Error(`${field} has unsupported fields`);
  }
  const record = {
    url: normalizeText(rawRecord.url),
    scope_id: normalizeText(rawRecord.scope_id).toLowerCase(),
    document_title: normalizeText(rawRecord.document_title),
    report_title: normalizeText(rawRecord.report_title),
    available: true
  };
  if (record.scope_id !== scopeId) {
    throw new Error(`${field}.scope_id does not match ${scopeId}`);
  }
  if (!record.document_title) {
    throw new Error(`${field}.document_title must not be empty`);
  }
  if (!SCOPE_ROUTE_PATTERNS[scopeId].test(record.url)) {
    throw new Error(`${field}.url is not canonical for ${scopeId}`);
  }
  if (record.url.includes("&subdoc=") !== Boolean(record.report_title)) {
    throw new Error(`${field}.report_title must identify sub-scope placements only`);
  }
  return Object.freeze(record);
}

export function normalizeDocumentLocationProjection(payload, expectedScopeId) {
  const scopeId = normalizeText(expectedScopeId).toLowerCase();
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error(`document locations ${scopeId} must be an object`);
  }
  if (payload.schema_version !== DOCUMENT_LOCATION_SCHEMA_VERSION) {
    throw new Error(`document locations ${scopeId} has an unsupported schema`);
  }
  if (normalizeText(payload.scope_id).toLowerCase() !== scopeId) {
    throw new Error(`document locations ${scopeId} has a mismatched scope_id`);
  }
  if (!Array.isArray(payload.records)) {
    throw new Error(`document locations ${scopeId}.records must be an array`);
  }
  const records = payload.records.map((record, index) => (
    normalizeProjectionRecord(record, scopeId, index)
  ));
  const seenUrls = new Set();
  records.forEach((record) => {
    if (seenUrls.has(record.url)) {
      throw new Error(`document locations ${scopeId} contains duplicate URL ${record.url}`);
    }
    seenUrls.add(record.url);
  });
  return records;
}

async function fetchJson(url) {
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`Document locations request failed (${response.status}).`);
  }
  return response.json();
}

function searchRank(title, query) {
  if (!query) return 3;
  if (title === query) return 0;
  if (title.startsWith(query)) return 1;
  if (title.includes(query)) return 2;
  return -1;
}

/**
 * Search document titles while preserving distinct canonical placements.
 * Exact and prefix title matches lead other case-insensitive title matches.
 */
export function searchDocumentLocationRecords(records, query, excludedUrls = []) {
  const normalizedQuery = normalizeText(query).toLowerCase();
  const excluded = new Set(
    (Array.isArray(excludedUrls) ? excludedUrls : [])
      .map((url) => normalizeText(url))
      .filter(Boolean)
  );
  return (Array.isArray(records) ? records : [])
    .map((record, index) => ({
      record,
      index,
      rank: searchRank(normalizeText(record && record.document_title).toLowerCase(), normalizedQuery)
    }))
    .filter((item) => item.rank >= 0 && !excluded.has(item.record.url))
    .sort((left, right) => left.rank - right.rank || left.index - right.index)
    .map((item) => item.record);
}

export function committedDocumentLocation(record) {
  const committed = {
    url: normalizeText(record && record.url),
    scope_id: normalizeText(record && record.scope_id).toLowerCase(),
    document_title: normalizeText(record && record.document_title),
    report_title: normalizeText(record && record.report_title)
  };
  if (
    !SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS.includes(committed.scope_id)
    || !SCOPE_ROUTE_PATTERNS[committed.scope_id].test(committed.url)
    || !committed.document_title
    || committed.url.includes("&subdoc=") !== Boolean(committed.report_title)
  ) {
    throw new Error("document location commit record is invalid");
  }
  return Object.freeze(committed);
}

export function resolveDocumentLocationRecords(records, urls) {
  const byUrl = new Map(
    (Array.isArray(records) ? records : []).map((record) => [record.url, record])
  );
  return (Array.isArray(urls) ? urls : []).map((rawUrl) => {
    const url = normalizeText(rawUrl);
    const record = byUrl.get(url);
    if (record) return record;
    const docsScopeMatch = DOCS_SCOPE_ROUTE_PATTERN.exec(url);
    const scopeId = url.startsWith("/analysis/")
      ? "analysis"
      : (
          url.startsWith("/library/")
            ? "library"
            : (docsScopeMatch ? docsScopeMatch[1] : "")
        );
    return Object.freeze({
      url,
      scope_id: scopeId,
      document_title: "Unavailable document",
      report_title: "",
      available: false
    });
  });
}

/**
 * Create a cached public-projection provider.
 *
 * Each operation requires an explicit scope allowlist. The provider fetches
 * only those per-scope indexes and never reaches source or management APIs.
 */
export function createDocumentLocationProvider(options = {}) {
  const loadJson = typeof options.fetchJson === "function" ? options.fetchJson : fetchJson;
  const cache = new Map();

  async function loadScope(scopeId) {
    if (!cache.has(scopeId)) {
      cache.set(scopeId, Promise.resolve(loadJson(projectionUrl(scopeId))).then((payload) => (
        normalizeDocumentLocationProjection(payload, scopeId)
      )));
    }
    try {
      return await cache.get(scopeId);
    } catch (error) {
      cache.delete(scopeId);
      throw error;
    }
  }

  async function load(scopeIds) {
    const requestedScopeIds = normalizeDocumentLocationScopeIds(scopeIds);
    const recordsByScope = await Promise.all(
      requestedScopeIds.map((scopeId) => loadScope(scopeId))
    );
    return recordsByScope.flat();
  }

  return Object.freeze({
    async load({ scopeIds } = {}) {
      return load(scopeIds);
    },
    async search({ scopeIds, query = "", excludedUrls = [] } = {}) {
      return searchDocumentLocationRecords(
        await load(scopeIds),
        query,
        excludedUrls
      );
    },
    async resolve({ scopeIds, urls = [] } = {}) {
      return resolveDocumentLocationRecords(await load(scopeIds), urls);
    },
    clear() {
      cache.clear();
    }
  });
}
