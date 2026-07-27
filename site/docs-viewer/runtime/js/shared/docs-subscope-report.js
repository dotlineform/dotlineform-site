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

function managementSettings(context) {
  var settings = context && context.subscopeManagement;
  return settings && typeof settings === "object" ? settings : null;
}

function managementDocs(settings) {
  if (!settings || !Array.isArray(settings.documents)) return null;
  return settings.documents.map(function (record) {
    return {
      docId: cleanString(record && record.doc_id),
      title: cleanString(record && record.title),
      uiStatus: cleanString(record && record.ui_status),
      viewable: !record || record.viewable !== false
    };
  }).filter(function (record) {
    return record.docId;
  });
}

function statusRecord(settings, statusValue) {
  var statuses = settings && settings.uiStatusByValue;
  if (!statusValue || !(statuses instanceof Map)) return null;
  return statuses.get(statusValue) || null;
}

function reportStateCallback(context) {
  return context && typeof context.onSubscopeStateChange === "function"
    ? context.onSubscopeStateChange
    : null;
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

  var accessibleParts = [titleText.textContent];
  var uiStatus = statusRecord(state.management, doc.uiStatus);
  if (uiStatus) {
    var statusIcon = document.createElement("span");
    statusIcon.className = "docsViewer__navStatus";
    statusIcon.setAttribute("aria-hidden", "true");
    statusIcon.textContent = cleanString(uiStatus.emoji);
    title.appendChild(statusIcon);
    accessibleParts.push(cleanString(uiStatus.label) || doc.uiStatus);
  }
  if (state.management && doc.viewable === false) {
    var nonViewableIcon = document.createElement("span");
    nonViewableIcon.className = "docsViewer__draftPrefix";
    nonViewableIcon.setAttribute("aria-hidden", "true");
    nonViewableIcon.textContent = cleanString(state.management.nonViewableEmoji) || "\uD83D\uDEAB";
    title.appendChild(nonViewableIcon);
    accessibleParts.push("non-viewable");
  }
  title.appendChild(titleText);
  if (state.management) {
    title.setAttribute("aria-label", accessibleParts.filter(Boolean).join(", "));
  }
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

function publishState(state, reportState, target, reason) {
  if (!state.onStateChange) return;
  state.onStateChange({
    state: cleanString(reportState),
    reason: cleanString(reason),
    target: target || null
  });
}

function invalidateDetailRequest(state) {
  state.detailRequestVersion += 1;
  return state.detailRequestVersion;
}

function renderListView(state) {
  invalidateDetailRequest(state);
  state.root.dataset.reportState = "list";
  state.tableNode.hidden = false;
  state.statusNode.hidden = false;
  if (state.detailNode) state.detailNode.hidden = true;
  renderRows(state, state.docs);
  publishState(state, "list", null, "list-view");
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
  var payloadDocId = cleanString(payload && payload.doc_id);
  if (payloadDocId !== docId) {
    throw new Error("Docs sub-scope detail payload did not match the requested document.");
  }
  state.detailPayloads[docId] = payload;
  state.detailNode.dataset.reportSubdocId = docId;
  state.detailNode.dataset.reportSubdocTitle = detailTitle(payload, docId);
  state.detailNode.dataset.reportSubdocUpdated = cleanString(payload && payload.last_updated);
  state.detailTitleNode.textContent = detailTitle(payload, docId);
  state.detailBodyNode.innerHTML = payload && payload.content_html ? payload.content_html : "";
  publishState(state, "detail", {
    scope: state.viewerScope,
    sub_scope: state.subScopeId,
    doc_id: docId
  }, "detail-loaded");
}

function renderDetailById(state, docId) {
  var requestVersion = invalidateDetailRequest(state);
  publishState(state, "loading", null, "detail-navigation");
  state.root.dataset.reportState = "detail";
  state.tableNode.hidden = true;
  state.statusNode.hidden = true;
  renderDetailShell(state, docId);

  var url = byIdPayloadUrl(state, docId);
  if (!url) {
    publishState(state, "error", null, "missing-detail-path");
    renderError(state.root, "Docs sub-scope by-id payload path is not configured: " + state.subScopeId);
    return Promise.resolve(true);
  }

  return fetchJson(url, "Failed to load docs sub-scope detail payload")
    .then(function (payload) {
      if (requestVersion !== state.detailRequestVersion) return true;
      renderDetailPayload(state, docId, payload);
      return true;
    })
    .catch(function (error) {
      if (requestVersion !== state.detailRequestVersion) return true;
      publishState(state, "error", null, "detail-load-failed");
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
  var onStateChange = reportStateCallback(context);
  if (!root) return Promise.resolve(false);
  if (!subScopeIdValue) {
    if (onStateChange) onStateChange({ state: "error", reason: "missing-sub-scope", target: null });
    renderError(root, "This report is missing viewer_report_subscope.");
    return Promise.resolve(true);
  }

  var subScope = findSubScope(context, subScopeIdValue);
  if (!subScope) {
    if (onStateChange) onStateChange({ state: "error", reason: "unconfigured-sub-scope", target: null });
    renderError(root, "Docs sub-scope is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var management = managementSettings(context);
  var managedDocs = managementDocs(management);
  var url = managedDocs ? "" : manifestUrl(subScope);
  if (managedDocs === null && !url) {
    if (onStateChange) onStateChange({ state: "error", reason: "missing-manifest", target: null });
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
    detailRequestVersion: 0,
    detailPayloads: {},
    management: management,
    onStateChange: onStateChange,
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode,
    viewerScope: cleanId(context && context.viewerScope)
  };

  if (management && cleanString(management.error)) {
    publishState(state, "error", null, "management-inventory-failed");
    renderError(root, cleanString(management.error));
    return Promise.resolve(true);
  }

  var parent = root.parentNode;
  var windowRef = root.ownerDocument && root.ownerDocument.defaultView;
  if (onStateChange && parent && windowRef && typeof windowRef.MutationObserver === "function") {
    state.unmountObserver = new windowRef.MutationObserver(function () {
      if (root.parentNode === parent) return;
      state.unmountObserver.disconnect();
      state.unmountObserver = null;
      invalidateDetailRequest(state);
      publishState(state, "unmounted", null, "report-unmount");
    });
    state.unmountObserver.observe(parent, { childList: true });
  }

  publishState(state, "loading", null, "report-loading");
  var docsRequest = managedDocs
    ? Promise.resolve(managedDocs)
    : fetchJson(url, "Failed to load docs sub-scope manifest").then(manifestDocs);
  return docsRequest
    .then(function (documents) {
      state.docs = documents;
      state.docIds = state.docs.map(function (doc) { return doc.docId; });
      var selectedDetailId = currentSubdocId();
      if (selectedDetailId) {
        if (state.docIds.indexOf(selectedDetailId) === -1) {
          publishState(state, "invalid", null, "unlisted-detail");
          renderError(root, "Docs sub-scope detail is not listed: " + selectedDetailId);
          return true;
        }
        return renderDetailById(state, selectedDetailId);
      }
      renderListView(state);
      return true;
    })
    .catch(function (error) {
      publishState(state, "error", null, "report-load-failed");
      renderError(root, error && error.message ? error.message : "Failed to render docs sub-scope report.");
      return true;
    });
}
