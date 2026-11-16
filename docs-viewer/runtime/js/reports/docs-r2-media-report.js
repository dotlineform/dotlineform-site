import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

export function mountDocsR2MediaReport(context) {
  const root = context.reportRoot;
  const document = root.ownerDocument;
  const service = context.reportService;
  root.innerHTML = [
    '<div class="docsViewerReport__toolbar">',
    '  <div class="docsViewerReport__refreshGroup">',
    '    <button class="docsViewer__toolbarIconButton" type="button" data-r2-refresh aria-label="Refresh R2 orphan report" title="Refresh R2 orphan report"></button>',
    '    <select class="docsViewer__fieldInput" data-r2-collection aria-label="Filter by collection"></select>',
    '  </div>',
    '</div>',
    '<p class="docsViewerReport__status" role="status"></p>',
    '<div class="docsViewerReport__table" hidden>',
    '  <div class="docsViewerReport__head"><span>Collection</span><span>R2 key</span><span>Owner</span><span>Finding</span></div>',
    '  <ul class="docsViewerReport__rows"></ul>',
    '</div>'
  ].join("");
  const refresh = root.querySelector("[data-r2-refresh]");
  const collection = root.querySelector("[data-r2-collection]");
  const status = root.querySelector(".docsViewerReport__status");
  const table = root.querySelector(".docsViewerReport__table");
  const rows = root.querySelector(".docsViewerReport__rows");
  if (context.reportViewSwitch) refresh.before(context.reportViewSwitch);
  refresh.append(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  let report = null;
  let filter = "*";
  let busy = false;
  let message = "";

  function populateFilter() {
    const append = (id, title) => {
      const option = document.createElement("option");
      option.value = id;
      option.textContent = title;
      collection.append(option);
    };
    collection.replaceChildren();
    append("*", "All collections");
    for (const [id, title] of Object.entries(report?.collections ?? {})) append(id, title);
    if (report && filter !== "*" && !Object.hasOwn(report.collections, filter)) filter = "*";
    collection.value = filter;
  }

  function addRow(finding) {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    const cell = (value, tag = "span") => {
      const node = document.createElement(tag);
      node.textContent = value;
      row.append(node);
      return node;
    };
    cell(report.collections[finding.collection]);
    cell(finding.key, "code");
    if (finding.owner_title !== null) {
      const link = cell(finding.owner_title, "a");
      link.className = "docsViewerReport__cellLink";
      link.href = context.viewerUrlForDocument(finding.doc_id, { collection: finding.collection });
      link.dataset.docsViewerCollection = finding.collection;
      link.dataset.docsViewerDocId = finding.doc_id;
    } else {
      cell(finding.doc_id);
    }
    cell(finding.owner_title === null ? "Owner missing in Working" : "No saved reference");
    rows.append(row);
  }

  function render() {
    refresh.disabled = busy;
    refresh.setAttribute("aria-busy", String(busy));
    collection.disabled = !report;
    rows.replaceChildren();
    const findings = (report?.findings ?? []).filter((finding) => filter === "*" || finding.collection === filter);
    table.hidden = !findings.length;
    for (const finding of findings) addRow(finding);
    const details = report
      ? `Last refreshed ${new Date(report.refreshed_at).toLocaleString("en-GB")} · Deployed commit ${report.deployed_commit.slice(0, 12)}`
      : "No saved R2 orphan report. Use Refresh to run it.";
    const summary = report
      ? `${findings.length} ${findings.length === 1 ? "finding" : "findings"} · ${report.scanned} objects checked across all collections.`
      : "";
    status.textContent = [message, details, summary].filter(Boolean).join("\n");
  }

  async function load(run) {
    if (busy) return;
    busy = true;
    message = run ? "Refreshing R2 orphan report…" : "";
    render();
    try {
      const result = await (run ? service.refreshR2MediaReport() : service.readR2MediaReport());
      report = result.report;
      populateFilter();
      message = "";
    } catch (error) {
      message = (error.message || "The report request failed.") + (report ? " Showing the previous report." : "");
    } finally {
      busy = false;
      render();
    }
  }

  refresh.addEventListener("click", () => load(true));
  collection.addEventListener("change", () => {
    filter = collection.value;
    render();
  });
  context.registerRetainedView?.({
    id: "docs-r2-media",
    capture: () => filter,
    restore: (saved) => {
      filter = saved;
      populateFilter();
      render();
    }
  });
  populateFilter();
  return load(false);
}
