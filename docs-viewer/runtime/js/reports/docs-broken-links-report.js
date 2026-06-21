const DEFAULT_SORT_KEY = "fromPage";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["fromPage", "link"]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function configuredScopes(context) {
  const scopes = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  return scopes.map((scope) => ({
    scopeId: cleanString(scope && (scope.scope_id || scope.scopeId)).toLowerCase(),
    title: cleanString(scope && scope.title) || cleanString(scope && (scope.scope_id || scope.scopeId)),
    viewerBaseUrl: cleanString(scope && (scope.viewer_base_url || scope.viewerBaseUrl))
  })).filter((scope) => scope.scopeId);
}

function selectedScopeFromRoute(scopes, fallbackScope) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_scope")).toLowerCase();
  if (scopes.some((scope) => scope.scopeId === selected)) return selected;
  const fallback = cleanString(fallbackScope).toLowerCase();
  if (scopes.some((scope) => scope.scopeId === fallback)) return fallback;
  return scopes[0] ? scopes[0].scopeId : "";
}

function persistSelectedScope(scopeId) {
  const url = new URL(window.location.href);
  if (scopeId) {
    url.searchParams.set("report_scope", scopeId);
  } else {
    url.searchParams.delete("report_scope");
  }
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.runBrokenLinksAudit === "function"
    ? context.reportService
    : null;
}

function openSourceService(context) {
  const service = reportService(context);
  return service && typeof service.openSourceDoc === "function" ? service : null;
}

function reportActivityContext(scope) {
  return {
    page_id: "docs-broken-links",
    action_id: "run-broken-links-audit",
    route: "/docs/?scope=studio&doc=docs-broken-links",
    control_id: "docsBrokenLinksReportRun",
    control_selector: "#docsBrokenLinksReportRun",
    correlation_id: "broken-links:" + scope + ":" + Date.now(),
    scope
  };
}

function postBrokenLinks(context, scope, includeActivity) {
  const service = reportService(context);
  if (!service) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  return service.runBrokenLinksAudit({
    scope,
    activityContext: includeActivity ? reportActivityContext(scope) : null
  });
}

function viewerBaseMatches(pathname, scopes) {
  const normalized = cleanString(pathname).replace(/\/+$/, "") || "/";
  return scopes.some((scope) => {
    const base = cleanString(scope.viewerBaseUrl || "/docs/").replace(/\/+$/, "") || "/";
    return normalized === base;
  });
}

function manageModeHref(href, scopes) {
  const raw = cleanString(href);
  if (!raw || raw === "#") return raw || "#";
  try {
    const url = new URL(raw, window.location.href);
    if (viewerBaseMatches(url.pathname, scopes)) {
      url.searchParams.delete("mode");
      if (url.origin === window.location.origin) {
        return url.pathname + url.search + url.hash;
      }
      return url.toString();
    }
  } catch (_error) {
    return raw;
  }
  return raw;
}

function appendLinkCell(row, state, className, label, href) {
  const link = document.createElement("a");
  link.className = className;
  link.href = manageModeHref(href, state.scopes);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = cleanString(label) || cleanString(href) || "link";
  row.appendChild(link);
}

function appendSourceCell(row, state, entry) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = manageModeHref(entry.from_page_url, state.scopes);
  link.dataset.openSource = "vscode";
  link.dataset.scope = cleanString(entry.from_page_scope || state.selectedScope).toLowerCase();
  link.dataset.docId = cleanString(entry.from_page_doc_id);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = cleanString(entry.from_page_text) || cleanString(entry.from_page_source_path) || cleanString(entry.from_page_url) || "source";
  row.appendChild(link);
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
  indicator.textContent = state.sortKey === key ? (state.sortDir === "asc" ? "asc" : "desc") : "";
  button.appendChild(indicator);
  if (state.sortKey === key) button.dataset.state = "active";
  return button;
}

function renderScopeSelect(state) {
  clearNode(state.scopeSelectNode);
  state.scopes.forEach((scope) => {
    const option = document.createElement("option");
    option.value = scope.scopeId;
    option.textContent = scope.title || scope.scopeId;
    state.scopeSelectNode.appendChild(option);
  });
  state.scopeSelectNode.value = state.selectedScope;
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
    ? "1 broken link" + state.selectedScope + "]"
    : entries.length + " broken links";
  state.emptyNode.hidden = entries.length > 0;
  if (!entries.length) {
    state.emptyNode.textContent = "No broken links found in " + state.selectedScope;
    return;
  }
  entries.forEach((entry) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    appendSourceCell(row, state, entry);
    appendLinkCell(row, state, "docsViewerReport__cellLink", entry.link_text, entry.from_page_url);
    state.rowsNode.appendChild(row);
  });
}

function setBusy(state, busy) {
  state.isBusy = Boolean(busy);
  state.runButton.disabled = state.isBusy || !state.selectedScope;
  state.runButton.textContent = state.isBusy ? "Running..." : "Run audit";
}

function runAudit(state, includeActivity) {
  if (!state.selectedScope) return Promise.resolve();
  setBusy(state, true);
  state.statusNode.textContent = "Running broken-links audit...";
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  return postBrokenLinks(state.context, state.selectedScope, includeActivity)
    .then((payload) => {
      state.entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
      state.sortKey = DEFAULT_SORT_KEY;
      state.sortDir = DEFAULT_SORT_DIR;
      renderRows(state);
    })
    .catch((error) => {
      state.entries = [];
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
  state.scopeSelectNode.addEventListener("change", () => {
    state.selectedScope = cleanString(state.scopeSelectNode.value).toLowerCase();
    persistSelectedScope(state.selectedScope);
    runAudit(state, false);
  });
  state.runButton.addEventListener("click", () => {
    runAudit(state, true);
  });
  state.rowsNode.addEventListener("click", (event) => {
    const link = event.target instanceof Element ? event.target.closest("[data-open-source]") : null;
    if (!link) return;
    const service = openSourceService(state.context);
    const scope = cleanString(link.getAttribute("data-scope")).toLowerCase();
    const docId = cleanString(link.getAttribute("data-doc-id"));
    if (!service || !scope || !docId) return;
    event.preventDefault();
    service.openSourceDoc({
      scope,
      docId,
      editor: "vscode"
    }).then(() => {
      state.statusNode.textContent = "Opened source in VS Code.";
    }).catch((error) => {
      state.statusNode.textContent = error && error.message ? error.message : "Failed to open source in VS Code.";
    });
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

  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.textContent = "";

  const select = document.createElement("select");
  select.className = "docsViewerReport__select";
  label.appendChild(select);

  const runButton = document.createElement("button");
  runButton.id = "docsBrokenLinksReportRun";
  runButton.type = "button";
  runButton.className = "docsViewerReport__button";
  runButton.textContent = "Run audit";

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(label);
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
    scopeSelectNode: select,
    runButton,
    statusNode: status,
    headNode: head,
    rowsNode: rows,
    emptyNode: empty
  };
}

export function mountDocsBrokenLinksReport(context) {
  const scopes = configuredScopes(context);
  const selectedScope = selectedScopeFromRoute(
    scopes,
    cleanString(context.reportMeta && context.reportMeta.scope) || cleanString(context.viewerScope)
  );
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    scopes,
    selectedScope,
    entries: [],
    sortKey: DEFAULT_SORT_KEY,
    sortDir: DEFAULT_SORT_DIR,
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
  }, nodes);

  renderScopeSelect(state);
  renderHead(state);
  attachEvents(state);
  if (!selectedScope) {
    state.statusNode.textContent = "No docs scopes are configured.";
    setBusy(state, false);
    return Promise.resolve();
  }
  return runAudit(state, false);
}
