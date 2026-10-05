import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
const DEFAULT_SORT_KEY = "fromPage";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["fromPage", "link"]);
function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function reportService(context) {
  const service = context && context.reportService;
  return service && typeof service.readBrokenLinks === "function" && typeof service.runBrokenLinksAudit === "function"
    ? service
    : null;
}

function appendLinkCell(row, _state, className, label, href) {
  const link = document.createElement("a");
  link.className = className;
  link.href = cleanString(href) || "#";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = cleanString(label) || cleanString(href) || "link";
  row.appendChild(link);
}

function appendSourceCell(row, entry) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = entry.from_page_url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = cleanString(entry.from_page_text) || cleanString(entry.from_page_url);
  row.appendChild(link);
}

function appendIssueCell(row, state, entry) {
  const label = entry.issue_type === "semantic_token"
    ? cleanString(entry.raw) + " — " + cleanString(entry.reason).replace(/_/g, " ")
    : cleanString(entry.link_text || entry.link_url);
  if (cleanString(entry.link_url)) {
    appendLinkCell(row, state, "docsViewerReport__cellLink", label, entry.link_url);
    return;
  }
  const text = document.createElement("span");
  text.className = "docsViewerReport__cellText";
  text.textContent = label;
  row.appendChild(text);
}

function sortValue(entry, sortKey) {
  if (sortKey === "link") return cleanString(entry.link_text || entry.link_url);
  return cleanString(entry.from_page_text || entry.from_page_url);
}

function compareEntries(state, left, right) {
  const direction = state.sortDir === "desc" ? -1 : 1;
  const selected = state.collator.compare(sortValue(left, state.sortKey), sortValue(right, state.sortKey));
  if (selected !== 0) return selected * direction;
  for (const key of SORT_KEYS) {
    if (key === state.sortKey) continue;
    const fallback = state.collator.compare(sortValue(left, key), sortValue(right, key));
    if (fallback !== 0) return fallback;
  }
  return 0;
}

function sortButton(state, key, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "docsViewerReport__sortButton";
  button.dataset.reportSort = key;
  button.textContent = label;
  const indicator = document.createElement("span");
  indicator.className = "docsViewerReport__sortIndicator";
  indicator.setAttribute("aria-hidden", "true");
  indicator.textContent = state.sortKey === key ? (state.sortDir === "asc" ? "▲" : "▼") : "";
  button.appendChild(indicator);
  if (state.sortKey === key) button.dataset.state = "active";
  return button;
}

function renderHead(state) {
  clearNode(state.headNode);
  state.headNode.appendChild(sortButton(state, "fromPage", "from page"));
  state.headNode.appendChild(sortButton(state, "link", "link"));
}

function renderRows(state) {
  clearNode(state.rowsNode);
  renderHead(state);
  state.messageNode.textContent = state.resultMessage;
  state.messageNode.hidden = !state.resultMessage;
  state.statusNode.hidden = !state.report;
  if (!state.report) {
    state.statusNode.textContent = "";
    state.emptyNode.hidden = true;
    return;
  }
  const entries = state.entries.slice().sort((left, right) => compareEntries(state, left, right));
  const scannedAt = new Date(state.report.scanned_at).toLocaleString("en-GB", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false
  });
  state.statusNode.textContent = "Last scanned: " + scannedAt;
  state.emptyNode.hidden = entries.length > 0 || state.unavailableSources.length > 0;
  if (!entries.length && !state.unavailableSources.length) {
    state.emptyNode.textContent = "No broken links found.";
    return;
  }
  entries.forEach((entry) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    appendSourceCell(row, entry);
    appendIssueCell(row, state, entry);
    state.rowsNode.appendChild(row);
  });
  state.unavailableSources.forEach((entry) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    appendSourceCell(row, entry);
    const explanation = document.createElement("span");
    explanation.className = "docsViewerReport__cellText";
    explanation.textContent = "Generated document unavailable; links not scanned.";
    row.appendChild(explanation);
    state.rowsNode.appendChild(row);
  });
}

function setBusy(state, busy) {
  state.isBusy = Boolean(busy);
  state.runButton.disabled = state.isBusy;
  state.runButton.setAttribute("aria-busy", String(state.isBusy));
  state.context.reportRoot.setAttribute("aria-busy", String(state.isBusy));
  state.headNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.isBusy;
  });
}

function loadReport(state, refresh = false) {
  if (state.isBusy) return Promise.resolve();
  const service = reportService(state.context);
  if (!service) {
    state.resultMessage = "Local docs-management server is not configured.";
    renderRows(state);
    return Promise.resolve();
  }
  state.resultMessage = "";
  renderRows(state);
  setBusy(state, true);
  return (refresh ? service.runBrokenLinksAudit() : service.readBrokenLinks())
    .then((payload) => {
      if (!payload || !Object.prototype.hasOwnProperty.call(payload, "report")) {
        throw new Error("Broken Links returned no saved report.");
      }
      const report = payload.report;
      if (report !== null && (
        report.schema_version !== "docs_broken_links_report_v1"
        || !Array.isArray(report.entries) || !Array.isArray(report.unavailable_sources)
        || !Number.isFinite(Date.parse(report.scanned_at))
      )) {
        throw new Error("Saved Broken Links report is invalid.");
      }
      if (refresh && !report) throw new Error("Broken Links refresh returned no saved report.");
      state.report = report;
      state.entries = report ? report.entries : [];
      state.unavailableSources = report ? report.unavailable_sources : [];
      renderRows(state);
    })
    .catch((error) => {
      const message = error && error.message ? error.message : "Broken Links could not complete the request.";
      state.resultMessage = message + (state.report ? " Showing the saved report." : "");
      renderRows(state);
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    loadReport(state, true);
  });
  state.headNode.addEventListener("click", (event) => {
    const button = event.target instanceof Element ? event.target.closest("[data-report-sort]") : null;
    if (!button) return;
    const key = cleanString(button.getAttribute("data-report-sort"));
    if (!SORT_KEYS.includes(key)) return;
    if (state.sortKey === key) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    renderRows(state);
  });
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "docs_broken_links";
  root.dataset.reportColumns = "2";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";

  const runButton = document.createElement("button");
  runButton.id = "docsBrokenLinksReportRun";
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Refresh");
  runButton.title = "Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));

  const status = document.createElement("span");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(runButton);
  toolbar.appendChild(status);

  const message = document.createElement("p");
  message.className = "docsViewerReport__status";
  message.hidden = true;

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";

  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "group");
  head.setAttribute("aria-label", "Sort broken-link rows");

  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";

  const empty = document.createElement("p");
  empty.className = "docsViewerReport__empty";
  empty.hidden = true;

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(toolbar);
  root.appendChild(message);
  root.appendChild(table);
  root.appendChild(empty);

  return {
    runButton,
    statusNode: status,
    messageNode: message,
    headNode: head,
    rowsNode: rows,
    emptyNode: empty
  };
}

export function mountDocsBrokenLinksReport(context) {
  if (!context.managementContext) throw new Error("Broken Links requires local management.");
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    report: null,
    resultMessage: "",
    entries: [],
    unavailableSources: [],
    sortKey: DEFAULT_SORT_KEY,
    sortDir: DEFAULT_SORT_DIR,
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
  }, nodes);
  if (context.registerRetainedView) context.registerRetainedView({
    id: "broken-links",
    capture: function () { return { key: state.sortKey, direction: state.sortDir }; },
    restore: function (saved) {
      if (state.sortKey === saved.key && state.sortDir === saved.direction) return;
      state.sortKey = saved.key; state.sortDir = saved.direction;
      renderHead(state); renderRows(state);
    }
  });

  renderHead(state);
  attachEvents(state);
  return loadReport(state);
}
