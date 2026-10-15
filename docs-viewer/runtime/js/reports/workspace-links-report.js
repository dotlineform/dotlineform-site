import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { applyWorkspaceLinksDocumentChange, prepareWorkspaceLinks, sortWorkspaceLinksRows } from "./workspace-links-data.js";
const COLUMNS = ["from", "to"];

function documentCell(documentRef, summary) {
  const cell = documentRef.createElement("td");
  const link = documentRef.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = summary.href;
  // A later shared icon policy can prefix the title without changing its text/key.
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
  toolbar.append(refresh, status);
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
  let busy = false;
  let released = false;
  const controls = COLUMNS.map(function (key) {
    const cell = documentRef.createElement("th");
    cell.scope = "col";
    const button = documentRef.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.textContent = key;
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
    controls.forEach(function (control) {
      const active = control.key === sortKey;
      control.cell.setAttribute("aria-sort", active ? (sortDir === "asc" ? "ascending" : "descending") : "none");
      control.button.dataset.state = active ? "active" : "";
      control.indicator.textContent = active ? (sortDir === "asc" ? "▲" : "▼") : "";
    });
    body.replaceChildren();
    const rows = data ? sortWorkspaceLinksRows(data.rows, sortKey, sortDir) : [];
    rows.forEach(function (row) {
      const tr = documentRef.createElement("tr");
      tr.append(documentCell(documentRef, row.from), documentCell(documentRef, row.to));
      body.appendChild(tr);
    });
    table.hidden = rows.length === 0;
    status.textContent = rows.length ? `${rows.length} ${rows.length === 1 ? "link" : "links"}` : "No document links in the saved report.";
  }

  if (context.registerRetainedView) context.registerRetainedView({
    id: "workspace-links",
    capture: function () { return { key: sortKey, direction: sortDir }; },
    restore: function (saved) {
      if (sortKey === saved.key && sortDir === saved.direction) return;
      sortKey = saved.key; sortDir = saved.direction;
      if (!busy) render();
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
    table.hidden = true;
    body.replaceChildren();
    status.textContent = "";
    try {
      const payload = await (rebuild ? service.refreshWorkspaceLinks() : service.readWorkspaceLinks());
      if (released) return;
      data = prepareWorkspaceLinks(payload, context.viewerUrlForDocument);
      render();
    } catch (error) {
      if (!released) {
        data = null;
        body.replaceChildren();
        table.hidden = true;
        status.textContent = `${error.message} Use Refresh to rebuild the Links report.`;
      }
    } finally {
      if (!released) { busy = false; refresh.disabled = false; }
    }
  }
  refresh.addEventListener("click", function () { load(true); });
  return load();
}
