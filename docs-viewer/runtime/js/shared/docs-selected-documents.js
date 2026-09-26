/** Validate the stage-independent selection list and order its display rows. */
export function selectedDocumentRows(payload) {
  if (!payload || payload.schema !== "docs_selected_v1" || !Array.isArray(payload.docs)) {
    throw new Error("Selected Documents data is invalid.");
  }
  const seen = new Set();
  const identity = /^d-\d{8}-\d{6}-[0-9a-f]{6}$/;
  const rows = payload.docs.map(function (row) {
    if (!row || typeof row.doc_id !== "string" || !identity.test(row.doc_id)
      || typeof row.title !== "string" || !row.title.trim()
      || typeof row.last_updated !== "string" || !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(row.last_updated)) {
      throw new Error("Selected Documents row is incomplete.");
    }
    const collection = Object.hasOwn(row, "collection");
    const fields = collection ? ["collection", "doc_id", "last_updated", "report_doc_id", "title"] : ["doc_id", "last_updated", "title"];
    if (Object.keys(row).sort().join() !== fields.join()
      || collection && (typeof row.collection !== "string" || !/^[a-z0-9][a-z0-9_-]*$/.test(row.collection)
        || typeof row.report_doc_id !== "string" || !identity.test(row.report_doc_id))) {
      throw new Error("Selected Documents requires exact document and collection identities.");
    }
    const key = (collection ? row.collection : "") + "/" + row.doc_id;
    if (seen.has(key)) throw new Error("Selected Documents contains duplicate targets.");
    seen.add(key);
    return row;
  });
  return rows.sort(function (a, b) {
    return b.last_updated.localeCompare(a.last_updated)
      || (a.collection || "").localeCompare(b.collection || "")
      || a.doc_id.localeCompare(b.doc_id);
  });
}
