/** Prepare Build-owned directed pairs and share each exact endpoint across rows. */

const TITLE_ORDER = new Intl.Collator("en", { sensitivity: "base", numeric: true });
/** Ordinary Index documents use the empty collection identity and fixed document artwork. */
export const INDEX_COLLECTION = {
  collection: "",
  title: "Index",
  iconUrl: new URL("../../../static/icons/dlf-doc.svg", import.meta.url).href
};

/**
 * @typedef {{collection: string, doc_id: string, title: string, collectionTitle: string, iconUrl: string, key: string, href: string, uses: number}} LinkEndpoint
 * @typedef {{from: LinkEndpoint, to: LinkEndpoint}} LinkRow
 * @typedef {{rows: LinkRow[], endpoints: Map<string, Map<string, LinkEndpoint>>}} WorkspaceLinksData
 */

/** Incoming mirrors add no rows. Resolve keys, routes and collection presentation once per used endpoint.
 * @param {object} payload Completed saved aggregate.
 * @param {function(string, {collection: string}): string} viewerUrlForDocument Active reader's exact route owner.
 * @param {Map<string, {title: string, iconUrl: string}>} collectionsById Loaded configured collection presentation.
 * @returns {WorkspaceLinksData} View-owned rows and shared endpoints; rebuild on Refresh.
 */
export function prepareWorkspaceLinks(payload, viewerUrlForDocument, collectionsById) {
  const data = { rows: [], endpoints: new Map() };
  function endpoint(summary) {
    let collection = data.endpoints.get(summary.collection);
    if (!collection) {
      collection = new Map();
      data.endpoints.set(summary.collection, collection);
    }
    let prepared = collection.get(summary.doc_id);
    if (!prepared) {
      const presentation = summary.collection ? collectionsById.get(summary.collection) : INDEX_COLLECTION;
      prepared = {
        ...summary, key: JSON.stringify([summary.collection, summary.doc_id]), uses: 0,
        collectionTitle: presentation.title, iconUrl: presentation.iconUrl,
        href: viewerUrlForDocument(summary.doc_id, { collection: summary.collection })
      };
      collection.set(summary.doc_id, prepared);
    }
    return prepared;
  }
  payload.documents.forEach((record) => {
    if (!record.outgoing.length) return;
    const from = endpoint(record.self);
    record.outgoing.forEach((summary) => {
      const to = endpoint(summary);
      from.uses += 1;
      to.uses += 1;
      data.rows.push({ from, to });
    });
  });
  return data;
}

/** Sort a title or collection title without reordering saved rows. Collection ties use document titles ascending. */
export function sortWorkspaceLinksRows(rows, key, direction) {
  const collectionSort = key === "fromCollection" || key === "toCollection";
  const side = key === "from" || key === "fromCollection" ? "from" : "to";
  const other = side === "from" ? "to" : "from";
  const field = collectionSort ? "collectionTitle" : "title";
  return rows.slice().sort((left, right) => (
    TITLE_ORDER.compare(left[side][field], right[side][field]) * (direction === "desc" ? -1 : 1)
    || (collectionSort ? TITLE_ORDER.compare(left[side].title, right[side].title) : 0)
    || TITLE_ORDER.compare(left[other].title, right[other].title)
    || left.from.key.localeCompare(right.from.key)
    || left.to.key.localeCompare(right.to.key)
  ));
}

/** Apply a committed title/deletion once; no effect means no table reordering.
 * @param {WorkspaceLinksData} data Prepared view state, mutated only by committed effects.
 * @param {object} change Collection provider's committed document change.
 * @returns {boolean} Whether displayed rows or titles changed.
 */
export function applyWorkspaceLinksDocumentChange(data, change) {
  const collection = data.endpoints.get(change.target.collection || "");
  const endpoint = collection?.get(change.target.doc_id);
  if (!endpoint) return false;
  if (!change.deleted) {
    if (endpoint.title === change.record.title) return false;
    endpoint.title = change.record.title;
    return true;
  }
  data.rows = data.rows.filter((row) => {
    if (row.from !== endpoint && row.to !== endpoint) return true;
    [row.from, row.to].forEach((removed) => {
      removed.uses -= 1;
      if (removed.uses) return;
      const owner = data.endpoints.get(removed.collection);
      owner.delete(removed.doc_id);
      if (!owner.size) data.endpoints.delete(removed.collection);
    });
    return false;
  });
  return true;
}
