export function bookHeadings(tree) {
  return tree.flatMap(node => [node, ...(node.sections || [])]);
}

export function bookDocumentList(order, headingId) {
  if (headingId === "") return order.root;
  if (headingId === "@front") return order.front;
  if (headingId === "@back") return order.back;
  return bookHeadings(order.tree).find(heading => heading.id === headingId).doc_ids;
}

export function isBookMatter(order, docId) {
  return order.front.includes(docId) || order.back.includes(docId);
}

export function createBookManifestStore(fetchManifest) {
  const entries = new Map();

  function read(book) {
    let entry = entries.get(book.collection);
    if (!entry) {
      entry = {};
      entry.ready = fetchManifest(book.manifestUrl).then(manifest => {
        entry.manifest = manifest;
        return manifest;
      }).catch(error => {
        entries.delete(book.collection);
        throw error;
      });
      entries.set(book.collection, entry);
    }
    return entry.ready;
  }

  function project(change) {
    const manifest = entries.get(change.target.collection)?.manifest;
    if (!manifest) return;
    const docId = change.target.doc_id;
    const index = manifest.docs.findIndex(row => row.doc_id === docId);
    if (change.deleted) {
      if (index < 0) return;
      manifest.docs.splice(index, 1);
      const order = manifest.book_order;
      const lists = [order.front, order.root, ...bookHeadings(order.tree).map(heading => heading.doc_ids), order.back];
      const placement = lists.find(ids => ids.includes(docId));
      placement?.splice(placement.indexOf(docId), 1);
    } else if (index < 0) {
      manifest.docs.push(change.record);
      if (change.book_heading_id !== undefined) {
        bookDocumentList(manifest.book_order, change.book_heading_id).push(docId);
      }
    } else {
      manifest.docs[index] = change.record;
    }
  }

  return { read, project };
}
