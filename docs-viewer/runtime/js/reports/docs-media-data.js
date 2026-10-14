/** Join completed service datasets and prepare browser-owned presentation data. */

function mediaKey(value) {
  return JSON.stringify([value.role, value.media_type, value.identity]);
}

function documentSummary(record, context) {
  const target = record.target;
  return {
    target: { collection: target.collection, docId: target.doc_id },
    title: record.title,
    href: context.viewerUrlForDocument(target.doc_id, { collection: target.collection })
  };
}

function buildOwnerRows(owner, context, collator) {
  const documentsByMedia = new Map();
  owner.documents.forEach((record) => {
    const document = documentSummary(record, context);
    const documentKey = JSON.stringify([document.target.collection, document.target.docId]);
    record.references.forEach((reference) => {
      const key = mediaKey(reference);
      if (!documentsByMedia.has(key)) documentsByMedia.set(key, new Map());
      documentsByMedia.get(key).set(documentKey, document);
    });
  });
  const rows = [];
  owner.files.forEach((file) => {
    if ([".DS_Store", ".gitkeep"].includes(file.identity.split("/").at(-1))) return;
    const documents = Array.from(documentsByMedia.get(mediaKey(file))?.values() || []);
    documents.sort((left, right) => collator.compare(left.title, right.title)
      || left.title.localeCompare(right.title) || left.href.localeCompare(right.href));
    rows.push({
      collection: file.collection,
      collectionTitle: owner.title,
      mediaType: file.media_type,
      identity: file.identity,
      mediaTarget: file,
      documents,
      searchText: [owner.title, file.identity, ...documents.map((document) => document.title)]
        .map((value) => value.trim()).join(" ").toLocaleLowerCase()
    });
  });
  return rows;
}

/** Consume one completed dataset and join its owners independently.
 * The browser owns file display exclusions, document ordering and viewer links.
 * Missing metadata displays an empty report and never requests a live scan.
 */
export function buildDocsMediaSnapshot(payload, context, collator) {
  if (!payload || payload.ok !== true || !Object.hasOwn(payload, "metadata")) {
    throw new Error("Docs Media metadata response is invalid.");
  }
  const metadata = payload.metadata;
  if (metadata === null) return null;
  const owners = [];
  const rows = [];
  const countsByCollection = new Map([["*", { total: 0, orphans: 0 }]]);
  metadata.owners.forEach((owner) => {
    owners.push({ collection: owner.collection, title: owner.title });
    const ownerRows = buildOwnerRows(owner, context, collator);
    rows.push(...ownerRows);
    const counts = { total: ownerRows.length, orphans: ownerRows.filter((row) => row.documents.length === 0).length };
    countsByCollection.set(owner.collection, counts);
    const all = countsByCollection.get("*");
    all.total += counts.total;
    all.orphans += counts.orphans;
  });
  return { rows, owners, refreshedAt: metadata.refreshed_at, countsByCollection };
}
