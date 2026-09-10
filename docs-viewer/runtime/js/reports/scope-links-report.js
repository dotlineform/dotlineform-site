import { docsViewerLinksDocumentSummary } from "../shared/docs-viewer-links-presentation.js";

const COLUMNS = ["from", "to"];
const TITLE_ORDER = new Intl.Collator("en", { sensitivity: "base", numeric: true });

function documentKey(document) {
  const target = document.target;
  return JSON.stringify([target.scope, target.sub_scope, target.doc_id]);
}

/** Project directed pairs from the saved aggregate; incoming mirrors add no rows.
 * Keep complete document summaries so future icon prefixes can use owned metadata.
 */
export function readScopeLinksRows(payload) {
  if (!payload || payload.schema_version !== 1 || payload.scope !== "analysis"
    || payload.stage !== "working" || !Array.isArray(payload.documents)) {
    throw new Error("Unsupported scope Links data.");
  }
  const rows = [];
  const sources = new Set();
  payload.documents.forEach(function (record) {
    if (!record || record.schema_version !== 1 || !Array.isArray(record.outgoing)
      || !Array.isArray(record.incoming)) throw new Error("Invalid document Links record.");
    const from = docsViewerLinksDocumentSummary(record.self, payload);
    const sourceKey = documentKey(from);
    if (from.target.scope !== payload.scope || sources.has(sourceKey)) {
      throw new Error("Scope Links contains an invalid source identity.");
    }
    sources.add(sourceKey);
    const targets = new Set();
    record.outgoing.forEach(function (entry) {
      const to = docsViewerLinksDocumentSummary(entry && entry.document, payload);
      const targetKey = documentKey(to);
      if (targets.has(targetKey)) throw new Error("Scope Links contains a duplicate directed pair.");
      targets.add(targetKey);
      rows.push({ from, to });
    });
  });
  return rows;
}

/** Sort by the selected title, then the other title and exact endpoint identities.
 * Icon presentation is independent of these keys. Never reorder the saved dataset.
 */
export function sortScopeLinksRows(rows, key = "from", direction = "asc") {
  if (!COLUMNS.includes(key) || !["asc", "desc"].includes(direction)) {
    throw new Error("Invalid Links sort selection.");
  }
  const other = key === "from" ? "to" : "from";
  return rows.slice().sort(function (left, right) {
    return TITLE_ORDER.compare(left[key].title, right[key].title) * (direction === "desc" ? -1 : 1)
      || TITLE_ORDER.compare(left[other].title, right[other].title)
      || documentKey(left.from).localeCompare(documentKey(right.from))
      || documentKey(left.to).localeCompare(documentKey(right.to));
  });
}

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
 * Refresh only rereads links.json. Late responses cannot update a departed host.
 */
export function mountScopeLinksReport(context) {
  if (context.viewerScope !== "analysis" || context.viewerStage !== "working") {
    throw new Error("Links is available only in Analysis Working.");
  }
  const service = context.reportService;
  if (!service || typeof service.readScopeLinks !== "function") {
    throw new Error("Links requires the local report service.");
  }
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  const toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const refresh = documentRef.createElement("button");
  refresh.type = "button";
  refresh.className = "docsViewerReport__button docsViewerReport__button--pill";
  refresh.textContent = "🔄";
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
  let rows = [];
  let sortKey = "from";
  let sortDir = "asc";
  let requestVersion = 0;
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
    sortScopeLinksRows(rows, sortKey, sortDir).forEach(function (row) {
      const tr = documentRef.createElement("tr");
      tr.append(documentCell(documentRef, row.from), documentCell(documentRef, row.to));
      body.appendChild(tr);
    });
    table.hidden = rows.length === 0;
    status.textContent = rows.length ? `${rows.length} ${rows.length === 1 ? "link" : "links"}` : "No document links in the last scope rebuild.";
  }

  function current(version) {
    return version === requestVersion && root.isConnected !== false
      && (typeof context.isCurrentDocument !== "function" || context.isCurrentDocument());
  }

  async function load() {
    const version = ++requestVersion;
    refresh.disabled = true;
    table.hidden = true;
    body.replaceChildren();
    status.textContent = "Loading links…";
    try {
      const payload = await service.readScopeLinks({ scope: context.viewerScope, stage: context.viewerStage });
      if (!current(version)) return;
      rows = readScopeLinksRows(payload);
      render();
    } catch (error) {
      if (current(version)) {
        rows = [];
        status.textContent = `${error.message} Run Rebuild docs and Search, then Refresh.`;
      }
    } finally {
      if (current(version)) refresh.disabled = false;
    }
  }
  refresh.addEventListener("click", load);
  return load();
}
