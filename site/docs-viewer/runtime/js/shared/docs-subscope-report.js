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

function manifestDocs(payload) {
  if (!payload || typeof payload !== "object") return [];
  if (Array.isArray(payload.docs)) {
    return payload.docs.map(function (record) {
      return {
        docId: cleanString(record && record.doc_id),
        title: cleanString(record && record.title)
      };
    }).filter(function (record) {
      return record.docId;
    });
  }
  return normalizeDocIds(payload.doc_ids).map(function (docId) {
    return { docId: docId, title: "" };
  });
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

function currentSubdocId() {
  if (typeof window === "undefined" || !window.location) return "";
  return cleanString(new URLSearchParams(window.location.search).get("subdoc"));
}

function byIdPayloadUrl(state, docId) {
  if (!state.byIdUrlBase) return "";
  return state.byIdUrlBase + "/" + encodeURIComponent(docId) + ".json";
}

function writeSubdocUrl(state, docId, mode) {
  if (typeof window === "undefined" || !window.history || !window.location) return;
  var url = new URL(window.location.href);
  if (state.parentDocId) url.searchParams.set("doc", state.parentDocId);
  if (docId) {
    url.searchParams.set("subdoc", docId);
  } else {
    url.searchParams.delete("subdoc");
  }
  var nextState = Object.assign({}, window.history.state || {}, {
    docId: state.parentDocId || url.searchParams.get("doc") || "",
    hash: url.hash ? url.hash.slice(1) : "",
    reportParams: docId ? { subdoc: docId } : {}
  });
  if (mode === "replace") {
    window.history.replaceState(nextState, "", url.pathname + url.search + url.hash);
    return;
  }
  window.history.pushState(nextState, "", url.pathname + url.search + url.hash);
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

function appendDocRow(state, doc) {
  var docId = doc.docId;
  var row = document.createElement("li");
  row.className = "docsViewerReport__row";
  row.dataset.reportSubdocId = docId;

  var title = document.createElement("button");
  title.className = "docsViewerReport__cellLink docsViewerReport__subscopeButton";
  title.type = "button";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title || humanize(docId) || docId;

  title.appendChild(titleText);
  title.addEventListener("click", function () {
    writeSubdocUrl(state, docId, "push");
    renderDetailById(state, docId);
  });
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

  return { statusNode: status, tableNode: table, rowsNode: rows };
}

function renderRows(state, docs) {
  clearNode(state.rowsNode);
  renderStatus(state, docs.length);
  if (!docs.length) {
    var empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = "No documents in this sub-scope.";
    state.rowsNode.appendChild(empty);
    return;
  }
  docs.forEach(function (doc) {
    appendDocRow(state, doc);
  });
}

function renderListView(state) {
  state.root.dataset.reportState = "list";
  state.tableNode.hidden = false;
  state.statusNode.hidden = false;
  if (state.detailNode) state.detailNode.hidden = true;
  renderRows(state, state.docs);
}

function detailTitle(payload, fallback) {
  return cleanString(payload && payload.title) || humanize(fallback) || fallback;
}

function renderDetailShell(state, docId) {
  if (state.detailNode) state.detailNode.remove();

  var titleId = "docs-report-detail-title-" + cleanId(state.subScopeId || "subscope");
  var section = document.createElement("section");
  section.className = "docsReportDetail";
  section.setAttribute("aria-labelledby", titleId);

  var header = document.createElement("div");
  header.className = "docsReportDetail__header";

  var back = document.createElement("button");
  back.className = "docsViewerReport__button docsReportDetail__back";
  back.type = "button";
  back.textContent = "Back to all " + subScopeTitle(state.subScope, state.subScopeId).toLowerCase();
  back.addEventListener("click", function () {
    writeSubdocUrl(state, "", "push");
    renderListView(state);
  });

  var title = document.createElement("p");
  title.className = "docsReportDetail__title";
  title.id = titleId;
  title.textContent = "Loading " + (humanize(docId) || docId) + "...";

  var body = document.createElement("article");
  body.className = "docsReportDetail__body docsViewer__content content";

  header.appendChild(back);
  header.appendChild(title);
  section.appendChild(header);
  section.appendChild(body);
  state.root.appendChild(section);
  state.detailNode = section;
  state.detailTitleNode = title;
  state.detailBodyNode = body;
}

function renderDetailPayload(state, docId, payload) {
  state.detailPayloads[docId] = payload;
  state.detailNode.dataset.reportSubdocId = docId;
  state.detailNode.dataset.reportSubdocTitle = detailTitle(payload, docId);
  state.detailNode.dataset.reportSubdocUpdated = cleanString(payload && payload.last_updated);
  state.detailTitleNode.textContent = detailTitle(payload, docId);
  state.detailBodyNode.innerHTML = payload && payload.content_html ? payload.content_html : "";
}

function renderDetailById(state, docId) {
  state.root.dataset.reportState = "detail";
  state.tableNode.hidden = true;
  state.statusNode.hidden = true;
  renderDetailShell(state, docId);

  var url = byIdPayloadUrl(state, docId);
  if (!url) {
    renderError(state.root, "Docs sub-scope by-id payload path is not configured: " + state.subScopeId);
    return Promise.resolve(true);
  }

  return fetchJson(url, "Failed to load docs sub-scope detail payload")
    .then(function (payload) {
      renderDetailPayload(state, docId, payload);
      return true;
    })
    .catch(function (error) {
      renderError(state.root, error && error.message ? error.message : "Failed to render docs sub-scope detail.");
      return true;
    });
}

function renderError(root, message) {
  clearNode(root);
  root.dataset.reportState = "error";
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
    root: root,
    parentDocId: cleanString(context && context.doc && context.doc.doc_id),
    subScope: subScope,
    subScopeId: subScopeIdValue,
    byIdUrlBase: byIdUrlBase(subScope),
    docs: [],
    docIds: [],
    detailPayloads: {},
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode
  };

  return fetchJson(url, "Failed to load docs sub-scope manifest")
    .then(function (payload) {
      state.docs = manifestDocs(payload);
      state.docIds = state.docs.map(function (doc) { return doc.docId; });
      var selectedDetailId = currentSubdocId();
      if (selectedDetailId) {
        if (state.docIds.indexOf(selectedDetailId) === -1) {
          renderError(root, "Docs sub-scope detail is not listed: " + selectedDetailId);
          return true;
        }
        return renderDetailById(state, selectedDetailId);
      }
      renderListView(state);
      return true;
    })
    .catch(function (error) {
      renderError(root, error && error.message ? error.message : "Failed to render docs sub-scope report.");
      return true;
    });
}
