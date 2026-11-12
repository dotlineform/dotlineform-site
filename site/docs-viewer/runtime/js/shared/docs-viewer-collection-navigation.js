import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

// A sequence belongs to the invoking link and travels only through same-tab reader navigation.
const sequencesByLink = new WeakMap();

export function registerCollectionNavigationLink(link, getSequence) {
  sequencesByLink.set(link, getSequence);
}

export function collectionSequenceForLink(link) {
  return sequencesByLink.get(link)?.();
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
    registerCollectionNavigationLink(link, () => ({ rows, position: adjacent }));
    nav.append(link);
  }
  return nav;
}
