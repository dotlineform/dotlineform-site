import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { INDEX_COLLECTION, applyWorkspaceLinksDocumentChange, prepareWorkspaceLinks, sortWorkspaceLinksRows } from "./workspace-links-data.js";
const COLUMNS = [
  { key: "fromCollection", label: "From collection", collection: true },
  { key: "from", label: "from" },
  { key: "toCollection", label: "To collection", collection: true },
  { key: "to", label: "to" }
];

function collectionCell(documentRef, summary) {
  const cell = documentRef.createElement("td");
  cell.className = "docsViewerReport__collectionCell";
  const icon = documentRef.createElement("span");
  icon.className = "docsViewer__listIcon";
  icon.style.maskImage = `url("${summary.iconUrl}")`;
  icon.setAttribute("role", "img");
  icon.setAttribute("aria-label", summary.collectionTitle);
  icon.title = summary.collectionTitle;
  cell.appendChild(icon);
  return cell;
}

function documentCell(documentRef, summary) {
  const cell = documentRef.createElement("td");
  const link = documentRef.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = summary.href;
  const title = documentRef.createElement("span");
  title.textContent = summary.title;
  link.appendChild(title);
  cell.appendChild(link);
  return cell;
}

/** Mount the local Working report and await its initial snapshot read.
 * Refresh rebuilds current records; only disposal ends the retained view's lifetime.
 */
export function mountWorkspaceLinksReport(context) {
  if (!context.managementContext) {
    throw new Error("Links is available only in Working.");
  }
  const service = context.reportService;
  if (!service || typeof service.readWorkspaceLinks !== "function" || typeof service.refreshWorkspaceLinks !== "function") {
    throw new Error("Links requires the local report service.");
  }
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  const toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const refresh = documentRef.createElement("button");
  refresh.type = "button";
  refresh.className = "docsViewer__toolbarIconButton";
  refresh.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--refresh-cw"));
  refresh.setAttribute("aria-label", "Refresh links");
  refresh.title = "Refresh links";
  const status = documentRef.createElement("p");
  status.className = "docsViewerReport__status";
  status.setAttribute("aria-live", "polite");
  const refreshGroup = documentRef.createElement("div");
  refreshGroup.className = "docsViewerReport__refreshGroup";
  refreshGroup.append(refresh, status);
  const filters = documentRef.createElement("div");
  filters.className = "docsViewerReport__collectionFilters";
  filters.setAttribute("role", "group");
  filters.setAttribute("aria-label", "Filter links by collection");
  toolbar.append(refreshGroup, filters);
  const table = documentRef.createElement("table");
  const head = documentRef.createElement("thead");
  const headings = documentRef.createElement("tr");
  const body = documentRef.createElement("tbody");
  head.appendChild(headings);
  table.append(head, body);
  root.replaceChildren(toolbar, table);
  let data = null;
  let sortKey = "from";
  let sortDir = "asc";
  let selectedCollection = null;
  let busy = false;
  let released = false;
  const filterControls = [
    { collection: null, title: "All" }, INDEX_COLLECTION,
    ...context.workspaceConfig.collectionsById.values()
  ].map(function (collection) {
    const button = documentRef.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__filter";
    button.title = collection.title;
    button.setAttribute("aria-pressed", String(collection.collection === selectedCollection));
    if (collection.collection === null) {
      button.textContent = collection.title;
      button.setAttribute("aria-label", "Show all links");
    } else {
      button.setAttribute("aria-label", `Show links involving ${collection.title}`);
      const icon = documentRef.createElement("span");
      icon.className = "docsViewer__toolbarIcon";
      icon.setAttribute("aria-hidden", "true");
      icon.style.maskImage = `url("${collection.iconUrl}")`;
      button.appendChild(icon);
    }
    button.addEventListener("click", function () {
      if (released || busy || selectedCollection === collection.collection) return;
      selectedCollection = collection.collection;
      render();
    });
    filters.appendChild(button);
    return { collection: collection.collection, button };
  });
  const controls = COLUMNS.map(function (column) {
    const key = column.key;
    const cell = documentRef.createElement("th");
    cell.scope = "col";
    const button = documentRef.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    if (column.collection) {
      cell.className = "docsViewerReport__collectionCell";
      button.setAttribute("aria-label", `Sort by ${column.label.toLowerCase()}`);
      button.title = column.label;
      button.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewerReport__collectionHeaderIcon"));
    } else {
      button.textContent = column.label;
    }
    const indicator = documentRef.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    button.appendChild(indicator);
    cell.appendChild(button);
    headings.appendChild(cell);
    button.addEventListener("click", function () {
      if (released || busy) return;
      sortDir = sortKey === key && sortDir === "asc" ? "desc" : "asc";
      sortKey = key;
      render();
    });
    return { key, cell, button, indicator };
  });

  function render() {
    filterControls.forEach(function (control) {
      control.button.setAttribute("aria-pressed", String(control.collection === selectedCollection));
    });
    controls.forEach(function (control) {
      const active = control.key === sortKey;
      control.cell.setAttribute("aria-sort", active ? (sortDir === "asc" ? "ascending" : "descending") : "none");
      control.button.dataset.state = active ? "active" : "";
      control.indicator.textContent = active ? (sortDir === "asc" ? "▲" : "▼") : "";
    });
    body.replaceChildren();
    const matching = !data ? [] : selectedCollection === null ? data.rows : data.rows.filter(function (row) {
      return row.from.collection === selectedCollection || row.to.collection === selectedCollection;
    });
    const rows = sortWorkspaceLinksRows(matching, sortKey, sortDir);
    rows.forEach(function (row) {
      const tr = documentRef.createElement("tr");
      tr.append(
        collectionCell(documentRef, row.from), documentCell(documentRef, row.from),
        collectionCell(documentRef, row.to), documentCell(documentRef, row.to)
      );
      body.appendChild(tr);
    });
    table.hidden = rows.length === 0;
    status.textContent = `${rows.length} ${rows.length === 1 ? "link" : "links"}`;
  }

  if (context.registerRetainedView) context.registerRetainedView({
    id: "workspace-links",
    capture: function () { return { key: sortKey, direction: sortDir, collection: selectedCollection }; },
    restore: function (saved) {
      if (sortKey === saved.key && sortDir === saved.direction && selectedCollection === saved.collection) return;
      sortKey = saved.key; sortDir = saved.direction; selectedCollection = saved.collection;
      if (!busy && data) render();
    },
    dispose: function () { released = true; data = null; }
  });
  if (context.collectionProvider && context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    if (!released && data && applyWorkspaceLinksDocumentChange(data, change)) render();
  });

  async function load(rebuild = false) {
    if (released || busy) return;
    busy = true;
    data = null;
    refresh.disabled = true;
    filterControls.forEach(function (control) { control.button.disabled = true; });
    table.hidden = true;
    body.replaceChildren();
    status.textContent = "";
    try {
      const payload = await (rebuild ? service.refreshWorkspaceLinks() : service.readWorkspaceLinks());
      if (released) return;
      data = prepareWorkspaceLinks(payload, context.viewerUrlForDocument, context.workspaceConfig.collectionsById);
      render();
    } catch (error) {
      if (!released) {
        data = null;
        body.replaceChildren();
        table.hidden = true;
        status.textContent = `${error.message} Use Refresh to rebuild the Links report.`;
      }
    } finally {
      if (!released) {
        busy = false;
        refresh.disabled = false;
        filterControls.forEach(function (control) { control.button.disabled = !data; });
      }
    }
  }
  refresh.addEventListener("click", function () { load(true); });
  return load();
}
