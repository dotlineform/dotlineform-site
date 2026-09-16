const DOCUMENT_LOCATION_SCHEMA_VERSION = "docs_document_locations_v2";
const IMMUTABLE_DOC_ID = "d-\\d{8}-\\d{6}-[a-f0-9]{6}";

const DOCUMENT_ROUTE_PATTERN = new RegExp(`^/analysis/\\?doc=${IMMUTABLE_DOC_ID}(?:&subdoc=${IMMUTABLE_DOC_ID})?$`);
const PROJECTION_URL = "/assets/data/search/analysis/document-locations.json";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function exactRecordKeys(record) {
  return Object.keys(record).sort().join(",");
}

function normalizeProjectionRecord(rawRecord, index) {
  const field = `document locations.records[${index}]`;
  if (!rawRecord || typeof rawRecord !== "object" || Array.isArray(rawRecord)) {
    throw new Error(`${field} must be an object`);
  }
  if (exactRecordKeys(rawRecord) !== "document_title,report_title,url") {
    throw new Error(`${field} has unsupported fields`);
  }
  const record = {
    url: normalizeText(rawRecord.url),
    document_title: normalizeText(rawRecord.document_title),
    report_title: normalizeText(rawRecord.report_title),
    available: true
  };
  if (!record.document_title) {
    throw new Error(`${field}.document_title must not be empty`);
  }
  if (!DOCUMENT_ROUTE_PATTERN.test(record.url)) {
    throw new Error(`${field}.url is not a canonical public document location`);
  }
  if (record.url.includes("&subdoc=") !== Boolean(record.report_title)) {
    throw new Error(`${field}.report_title must identify collection placements only`);
  }
  return Object.freeze(record);
}

export function normalizeDocumentLocationProjection(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error(`document locations must be an object`);
  }
  if (payload.schema_version !== DOCUMENT_LOCATION_SCHEMA_VERSION) {
    throw new Error(`document locations has an unsupported schema`);
  }
  if (exactRecordKeys(payload) !== "records,schema_version") {
    throw new Error("document locations has unsupported fields");
  }
  if (!Array.isArray(payload.records)) {
    throw new Error(`document locations.records must be an array`);
  }
  const records = payload.records.map((record, index) => (
    normalizeProjectionRecord(record, index)
  ));
  const seenUrls = new Set();
  records.forEach((record) => {
    if (seenUrls.has(record.url)) {
      throw new Error(`document locations contains duplicate URL ${record.url}`);
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
    document_title: normalizeText(record && record.document_title),
    report_title: normalizeText(record && record.report_title)
  };
  if (
    !DOCUMENT_ROUTE_PATTERN.test(committed.url)
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
    return Object.freeze({
      url,
      document_title: "Unavailable document",
      report_title: "",
      available: false
    });
  });
}

/** Create a cached reader for the accepted public document-location projection.
 * Reads never reach source or management APIs; failures clear only this cache.
 */
export function createDocumentLocationProvider(options = {}) {
  const loadJson = typeof options.fetchJson === "function" ? options.fetchJson : fetchJson;
  let cached = null;

  async function load() {
    if (!cached) {
      cached = Promise.resolve().then(() => loadJson(PROJECTION_URL)).then(normalizeDocumentLocationProjection);
    }
    try {
      return await cached;
    } catch (error) {
      cached = null;
      throw error;
    }
  }

  return Object.freeze({
    load,
    async search({ query = "", excludedUrls = [] } = {}) {
      return searchDocumentLocationRecords(await load(), query, excludedUrls);
    },
    async resolve({ urls = [] } = {}) {
      return resolveDocumentLocationRecords(await load(), urls);
    },
    clear() {
      cached = null;
    }
  });
}
