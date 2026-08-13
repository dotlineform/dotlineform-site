function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function exactReportTarget(context) {
  const scope = cleanString(context && context.viewerScope).toLowerCase();
  const docId = cleanString(context && context.payload && context.payload.doc_id);
  if (!scope || !docId) {
    throw new Error("Documents Linking Here requires an exact report-host target.");
  }
  return { scope, docId };
}

function exactScopeConfig(context, scope) {
  const configs = Array.isArray(context && context.scopeConfigs)
    ? context.scopeConfigs
    : [];
  return configs.find(function (config) {
    return cleanString(config && config.scopeId).toLowerCase() === scope;
  }) || null;
}

function normalizeRows(payload, target) {
  if (
    !payload
    || payload.schema !== "docs_backlinks_v1"
    || cleanString(payload.scope).toLowerCase() !== target.scope
    || !payload.by_target
    || typeof payload.by_target !== "object"
    || Array.isArray(payload.by_target)
  ) {
    throw new Error("Documents Linking Here data is invalid.");
  }
  const rawRows = payload.by_target[target.docId];
  if (rawRows == null) return [];
  if (!Array.isArray(rawRows)) {
    throw new Error("Documents Linking Here rows are invalid.");
  }
  return rawRows.map(function (row) {
    const docId = cleanString(row && row.doc_id);
    const title = cleanString(row && row.title);
    const viewerUrl = cleanString(row && row.viewer_url);
    if (!docId || !title || !viewerUrl) {
      throw new Error("Documents Linking Here row is incomplete.");
    }
    return { docId, title, viewerUrl };
  });
}

function loadRows(context, target) {
  const config = exactScopeConfig(context, target.scope);
  const backlinksUrl = cleanString(config && config.backlinksUrl);
  if (!backlinksUrl) {
    return Promise.reject(new Error(
      "Documents Linking Here data is not configured for this scope."
    ));
  }
  return fetch(backlinksUrl, {
    headers: { Accept: "application/json" },
    cache: "no-store"
  }).then(function (response) {
    if (!response.ok) {
      throw new Error("Failed to load Documents Linking Here data.");
    }
    return response.json();
  }).then(function (payload) {
    return normalizeRows(payload, target);
  });
}

function renderRows(root, rows) {
  clearNode(root);
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  status.textContent = rows.length
    ? `${rows.length} ${rows.length === 1 ? "document links" : "documents link"} here`
    : "No documents link here.";
  root.appendChild(status);
  if (!rows.length) return;

  const list = document.createElement("ul");
  list.className = "docsViewerReport__rows";
  rows.forEach(function (row) {
    const item = document.createElement("li");
    item.className = "docsViewerReport__row";
    const link = document.createElement("a");
    link.className = "docsViewerReport__cellLink docsViewerReport__title";
    link.href = row.viewerUrl;
    link.textContent = row.title;
    item.appendChild(link);
    list.appendChild(item);
  });
  root.appendChild(list);
}

export function mountDocsBacklinksReport(context) {
  const root = context.reportRoot;
  const target = exactReportTarget(context);
  return loadRows(context, target).then(function (rows) {
    renderRows(root, rows);
    return true;
  });
}
