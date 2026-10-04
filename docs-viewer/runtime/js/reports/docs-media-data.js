/** Validate saved media datasets and assemble local report rows in the browser. */

const DOC_ID = /^d-\d{8}-\d{6}-[0-9a-f]{6}$/;
function documentId(value, collection) {
  return (collection === "catalogue" ? /^[0-9]{5}$/ : DOC_ID).test(value);
}
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
    || value.media_type === "thumbs" || !["source", "build-source"].includes(value.role) || !mediaIdentity(value.identity)) {
    throw new Error("Docs media identity is invalid.");
  }
  return JSON.stringify([value.role, value.media_type, value.identity]);
}

function documentSummary(record, owner, context) {
  const target = record && record.target;
  if (!exactKeys(record, ["target", "title", "references"])
    || !exactKeys(target, ["collection", "doc_id"])
    || !collectionId(target.collection)
    || target.collection !== owner.collection
    || !exactString(target.doc_id) || !documentId(target.doc_id, target.collection)
    || !exactString(record.title) || !record.title || !Array.isArray(record.references)) {
    throw new Error("Docs media document reference is invalid.");
  }
  if (typeof context.viewerUrlForDocument !== "function") {
    throw new Error("Docs media document location is unavailable.");
  }
  const url = new URL(context.viewerUrlForDocument(target.doc_id, { collection: target.collection }), "http://docs.local");
  if (url.pathname !== "/docs/"
    || url.searchParams.get("doc") !== target.doc_id || (url.searchParams.get("collection") || "") !== target.collection) {
    throw new Error("Docs media document location does not match its exact target.");
  }
  return {
    target: {  collection: target.collection, docId: target.doc_id },
    title: record.title,
    href: url.pathname + url.search
  };
}

function buildOwnerRows(owner, context) {
  const documentsByMedia = new Map();
  const documentIds = new Set();
  owner.documents.forEach((record) => {
    const document = documentSummary(record, owner, context);
    const documentKey = JSON.stringify([document.target.collection, document.target.docId]);
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
  owner.files.forEach((file) => {
    if (!exactKeys(file, ["collection", "role", "media_type", "identity"])
      || file.collection !== owner.collection) {
      throw new Error("Docs media file does not match its owner.");
    }
    const key = mediaKey(file);
    if (fileIds.has(key)) throw new Error("Docs media contains a duplicate file identity.");
    fileIds.add(key);
    if ([".DS_Store", ".gitkeep"].includes(file.identity.split("/").at(-1))) return;
    const documents = Array.from(documentsByMedia.get(key)?.values() || []);
    documents.sort((left, right) => collator.compare(left.title, right.title)
      || left.title.localeCompare(right.title) || left.href.localeCompare(right.href));
    rows.push({
      collection: file.collection,
      collectionTitle: owner.title,
      mediaType: file.media_type,
      identity: file.identity,
      mediaTarget: { ...file },
      documents
    });
  });
  return rows;
}

/** Validate one complete saved snapshot and join its owners independently.
 * The browser owns file display exclusions, document ordering and viewer links.
 * Missing metadata displays an empty report and never requests a live scan.
 */
export function buildDocsMediaSnapshot(payload, context) {
  if (!exactKeys(payload, ["ok", "metadata"]) || payload.ok !== true) {
    throw new Error("Docs Media metadata response is invalid.");
  }
  const metadata = payload.metadata;
  if (metadata === null) return null;
  if (!exactKeys(metadata, ["schema_version", "refreshed_at", "owners"])
    || metadata.schema_version !== "docs_media_metadata_v1"
    || !exactString(metadata.refreshed_at)
    || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(metadata.refreshed_at)
    || !Number.isFinite(Date.parse(metadata.refreshed_at)) || !Array.isArray(metadata.owners)) {
    throw new Error("Docs Media metadata is invalid. Use Run/Refresh to regenerate it.");
  }
  const identities = new Set();
  const owners = [];
  const rows = [];
  metadata.owners.forEach((owner) => {
    if (!exactKeys(owner, ["collection", "title", "files", "documents"])
      || !collectionId(owner.collection) || identities.has(owner.collection)
      || !exactString(owner.title) || !owner.title
      || !Array.isArray(owner.files) || !Array.isArray(owner.documents)) {
      throw new Error("Docs Media metadata has an invalid owner.");
    }
    identities.add(owner.collection);
    owners.push({ collection: owner.collection, title: owner.title });
    rows.push(...buildOwnerRows(owner, context));
  });
  if (!identities.has("")) throw new Error("Docs Media metadata requires the ordinary owner.");
  return { rows, owners, refreshedAt: metadata.refreshed_at };
}
