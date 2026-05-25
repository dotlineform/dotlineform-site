function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendTextCell(row, className, text) {
  const cell = document.createElement("span");
  cell.className = className;
  cell.textContent = text;
  row.appendChild(cell);
  return cell;
}

function appendHeaderCell(row, text) {
  appendTextCell(row, "docsViewerReport__headLabel", text);
}

function appendReportCell(row, report) {
  const cell = appendTextCell(row, "docsViewerReport__cellMeta docsViewerReport__reportName", "");
  const title = document.createElement("span");
  title.className = "docsViewerReport__title";
  title.textContent = cleanString(report.title) || cleanString(report.reportId);
  const id = document.createElement("span");
  id.className = "docsViewerReport__subtext";
  id.textContent = cleanString(report.reportId);
  cell.appendChild(title);
  cell.appendChild(id);
}

function presetLabel(report) {
  const presets = Array.isArray(report && report.presets) ? report.presets : [];
  if (!presets.length) return "";
  return presets.map((preset) => cleanString(preset.presetId)).filter(Boolean).join(", ");
}

export function mountReportsListReport(context) {
  const root = context.reportRoot;
  const reports = context.reportRegistry && Array.isArray(context.reportRegistry.reports)
    ? context.reportRegistry.reports.slice()
    : [];

  clearNode(root);
  root.dataset.reportColumns = "3";

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  status.textContent = reports.length === 1 ? "1 report" : `${reports.length} reports`;

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";

  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  appendHeaderCell(head, "report");
  appendHeaderCell(head, "access");
  appendHeaderCell(head, "presets");

  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";

  reports
    .sort((left, right) => cleanString(left.title || left.reportId).localeCompare(
      cleanString(right.title || right.reportId),
      undefined,
      { sensitivity: "base" }
    ))
    .forEach((report) => {
      const row = document.createElement("li");
      row.className = "docsViewerReport__row";
      row.dataset.reportDocId = cleanString(report.reportId);
      appendReportCell(row, report);
      appendTextCell(row, "docsViewerReport__cellMeta", cleanString(report.defaultAccess) || "public");
      appendTextCell(row, "docsViewerReport__cellMeta", presetLabel(report));
      rows.appendChild(row);
    });

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(status);
  root.appendChild(table);
  return Promise.resolve(true);
}
