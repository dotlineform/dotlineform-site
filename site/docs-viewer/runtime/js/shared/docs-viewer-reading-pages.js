import { mountDocsViewerPaginationControl } from "./docs-viewer-pagination-control.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

const BREAK = "[data-docs-page-break]";
const PAGE_CLASS = "docsViewer__readingPage";

function pageGroups(root) {
  const groups = [];
  let nodes = [];
  function finishPage() {
    if (nodes.some(node => node.nodeType === 1 || (node.nodeType === 3 && node.data.trim()))) groups.push(nodes);
    nodes = [];
  }
  for (const node of root.childNodes) {
    if (node.nodeType === 1 && node.matches(BREAK)) finishPage();
    else nodes.push(node);
  }
  finishPage();
  return groups;
}

function pageButton(document, label, artwork) {
  const control = document.createElement("button");
  control.type = "button";
  control.className = "docsViewer__toolbarIconButton";
  control.title = label;
  control.setAttribute("aria-label", label);
  control.append(createDocsViewerToolbarIcon(document, artwork));
  return control;
}

/** Group the content once. Own the visible page and mode for this document mount. */
export function mountDocsViewerReadingPages(root, onPageChange) {
  if (!root.querySelector(":scope > " + BREAK)) return null;
  const groups = pageGroups(root);
  if (groups.length < 2) return null;
  const document = root.ownerDocument;
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewer__readingPageToolbar";
  const firstInToolbar = pageButton(document, "Go to page 1", "docsViewer__icon--arrow-left-to-line");
  toolbar.append(firstInToolbar);
  const pagination = mountDocsViewerPaginationControl({ host: toolbar, enabled: true, itemsLabel: "text", change: togglePagination });
  const pages = groups.map(nodes => {
    const page = document.createElement("div");
    page.className = PAGE_CLASS;
    page.tabIndex = -1;
    page.append(...nodes);
    return page;
  });
  const footer = document.createElement("nav");
  footer.className = "docsViewer__readingPageNavigation";
  footer.setAttribute("aria-label", "Reading page navigation");
  const firstInFooter = pageButton(document, "Go to page 1", "docsViewer__icon--arrow-left-to-line");
  const previous = pageButton(document, "Previous page", "docsViewer__icon--chevron-left");
  const next = pageButton(document, "Next page", "docsViewer__icon--chevron-right");
  const count = document.createElement("span");
  count.setAttribute("aria-live", "polite");
  footer.append(firstInFooter, previous, count, next);
  root.replaceChildren(...pages, footer);

  // Null selects continuous mode. An absent requested page opens the first page.
  let position;
  function setPage(requested) {
    position = requested === null ? null : Math.min(requested ?? 1, pages.length);
    pages.forEach((page, index) => { page.hidden = position !== null && position !== index + 1; });
    pagination.update(position !== null);
    footer.hidden = position === null;
    count.textContent = position === null ? "" : `${position} / ${pages.length}`;
    previous.disabled = position === 1;
    next.disabled = position === pages.length;
  }
  function goToPage(number) {
    if (position !== null && position !== number) setPage(number);
    const page = pages[number - 1];
    onPageChange();
    page.focus({ preventScroll: true });
    page.scrollIntoView({ block: "start" });
  }
  firstInToolbar.addEventListener("click", () => goToPage(1));
  firstInFooter.addEventListener("click", () => goToPage(1));
  previous.addEventListener("click", () => goToPage(position - 1));
  next.addEventListener("click", () => goToPage(position + 1));
  function togglePagination(enabled) {
    let destination = position;
    if (enabled) {
      // Use the same offset as page scrolling, allowing for subpixel alignment.
      const top = Number.parseFloat(document.defaultView.getComputedStyle(pages[0]).scrollMarginBlockStart) + 1;
      const index = pages.findIndex(page => page.getBoundingClientRect().bottom > top);
      destination = index === -1 ? pages.length : index + 1;
    }
    setPage(enabled ? destination : null);
    onPageChange();
    pages[destination - 1].scrollIntoView({ block: "start" });
  }

  return {
    toolbar,
    setPage,
    position: () => position,
    reveal(element) {
      if (position === null) return;
      const index = pages.indexOf(element.closest("." + PAGE_CLASS));
      if (index !== -1 && position !== index + 1) setPage(index + 1);
    },
    scrollToStart() {
      pages[(position ?? 1) - 1].scrollIntoView({ block: "start" });
    }
  };
}
