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

/** Partition audit sources by the owning report, independently of destination URLs. */
function reportService(context) {
  return context && context.reportService && typeof context.reportService.runBrokenLinksAudit === "function"
    ? context.reportService
    : null;
}

function postBrokenLinks(state) {
  const service = reportService(state.context);
  if (!service) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  return service.runBrokenLinksAudit({
    ...(state.reportContext.stage ? { stage: state.reportContext.stage } : {}),
    report_context: state.reportContext
  });
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
  const entries = state.entries.slice().sort((left, right) => compareEntries(state, left, right));
  state.statusNode.textContent = entries.length === 1
    ? "1 broken link"
    : entries.length + " broken links";
  if (state.unavailableSources.length) {
    state.statusNode.textContent += "; " + state.unavailableSources.length + " documents not scanned";
  }
  state.emptyNode.hidden = entries.length > 0 || state.unavailableSources.length > 0;
  if (!entries.length && !state.unavailableSources.length) {
    state.emptyNode.textContent = "No broken links found in " + state.stage;
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
  state.runButton.disabled = state.isBusy || !state.stage;
  state.runButton.classList.toggle("docsViewerReport__runText", state.isBusy);
  state.runButton.setAttribute("aria-busy", String(state.isBusy));
  state.runButton.setAttribute("aria-label", state.isBusy ? "Running audit" : "Run audit");
  state.runButton.title = state.isBusy ? "Running audit" : "Run audit";
  if (state.isBusy) state.runButton.textContent = "Running...";
  else state.runButton.replaceChildren(createDocsViewerToolbarIcon(state.runButton.ownerDocument, "docsViewer__icon--refresh-cw"));
}

function runAudit(state) {
  if (!state.stage || state.isBusy) return Promise.resolve();
  setBusy(state, true);
  state.statusNode.textContent = "Running broken-links audit...";
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  return postBrokenLinks(state)
    .then((payload) => {
      if (cleanString(payload.stage) !== cleanString(state.reportContext.stage)) {
        throw new Error("Broken Links response does not match the selected source context.");
      }
      state.entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
      state.unavailableSources = Array.isArray(payload && payload.unavailable_sources) ? payload.unavailable_sources : [];
      state.sortKey = DEFAULT_SORT_KEY;
      state.sortDir = DEFAULT_SORT_DIR;
      renderRows(state);
    })
    .catch((error) => {
      state.entries = [];
      state.unavailableSources = [];
      state.statusNode.textContent = error && error.message ? error.message : "Failed to run broken-links audit.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The audit could not run in this viewer context.";
      clearNode(state.rowsNode);
      renderHead(state);
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    runAudit(state);
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
  runButton.setAttribute("aria-label", "Run audit");
  runButton.title = "Run audit";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(runButton);
  toolbar.appendChild(status);

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
  root.appendChild(table);
  root.appendChild(empty);

  return {
    runButton,
    statusNode: status,
    headNode: head,
    rowsNode: rows,
    emptyNode: empty
  };
}

export function mountDocsBrokenLinksReport(context) {
  const stage = cleanString(context.viewerStage);
  if (stage !== "working") throw new Error("Broken Links is available in Working.");
  const reportContext = { stage };
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    stage,
    reportContext,
    entries: [],
    unavailableSources: [],
    sortKey: DEFAULT_SORT_KEY,
    sortDir: DEFAULT_SORT_DIR,
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
  }, nodes);

  renderHead(state);
  attachEvents(state);
  return runAudit(state);
}
