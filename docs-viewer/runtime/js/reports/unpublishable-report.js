const TITLE_ORDER = new Intl.Collator("en", { sensitivity: "base", numeric: true });

/** Validate the report envelope and order documents by title for display. */
export function readUnpublishableDocuments(payload) {
  if (!payload || payload.ok !== true || payload.schema_version !== "docs_unpublishable_report_v4"
    || payload.stage !== "working" || !Array.isArray(payload.documents)) {
    throw new Error("Unpublishable report data is invalid.");
  }
  const seen = new Set();
  return payload.documents.map(function (record) {
    const docId = record && record.doc_id;
    if (typeof docId !== "string" || !docId || docId !== docId.trim() || seen.has(docId)) {
      throw new Error("Unpublishable document identity is invalid.");
    }
    seen.add(docId);
    if (record.title !== null && typeof record.title !== "string") {
      throw new Error("Unpublishable document title is invalid.");
    }
    return { doc_id: docId, title: record.title };
  }).sort(function (left, right) {
    return Number(!left.title) - Number(!right.title)
      || TITLE_ORDER.compare(left.title || "", right.title || "")
      || left.doc_id.localeCompare(right.doc_id);
  });
}

/** Mount a read-only source report within the workspace's Working document. */
export function mountUnpublishableReport(context) {
  if (context.viewerStage !== "working") {
    throw new Error("Unpublishable is available only in Working.");
  }
  const service = context.reportService;
  if (!service || typeof service.readUnpublishable !== "function" || typeof service.openPublicationIgnore !== "function") {
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
  const open = documentRef.createElement("button");
  open.type = "button";
  open.className = "docsViewerReport__button";
  open.textContent = "Open in VS Code";
  toolbar.appendChild(open);
  const status = documentRef.createElement("p");
  status.className = "docsViewerReport__status";
  status.setAttribute("aria-live", "polite");
  const table = documentRef.createElement("table");
  const head = documentRef.createElement("thead");
  const headings = documentRef.createElement("tr");
  ["Title", "Document ID"].forEach(function (label) {
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
  let busy = false;

  function setBusy(value) {
    busy = value;
    refresh.disabled = value;
    open.disabled = value;
  }

  function current(version) {
    return version === requestVersion && root.isConnected !== false
      && (typeof context.isCurrentDocument !== "function" || context.isCurrentDocument());
  }

  async function load() {
    if (busy) return;
    const version = ++requestVersion;
    setBusy(true);
    body.replaceChildren();
    table.hidden = true;
    status.textContent = "Reading unpublishable.json…";
    try {
      const payload = await service.readUnpublishable({ stage: context.viewerStage });
      if (!current(version)) return;
      const documents = readUnpublishableDocuments(payload);
      documents.forEach(function (record) {
        const tr = documentRef.createElement("tr");
        const href = "/docs/?" + new URLSearchParams({ stage: "working", doc: record.doc_id });
        [record.title, record.doc_id].forEach(function (value) {
          const cell = documentRef.createElement("td");
          if (value) {
            const link = documentRef.createElement("a");
            link.className = "docsViewerReport__cellLink";
            link.href = href;
            link.textContent = value;
            cell.appendChild(link);
          } else {
            cell.textContent = "—";
          }
          tr.appendChild(cell);
        });
        body.appendChild(tr);
      });
      table.hidden = documents.length === 0;
      status.textContent = documents.length ? `${documents.length} ${documents.length === 1 ? "document" : "documents"}` : "The ignore list is empty.";
    } catch (error) {
      if (current(version)) status.textContent = error.message;
    } finally {
      if (current(version)) setBusy(false);
    }
  }
  refresh.addEventListener("click", load);
  open.addEventListener("click", async function () {
    if (busy) return;
    const version = ++requestVersion;
    setBusy(true);
    try {
      await service.openPublicationIgnore({ stage: context.viewerStage });
      if (current(version)) status.textContent = "Opened unpublishable.json in VS Code. Refresh after saving.";
    } catch (error) {
      if (current(version)) status.textContent = error.message;
    } finally {
      if (current(version)) setBusy(false);
    }
  });
  return load().then(function () { return true; });
}
