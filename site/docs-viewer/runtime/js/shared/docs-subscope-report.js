import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";

/**
 * Optional caller-owned composition for one shared sub-scope report.
 *
 * Render callbacks receive detached hosts that enter the document only when
 * populated. `notify` receives explicit collection-scoped mount, state,
 * refresh, and unmount events.
 *
 * @typedef {Object} DocsSubscopeReportContribution
 * @property {function(Object): void} [notify]
 * @property {function(Object): (Object|void)} [renderRow]
 * @property {function(Object): void} [renderListToolbar]
 * @property {function(Object): void} [renderDetailToolbar]
 */

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
    return normalizeDocuments(payload.docs);
  }
  return normalizeDocIds(payload.doc_ids).map(function (docId) {
    return normalizeDocument({ doc_id: docId, title: "" });
  });
}

function normalizeDocument(record) {
  var docId = cleanString(record && record.doc_id);
  var title = cleanString(record && record.title);
  return {
    docId: docId,
    title: title,
    record: Object.assign({}, record || {}, {
      doc_id: docId,
      title: title
    })
  };
}

function normalizeDocuments(records) {
  return (Array.isArray(records) ? records : []).map(normalizeDocument).filter(function (record) {
    return record.docId;
  });
}

function suppliedDocumentSource(context) {
  var source = context && context.subscopeDocumentSource;
  if (!source || typeof source !== "object" || !Array.isArray(source.documents)) return null;
  return {
    documents: normalizeDocuments(source.documents),
    error: cleanString(source.error),
    refresh: typeof source.refresh === "function" ? source.refresh : null
  };
}

function reportContribution(context) {
  var contribution = context && context.subscopeReportContribution;
  return contribution && typeof contribution === "object" ? contribution : null;
}

function contributionCallback(contribution, name) {
  return contribution && typeof contribution[name] === "function"
    ? contribution[name]
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

function collectionTarget(scope, subScope) {
  return {
    scope: cleanId(scope),
    sub_scope: cleanId(subScope)
  };
}

function detailTarget(state, docId) {
  return {
    scope: state.viewerScope,
    sub_scope: state.subScopeId,
    doc_id: cleanString(docId)
  };
}

function documentRecord(doc) {
  return Object.assign({}, doc && doc.record || {});
}

function contributionEvent(context, subScopeIdValue, detail) {
  var contribution = reportContribution(context);
  var notify = contributionCallback(contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    collection: collectionTarget(context && context.viewerScope, subScopeIdValue)
  }, detail || {}));
}

function notifyContribution(state, detail) {
  var notify = contributionCallback(state.contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    collection: collectionTarget(state.viewerScope, state.subScopeId)
  }, detail || {}));
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

  var leadingHost = document.createElement("span");
  leadingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--leading";
  leadingHost.dataset.reportContributionHost = "row-leading";

  var title = document.createElement("button");
  title.className = "docsViewerReport__cellLink docsViewerReport__subscopeButton";
  title.type = "button";

  var titlePrefixHost = document.createElement("span");
  titlePrefixHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--titlePrefix";
  titlePrefixHost.dataset.reportContributionHost = "title-prefix";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title || humanize(docId) || docId;

  var renderRow = contributionCallback(state.contribution, "renderRow");
  var rowResult = renderRow ? renderRow({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    document: documentRecord(doc),
    leadingHost: leadingHost,
    titlePrefixHost: titlePrefixHost
  }) : null;
  if (titlePrefixHost.childNodes.length) title.appendChild(titlePrefixHost);
  title.appendChild(titleText);
  var accessibleLabels = rowResult && Array.isArray(rowResult.accessibleLabels)
    ? rowResult.accessibleLabels.map(cleanString).filter(Boolean)
    : [];
  if (accessibleLabels.length) {
    title.setAttribute("aria-label", [titleText.textContent].concat(accessibleLabels).join(", "));
  }
  title.addEventListener("click", function () {
    writeSubdocUrl(state, docId, "push");
    renderDetailById(state, docId);
  });
  if (leadingHost.childNodes.length) row.appendChild(leadingHost);
  row.appendChild(title);
  state.rowsNode.appendChild(row);
  return {
    hasLeadingContent: leadingHost.childNodes.length > 0,
    leadingHost: leadingHost,
    row: row
  };
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

  return {
    headNode: head,
    rowsNode: rows,
    statusNode: status,
    tableNode: table
  };
}

function renderListToolbar(state) {
  if (state.listToolbarNode) {
    state.listToolbarNode.remove();
    state.listToolbarNode = null;
  }
  var renderToolbar = contributionCallback(state.contribution, "renderListToolbar");
  if (!renderToolbar) return;
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--list";
  host.dataset.reportContributionHost = "list-toolbar";
  renderToolbar({
    collection: collectionTarget(state.viewerScope, state.subScopeId),
    documents: state.docs.map(documentRecord),
    host: host
  });
  if (!host.childNodes.length) return;
  state.root.insertBefore(host, state.tableNode);
  state.listToolbarNode = host;
}

function renderRows(state, docs) {
  clearNode(state.rowsNode);
  state.root.removeAttribute("data-report-leading-column");
  var priorHeadCell = state.headNode.querySelector("[data-report-contribution-head]");
  if (priorHeadCell) priorHeadCell.remove();
  renderStatus(state, docs.length);
  if (!docs.length) {
    var empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = "No documents in this sub-scope.";
    state.rowsNode.appendChild(empty);
    return;
  }
  var rows = docs.map(function (doc) {
    return appendDocRow(state, doc);
  });
  if (!rows.some(function (record) { return record.hasLeadingContent; })) return;
  state.root.dataset.reportLeadingColumn = "true";
  var headCell = document.createElement("span");
  headCell.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--head";
  headCell.dataset.reportContributionHead = "true";
  headCell.setAttribute("aria-hidden", "true");
  state.headNode.insertBefore(headCell, state.headNode.firstChild);
  rows.forEach(function (record) {
    if (!record.leadingHost.parentNode) {
      record.row.insertBefore(record.leadingHost, record.row.firstChild);
    }
  });
}

function publishState(state, reportState, target, reason) {
  notifyContribution(state, {
    type: "state",
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
  state.validDetailId = "";
  state.root.dataset.reportState = "list";
  state.tableNode.hidden = false;
  state.statusNode.hidden = false;
  if (state.detailNode) state.detailNode.hidden = true;
  renderListToolbar(state);
  if (state.listToolbarNode) state.listToolbarNode.hidden = false;
  renderRows(state, state.docs);
  publishState(state, "list", null, "list-view");
}

function detailTitle(payload, fallback) {
  return cleanString(payload && payload.title) || humanize(fallback) || fallback;
}

function renderDetailShell(state, docId) {
  if (state.detailNode) state.detailNode.remove();
  state.validDetailId = "";

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
  state.detailHeaderNode = header;
  state.detailTitleNode = title;
  state.detailBodyNode = body;
}

function renderDetailToolbar(state, docId) {
  var renderToolbar = contributionCallback(state.contribution, "renderDetailToolbar");
  if (!renderToolbar || !state.detailHeaderNode || !state.detailTitleNode) return;
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--detail";
  host.dataset.reportContributionHost = "detail-toolbar";
  var doc = state.docs.find(function (record) { return record.docId === docId; });
  renderToolbar({
    commitDeletedDocument: function (target) {
      return reconcileCommittedDeletion(state, target);
    },
    document: documentRecord(doc),
    host: host,
    target: detailTarget(state, docId)
  });
  if (host.childNodes.length) {
    state.detailHeaderNode.insertBefore(host, state.detailTitleNode);
  }
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
  state.validDetailId = docId;
  renderDetailToolbar(state, docId);
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
  if (state.listToolbarNode) state.listToolbarNode.hidden = true;
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

function assertCollectionTarget(state, target) {
  var targetScope = cleanId(target && target.scope);
  var targetSubScope = cleanId(target && target.sub_scope);
  var targetDocId = cleanString(target && target.doc_id);
  if (
    !targetDocId
    || targetScope !== state.viewerScope
    || targetSubScope !== state.subScopeId
  ) {
    throw new Error("Deleted sub-scope document target did not match the mounted collection.");
  }
  return targetDocId;
}

function focusFirstListRow(state) {
  var first = state.rowsNode && state.rowsNode.querySelector(".docsViewerReport__subscopeButton");
  if (!first || typeof first.focus !== "function") return;
  try {
    first.focus({ preventScroll: true });
  } catch (_error) {
    first.focus();
  }
}

function publishDocumentsRefresh(state, reason) {
  notifyContribution(state, {
    type: "refresh",
    documents: state.docs.map(documentRecord),
    reason: cleanString(reason)
  });
}

function returnFromDeletedDetail(state, docId) {
  if (state.validDetailId === docId) {
    if (state.detailNode) state.detailNode.remove();
    state.detailNode = null;
    state.detailHeaderNode = null;
    state.detailTitleNode = null;
    state.detailBodyNode = null;
    writeSubdocUrl(state, "", "replace");
    renderListView(state);
    focusFirstListRow(state);
    return;
  }
  if (state.root.dataset.reportState === "list") {
    renderListView(state);
  }
}

function refreshedDocuments(payload) {
  if (Array.isArray(payload)) return normalizeDocuments(payload);
  if (payload && typeof payload === "object" && Array.isArray(payload.documents)) {
    return normalizeDocuments(payload.documents);
  }
  throw new Error("Managed sub-scope inventory refresh returned an invalid document collection.");
}

function recoverCommittedDeletion(state, docId) {
  if (typeof state.documentSourceRefresh !== "function") {
    return Promise.reject(new Error(
      "Document was deleted, but the report inventory could not be reconciled."
    ));
  }
  return Promise.resolve(state.documentSourceRefresh()).then(function (payload) {
    if (!state.mounted) {
      return { reconciled: false, mode: "unmounted" };
    }
    var documents = refreshedDocuments(payload);
    if (documents.some(function (doc) { return doc.docId === docId; })) {
      throw new Error("Document was deleted, but the refreshed report inventory still lists it.");
    }
    state.docs = documents;
    state.docIds = documents.map(function (doc) { return doc.docId; });
    delete state.detailPayloads[docId];
    publishDocumentsRefresh(state, "document-deleted-recovery");
    returnFromDeletedDetail(state, docId);
    return { reconciled: true, mode: "refetch" };
  });
}

function reconcileCommittedDeletion(state, target) {
  var docId = assertCollectionTarget(state, target);
  if (!state.mounted) {
    return Promise.resolve({ reconciled: false, mode: "unmounted" });
  }
  if (!Array.isArray(state.docs)) {
    return recoverCommittedDeletion(state, docId);
  }
  var matchingIndexes = [];
  state.docs.forEach(function (doc, index) {
    if (doc.docId === docId) matchingIndexes.push(index);
  });
  if (matchingIndexes.length !== 1) {
    return recoverCommittedDeletion(state, docId);
  }
  state.docs = state.docs.filter(function (_doc, index) {
    return index !== matchingIndexes[0];
  });
  state.docIds = state.docs.map(function (doc) { return doc.docId; });
  delete state.detailPayloads[docId];
  publishDocumentsRefresh(state, "document-deleted-local");
  returnFromDeletedDetail(state, docId);
  return Promise.resolve({ reconciled: true, mode: "local" });
}

/**
 * Mounts the public-safe sub-scope reader with an optional document source and
 * optional caller-owned contribution. The report retains collection identity,
 * membership, navigation, and detail validation.
 *
 * @param {Object} context
 * @returns {Promise<boolean>}
 */
export function mountDocsSubscopeReport(context) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var subScopeIdValue = cleanId(reportMeta.subScope);
  if (!root) return Promise.resolve(false);
  if (!subScopeIdValue) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "missing-sub-scope",
      target: null
    });
    renderError(root, "This report is missing viewer_report_subscope.");
    return Promise.resolve(true);
  }

  var subScope = findSubScope(context, subScopeIdValue);
  if (!subScope) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "unconfigured-sub-scope",
      target: null
    });
    renderError(root, "Docs sub-scope is not configured: " + subScopeIdValue);
    return Promise.resolve(true);
  }

  var documentSource = suppliedDocumentSource(context);
  var url = documentSource ? "" : manifestUrl(subScope);
  if (!documentSource && !url) {
    contributionEvent(context, subScopeIdValue, {
      type: "state",
      state: "error",
      reason: "missing-manifest",
      target: null
    });
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
    documentSourceRefresh: documentSource && documentSource.refresh,
    contribution: reportContribution(context),
    headNode: refs.headNode,
    listToolbarNode: null,
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode,
    validDetailId: "",
    viewerScope: cleanId(context && context.viewerScope),
    mounted: true
  };

  var parent = root.parentNode;
  var windowRef = root.ownerDocument && root.ownerDocument.defaultView;
  if (state.contribution && parent && windowRef && typeof windowRef.MutationObserver === "function") {
    state.unmountObserver = new windowRef.MutationObserver(function () {
      if (root.parentNode === parent) return;
      state.unmountObserver.disconnect();
      state.unmountObserver = null;
      state.mounted = false;
      invalidateDetailRequest(state);
      publishState(state, "unmounted", null, "report-unmount");
      notifyContribution(state, {
        type: "unmount",
        reason: "report-unmount"
      });
    });
    state.unmountObserver.observe(parent, { childList: true });
  }

  notifyContribution(state, {
    type: "mount",
    root: root
  });
  if (documentSource && documentSource.error) {
    publishState(state, "error", null, "document-source-failed");
    renderError(root, documentSource.error);
    return Promise.resolve(true);
  }

  publishState(state, "loading", null, "report-loading");
  var docsRequest = documentSource
    ? Promise.resolve(documentSource.documents)
    : fetchJson(url, "Failed to load docs sub-scope manifest").then(manifestDocs);
  return docsRequest
    .then(function (documents) {
      state.docs = documents;
      state.docIds = state.docs.map(function (doc) { return doc.docId; });
      notifyContribution(state, {
        type: "refresh",
        documents: state.docs.map(documentRecord),
        reason: "documents-loaded"
      });
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
