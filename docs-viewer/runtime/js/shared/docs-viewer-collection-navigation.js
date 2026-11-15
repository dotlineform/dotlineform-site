import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

// A sequence belongs to the invoking link and travels only through same-tab reader navigation.
const sequencesByLink = new WeakMap();

export function registerCollectionNavigationLink(link, getSequence) {
  sequencesByLink.set(link, getSequence);
}

export function collectionSequenceForLink(link) {
  return sequencesByLink.get(link)?.();
}

export function registerBookTocLinks(toc) {
  const links = Array.from(toc.querySelectorAll("a"));
  const order = toc.dataset.bookOrder;
  if (!order) {
    if (links.length < 2) return;
    const rows = links.map(link => ({ href: link.href, title: link.textContent }));
    links.forEach((link, position) => registerCollectionNavigationLink(link, () => ({ rows, position })));
    return;
  }
  const hostId = toc.dataset.bookHost;
  const collection = toc.dataset.docsBookToc;
  const entries = JSON.parse(order);
  if (entries.length < 2) return;
  const rows = entries.map(([docId, title]) => {
    const query = new URLSearchParams({ doc: docId });
    if (docId !== hostId) query.set("collection", collection);
    return { href: "?" + query.toString(), title };
  });
  const positions = new Map(entries.map(([docId], position) => [docId, position]));
  const sequence = { rows, position: positions.get(hostId), bookHostId: hostId };
  links.forEach(link => {
    const docId = new URL(link.href).searchParams.get("doc");
    registerCollectionNavigationLink(link, () => ({ ...sequence, position: positions.get(docId) }));
  });
  return sequence;
}

export function createCollectionNavigation(document, sequence, atTop) {
  const { rows, position } = sequence;
  const nav = document.createElement("nav");
  nav.className = "docsViewer__collectionNavigation";
  nav.classList.add(atTop ? "docsViewer__collectionNavigation--top" : "docsViewer__collectionNavigation--bottom");
  nav.setAttribute("aria-label", "Collection document navigation");

  for (const [offset, label, direction] of [[-1, "Previous", "left"], [1, "Next", "right"]]) {
    const adjacent = position + offset;
    const row = rows[adjacent];
    if (!row) continue;
    const link = document.createElement("a");
    link.className = "docsViewer__collectionNavigationLink";
    link.href = row.href;
    link.title = row.title;
    link.setAttribute("aria-label", label + " · " + row.title);
    const title = document.createElement("span");
    title.className = "docsViewer__collectionNavigationTitle";
    title.textContent = row.title;
    const icon = createDocsViewerToolbarIcon(document, "docsViewer__icon--chevron-" + direction);
    if (offset < 0) link.append(icon, title);
    else {
      link.classList.add("docsViewer__collectionNavigationLink--next");
      link.append(title, icon);
    }
    registerCollectionNavigationLink(link, () => ({ ...sequence, position: adjacent }));
    nav.append(link);
  }
  return nav;
}
