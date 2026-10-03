/**
 * @typedef {Object} DocumentTarget
 * @property {string} doc_id Exact immutable document ID, or the selected Review package's safe ID.
 * @property {string} [collection] Configured named storage owner; omitted for ordinary documents.
 */

/** Validate exact reader identity; collection names select storage, never a browse host.
 * @returns {Readonly<DocumentTarget>}
 */
export function documentTarget(value, options = {}) {
  var target = typeof value === "string" ? { doc_id: value } : value || {};
  var collection = target.collection || "";
  var docId = target.doc_id;
  if (typeof collection !== "string" || !/^(?:[a-z][a-z0-9-]*)?$/.test(collection)
    || typeof docId !== "string"
    || !(options.review ? /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/ : collection === "catalogue" ? /^[0-9]{5}$/ : /^d-\d{8}-\d{6}-[a-f0-9]{6}$/).test(docId)) {
    throw new Error("Document navigation requires an exact collection and document ID.");
  }
  return Object.freeze(collection ? { collection: collection, doc_id: docId } : { doc_id: docId });
}

/** Keys are page-session identities, independent of title, URL and Index selection. */
export function documentTargetKey(value) {
  return value ? (value.collection || "") + ":" + value.doc_id : "";
}
