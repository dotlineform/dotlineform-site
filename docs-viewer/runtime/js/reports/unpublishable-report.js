/** Validate Working identities before rendering local document links. */
export function readUnpublishableRows(payload) {
  if (!payload || payload.ok !== true || payload.schema_version !== "docs_unpublishable_report_v1"
    || payload.scope !== "analysis" || payload.stage !== "working" || !Array.isArray(payload.rows)) {
    throw new Error("Unpublishable report data is invalid.");
  }
  const seen = new Set();
  return payload.rows.map(function (row) {
    const target = row && row.target;
    if (!target || target.scope !== payload.scope || target.stage !== payload.stage
      || target.sub_scope !== "" || typeof target.doc_id !== "string" || !target.doc_id
      || typeof row.title !== "string" || !row.title
      || typeof row.collection_title !== "string" || !row.collection_title
      || typeof row.href !== "string") {
      throw new Error("Unpublishable document identity is invalid.");
    }
    const key = JSON.stringify([target.sub_scope, target.doc_id]);
    const url = new URL(row.href, "http://docs.invalid");
    if (seen.has(key) || !row.href.startsWith("/docs/?") || url.origin !== "http://docs.invalid"
      || url.searchParams.get("scope") !== target.scope || url.searchParams.get("stage") !== target.stage
      || url.searchParams.get("doc") !== target.doc_id
      || url.searchParams.has("subdoc")) {
      throw new Error("Unpublishable document link is invalid.");
    }
    seen.add(key);
    return row;
  });
}

/** Mount a read-only source report within the exact Analysis Working document. */
export function mountUnpublishableReport(context) {
  if (context.viewerScope !== "analysis" || context.viewerStage !== "working") {
    throw new Error("Unpublishable is available only in Analysis Working.");
  }
  const service = context.reportService;
  if (!service || typeof service.readUnpublishable !== "function") {
    throw new Error("Unpublishable requires the local report service.");
  }
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  const toolbar = documentRef.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const refresh = documentRef.createElement("button");
  refresh.type = "button";
  refresh.className = "docsViewerReport__button";
  refresh.textContent = "Refresh";
  toolbar.appendChild(refresh);
  const status = documentRef.createElement("p");
  status.className = "docsViewerReport__status";
  status.setAttribute("aria-live", "polite");
  const table = documentRef.createElement("table");
  const head = documentRef.createElement("thead");
  const headings = documentRef.createElement("tr");
  ["Title"].forEach(function (label) {
    const cell = documentRef.createElement("th");
    cell.scope = "col";
    cell.textContent = label;
    headings.appendChild(cell);
  });
  head.appendChild(headings);
  const body = documentRef.createElement("tbody");
  table.append(head, body);
  root.replaceChildren(toolbar, status, table);
  let requestVersion = 0;

  function current(version) {
    return version === requestVersion && root.isConnected !== false
      && (typeof context.isCurrentDocument !== "function" || context.isCurrentDocument());
  }

  async function load() {
    const version = ++requestVersion;
    refresh.disabled = true;
    body.replaceChildren();
    table.hidden = true;
    status.textContent = "Loading documents…";
    try {
      const payload = await service.readUnpublishable({ scope: context.viewerScope, stage: context.viewerStage });
      if (!current(version)) return;
      const rows = readUnpublishableRows(payload);
      rows.forEach(function (row) {
        const tr = documentRef.createElement("tr");
        const title = documentRef.createElement("td");
        const link = documentRef.createElement("a");
        link.className = "docsViewerReport__cellLink";
        link.href = row.href;
        link.textContent = row.title;
        title.appendChild(link);
        tr.appendChild(title);
        body.appendChild(tr);
      });
      table.hidden = rows.length === 0;
      status.textContent = rows.length ? `${rows.length} ${rows.length === 1 ? "document" : "documents"}` : "No unpublishable documents.";
    } catch (error) {
      if (current(version)) status.textContent = error.message;
    } finally {
      if (current(version)) refresh.disabled = false;
    }
  }
  refresh.addEventListener("click", load);
  return load().then(function () { return true; });
}
