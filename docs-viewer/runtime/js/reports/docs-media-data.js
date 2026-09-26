/** Validate generic media reads and assemble local report rows in the browser. */

const DOC_ID = /^d-\d{8}-\d{6}-[0-9a-f]{6}$/;
const TOKEN = /^[a-z0-9][a-z0-9_-]*$/;

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === keys.slice().sort().join(",");
}

function exactString(value) {
  return typeof value === "string" && value === value.trim();
}

function collectionId(value) {
  return exactString(value) && (value === "" || TOKEN.test(value));
}

function mediaIdentity(value) {
  return exactString(value) && value.length > 0 && !value.includes("\\")
    && Array.from(value).every((character) => character.codePointAt(0) >= 32 && character.codePointAt(0) !== 127)
    && value.split("/").every((part) => part && part !== "." && part !== "..");
}

function mediaKey(value) {
  if (!exactString(value.media_type) || !TOKEN.test(value.media_type)
    || !["source", "build-source"].includes(value.role) || !mediaIdentity(value.identity)) {
    throw new Error("Docs media identity is invalid.");
  }
  return JSON.stringify([value.role, value.media_type, value.identity]);
}

function validateRead(payload, request, schema, fields) {
  if (!exactKeys(payload, ["ok", "schema_version", "stage", "collection", ...fields])
    || payload.ok !== true || payload.schema_version !== schema
    || payload.stage !== request.stage || payload.collection !== request.collection) {
    throw new Error("Docs media data does not match the requested owner.");
  }
}

function collectionHosts(records) {
  if (!Array.isArray(records)) throw new Error("Docs media collection hosts are invalid.");
  const hosts = new Map();
  records.forEach((record) => {
    if (!exactKeys(record, ["collection", "report_host_doc_id"])
      || !collectionId(record.collection) || !record.collection
      || !exactString(record.report_host_doc_id) || !DOC_ID.test(record.report_host_doc_id)
      || hosts.has(record.collection)) {
      throw new Error("Docs media collection host is invalid.");
    }
    hosts.set(record.collection, record.report_host_doc_id);
  });
  return hosts;
}

function documentSummary(record, stage, hosts, context) {
  const target = record && record.target;
  if (!exactKeys(record, ["target", "title", "references"])
    || !exactKeys(target, ["stage", "collection", "doc_id"])
    || target.stage !== stage || !collectionId(target.collection)
    || !exactString(target.doc_id) || !DOC_ID.test(target.doc_id)
    || !exactString(record.title) || !record.title || !Array.isArray(record.references)) {
    throw new Error("Docs media document reference is invalid.");
  }
  const hostId = target.collection ? hosts.get(target.collection) : target.doc_id;
  if (!hostId || typeof context.viewerUrlForDocument !== "function") {
    throw new Error("Docs media document location is unavailable.");
  }
  const url = new URL(context.viewerUrlForDocument(hostId, { manage: true, stage }), "http://docs.local");
  if (url.pathname !== "/docs/" || url.searchParams.get("stage") !== stage
    || url.searchParams.get("doc") !== hostId || url.searchParams.has("subdoc")) {
    throw new Error("Docs media document location does not match its exact target.");
  }
  if (target.collection) url.searchParams.set("subdoc", target.doc_id);
  return {
    target: { stage, collection: target.collection, docId: target.doc_id },
    title: record.title,
    href: url.pathname + url.search
  };
}

/** Join one exact owner's live files to source references, without inferring missing files or build relationships.
 * Document links use configured collection host IDs and the viewer's existing route builder.
 * File exclusions, document deduplication and title ordering are report presentation policy.
 */
export function buildDocsMediaRows(filesPayload, referencesPayload, request, context) {
  if (!exactKeys(request, ["stage", "collection"]) || request.stage !== "working"
    || !collectionId(request.collection)) {
    throw new Error("Docs media requires an exact Working media owner.");
  }
  validateRead(filesPayload, request, "docs_media_files_v1", ["files"]);
  validateRead(referencesPayload, request, "docs_media_references_v1", ["collection_hosts", "documents"]);
  if (!Array.isArray(filesPayload.files) || !Array.isArray(referencesPayload.documents)) {
    throw new Error("Docs media files or document references are invalid.");
  }
  const hosts = collectionHosts(referencesPayload.collection_hosts);
  const documentsByMedia = new Map();
  const documentIds = new Set();
  referencesPayload.documents.forEach((record) => {
    const document = documentSummary(record, request.stage, hosts, context);
    const documentKey = JSON.stringify([document.target.stage, document.target.collection, document.target.docId]);
    if (documentIds.has(documentKey)) throw new Error("Docs media contains a duplicate document identity.");
    documentIds.add(documentKey);
    record.references.forEach((reference) => {
      if (!exactKeys(reference, ["role", "media_type", "identity"]) || reference.role !== "source") {
        throw new Error("Docs media reference is invalid.");
      }
      const key = mediaKey(reference);
      if (!documentsByMedia.has(key)) documentsByMedia.set(key, new Map());
      documentsByMedia.get(key).set(documentKey, document);
    });
  });
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const fileIds = new Set();
  const rows = [];
  filesPayload.files.forEach((file) => {
    if (!exactKeys(file, ["stage", "collection", "role", "media_type", "identity"])
      || file.stage !== request.stage || file.collection !== request.collection) {
      throw new Error("Docs media file does not match its owner.");
    }
    const key = mediaKey(file);
    if (fileIds.has(key)) throw new Error("Docs media contains a duplicate file identity.");
    fileIds.add(key);
    if (file.identity.split("/").at(-1) === ".DS_Store") return;
    const documents = Array.from(documentsByMedia.get(key)?.values() || []);
    documents.sort((left, right) => collator.compare(left.title, right.title)
      || left.title.localeCompare(right.title) || left.href.localeCompare(right.href));
    rows.push({
      stage: file.stage,
      collection: file.collection,
      mediaType: file.media_type,
      identity: file.identity,
      mediaTarget: { ...file },
      documents
    });
  });
  return rows;
}
