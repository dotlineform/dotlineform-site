import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanId(value) {
  return cleanString(value).toLowerCase();
}

function humanize(value) {
  var text = cleanString(value).replace(/[-_]+/g, " ").replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function fetchJson(url, failureMessage) {
  return fetch(appendAssetVersion(url), {
    headers: { Accept: "application/json" },
    cache: "default"
  }).then(function (response) {
    if (!response.ok) throw new Error(failureMessage + " (" + response.status + ")");
    return response.json();
  });
}

function normalizeDocIds(value) {
  return cleanString(value)
    .split(",")
    .map(cleanString)
    .filter(Boolean);
}

function manifestDocIds(payload) {
  if (!payload || typeof payload !== "object") return [];
  return normalizeDocIds(payload.doc_ids);
}

function subScopesFromRoute(context) {
  var routeContext = context && context.routeContext ? context.routeContext : {};
  return Array.isArray(routeContext.subScopes) ? routeContext.subScopes : [];
}

function subScopesFromConfigs(context) {
  var viewerScope = cleanId(context && context.viewerScope);
  var configs = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  var scopeConfig = configs.find(function (config) {
    return cleanId(config && (config.scope_id || config.scopeId)) === viewerScope;
  });
  return scopeConfig && Array.isArray(scopeConfig.subScopes) ? scopeConfig.subScopes : [];
}

function subScopeId(record) {
  return cleanId(record && (record.subScope || record.sub_scope));
}

function findSubScope(context, subScopeIdValue) {
  var target = cleanId(subScopeIdValue);
  if (!target) return null;
  var candidates = subScopesFromRoute(context).concat(subScopesFromConfigs(context));
  return candidates.find(function (record) {
    return subScopeId(record) === target;
  }) || null;
}

function subScopeTitle(record, fallback) {
  return cleanString(record && record.title) || humanize(fallback);
}

function manifestUrl(record) {
  return cleanString(record && (record.manifestUrl || record.manifest_url));
}

function byIdUrlBase(record) {
  return cleanString(record && (record.byIdUrlBase || record.by_id_url_base)).replace(/\/+$/, "");
}

function renderStatus(state, count) {
  var scopeTitle = subScopeTitle(state.subScope, state.subScopeId);
  state.statusNode.textContent = count === 1 ? "1 " + scopeTitle + " document" : count + " " + scopeTitle + " documents";
}

function appendHeaderCell(row, text) {
  var cell = document.createElement("span");
  cell.className = "docsViewerReport__headLabel";
  cell.textContent = text;
  row.appendChild(cell);
}

function appendDocRow(state, docId) {
  var row = document.createElement("li");
  row.className = "docsViewerReport__row";
  row.dataset.reportSubdocId = docId;

  var title = document.createElement("span");
  title.className = "docsViewerReport__cellMeta";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = humanize(docId) || docId;

  var idText = document.createElement("span");
  idText.className = "docsViewerReport__subtext";
  idText.textContent = docId;

  title.appendChild(titleText);
  title.appendChild(idText);
  row.appendChild(title);
  state.rowsNode.appendChild(row);
}

function renderShell(context, subScope) {
  var root = context.reportRoot;
  clearNode(root);
  root.dataset.reportColumns = "1";
  root.dataset.reportSubscope = subScopeId(subScope);

  var status = document.createElement("p");
  status.className = "docsViewerReport__status";

  var table = document.createElement("div");
  table.className = "docsViewerReport__table";

  var head = document.createElement("div");
  head.className = "docsViewerReport__head";
  appendHeaderCell(head, subScopeTitle(subScope, subScopeId(subScope)));

  var rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(status);
  root.appendChild(table);

  return { statusNode: status, rowsNode: rows };
}

function renderRows(state, docIds) {
  clearNode(state.rowsNode);
  renderStatus(state, docIds.length);
  if (!docIds.length) {
    var empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = "No documents in this sub-scope.";
    state.rowsNode.appendChild(empty);
    return;
  }
  docIds.forEach(function (docId) {
    appendDocRow(state, docId);
  });
}

function renderError(root, message) {
  clearNode(root);
  var note = document.createElement("p");
  note.className = "docsViewerReport__status is-error";
  note.textContent = message;
  root.appendChild(note);
}

export function mountDocsSubscopeReport(context) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var subScopeIdValue = cleanId(reportMeta.subScope);
  if (!root) return Promise.resolve(false);
  if (!subScopeIdValue) {
    renderError(root, "This report is missing viewer_report_subscope.");
    return Promise.resolve(true);
  }

  var subScope = findSubScope(context, subScopeIdValue);
  if (!subScope) {
    renderError(root, "Docs sub-scope is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var url = manifestUrl(subScope);
  if (!url) {
    renderError(root, "Docs sub-scope manifest is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var refs = renderShell(context, subScope);
  refs.statusNode.textContent = "Loading " + subScopeTitle(subScope, subScopeIdValue) + "...";
  var state = {
    subScope: subScope,
    subScopeId: subScopeIdValue,
    byIdUrlBase: byIdUrlBase(subScope),
    statusNode: refs.statusNode,
    rowsNode: refs.rowsNode
  };

  return fetchJson(url, "Failed to load docs sub-scope manifest")
    .then(function (payload) {
      renderRows(state, manifestDocIds(payload));
      return true;
    })
    .catch(function (error) {
      renderError(root, error && error.message ? error.message : "Failed to render docs sub-scope report.");
      return true;
    });
}
