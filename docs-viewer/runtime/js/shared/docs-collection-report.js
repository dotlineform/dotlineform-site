import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";
import { createDocsCollectionReportState } from "./docs-collection-report-state.js";
import {
  appendAssetVersion,
  requestUrl
} from "./docs-viewer-asset-url.js";
import {
  normalizeDocsCollectionFilterValue,
  projectDocsCollectionDocuments
} from "./docs-collection-report-filter.js";
import {
  COLLECTION_PAGE_SIZE,
  COLLECTION_SEARCH_DELAY_MS,
  appendCollectionThumbnail,
  createCollectionBrowsingData,
  createCollectionPager,
  loadCatalogueCollectionThumbnailSettings
} from "./docs-collection-browsing.js";

/**
 * Optional caller-owned composition for one shared collection report.
 *
 * Render callbacks receive detached hosts that enter the document only when
 * populated. `notify` receives explicit collection-scoped mount, state,
 * complete-manifest refresh, visible-row projection, and unmount events.
 * Committed records update the retained list in memory. Document navigation
 * and detail actions belong to the shared reader.
 *
 * @typedef {Object} DocsCollectionReportContribution
 * @property {function(Object): void} [notify]
 * @property {function(Object): (Object|void)} [renderRow]
 * @property {function(Object): void} [renderListToolbar]
 * @property {function(): *} [captureListState] Optional JSON-safe list restoration state.
 * @property {function(*): void} [restoreListState] Restore a previously captured caller state.
 */

var filterIdSequence = 0;

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

function fetchJson(url, failureMessage, options) {
  var settings = options || {};
  return fetch(appendAssetVersion(url), {
    headers: { Accept: "application/json" },
    cache: settings.cache || "no-cache"
  }).then(function (response) {
    if (!response.ok) throw new Error(failureMessage + " (" + response.status + ")");
    return response.json();
  });
}

function manifestDocs(payload) {
  if (!payload || Object.keys(payload).length !== 1 || !Array.isArray(payload.docs)) {
    throw new Error("Docs collection manifest requires a docs array.");
  }
  return normalizeDocuments(payload.docs);
}

function normalizeDocument(record) {
  var docId = cleanString(record && record.doc_id);
  var title = cleanString(record && record.title);
  if (record && Object.hasOwn(record, "has_thumbnail") && typeof record.has_thumbnail !== "boolean") {
    throw new Error("Document thumbnail presence must be a boolean.");
  }
  var normalizedRecord = Object.assign({}, record || {}, {
    doc_id: docId,
    title: title
  });
  return {
    docId: docId,
    title: title,
    record: Object.freeze(normalizedRecord)
  };
}

function normalizeDocuments(records) {
  return records.map(function (record) {
    if (!record || typeof record.doc_id !== "string" || !record.doc_id.trim()) {
      throw new Error("Docs collection manifest row requires a document ID.");
    }
    return normalizeDocument(record);
  });
}

function resolveReportContribution(context) {
  var hasSuppliedContribution = context && Object.prototype.hasOwnProperty.call(
    context,
    "collectionReportContributionPromise"
  );
  var contribution = hasSuppliedContribution
    ? context.collectionReportContributionPromise
    : context && context.collectionReportContribution;
  return Promise.resolve(contribution).then(function (resolved) {
    if (resolved == null) return null;
    if (typeof resolved !== "object" || Array.isArray(resolved)) {
      throw new Error("Docs collection report contribution is invalid.");
    }
    return resolved;
  });
}

function contributionCallback(contribution, name) {
  return contribution && typeof contribution[name] === "function"
    ? contribution[name]
    : null;
}

function collectionsFromRoute(context) {
  var routeContext = context && context.routeContext ? context.routeContext : {};
  return Array.isArray(routeContext.collections) ? routeContext.collections : [];
}

function collectionsFromConfigs(context) {
  var workspaceConfig = context && context.workspaceConfig;
  return workspaceConfig && Array.isArray(workspaceConfig.collections) ? workspaceConfig.collections : [];
}

function collectionId(record) {
  return cleanId(record && record.collection);
}

function findCollection(context, collectionIdValue) {
  var target = cleanId(collectionIdValue);
  if (!target) return null;
  var candidates = collectionsFromRoute(context).concat(collectionsFromConfigs(context));
  return candidates.find(function (record) {
    return collectionId(record) === target;
  }) || null;
}

function collectionTitle(record, fallback) {
  return cleanString(record && record.title) || humanize(fallback);
}

function collectionItemsLabel(collection) {
  return collectionId(collection) === "works" ? "documents" : collectionTitle(collection, collectionId(collection));
}

function manifestUrl(record) {
  return cleanString(record && (record.manifestUrl || record.manifest_url));
}

function collectionTarget(collection) {
  return {
    collection: cleanId(collection)
  };
}

function documentRecord(doc) {
  return doc && doc.record ? doc.record : Object.freeze({});
}

function contributionEvent(context, collectionIdValue, detail) {
  var contribution = context && context.resolvedCollectionReportContribution;
  var notify = contributionCallback(contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: context && context.managementContext ? "manage" : "public",
    collection: collectionTarget(collectionIdValue)
  }, detail || {}));
}

function notifyContribution(state, detail) {
  var notify = contributionCallback(state.contribution, "notify");
  if (!notify) return;
  notify(Object.assign({
    access: state.managementContext ? "manage" : "public",
    collection: collectionTarget(state.collectionId)
  }, detail || {}));
}

function appendDocRow(state, doc, reserveThumbnailSpace) {
  var docId = doc.docId;
  var row = document.createElement("li");
  row.className = "docsViewerReport__row";
  row.dataset.reportSubdocId = docId;

  var leadingHost = document.createElement("span");
  leadingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--leading";
  leadingHost.dataset.reportContributionHost = "row-leading";

  var title = document.createElement("a");
  title.className = "docsViewerReport__cellLink docsViewerReport__collectionButton";
  title.href = state.collectionProvider.documentHref({ collection: state.collectionId, doc_id: docId });
  if (state.collectionId === "catalogue") state.browsingData.appendThumbnail(title, doc);
  else if (doc.record.has_thumbnail === true) {
    if (!state.mediaRoot || !/^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(docId)) {
      throw new Error("Document thumbnail requires configured media and an exact document identity.");
    }
    var thumbnailUrl = state.mediaRoot.replace(/\/+$/, "") + "/collections/" +
      encodeURIComponent(state.collectionId) + "/thumbs/" + encodeURIComponent(docId + "-thumb.webp");
    appendCollectionThumbnail(title, requestUrl(thumbnailUrl, { reloadNonce: state.thumbnailRevisions.get(docId) }));
  } else if (state.collectionId === "works" && state.browsingData.thumbnailForDocument(doc)) {
    state.browsingData.appendThumbnail(title, doc);
  } else if (reserveThumbnailSpace) {
    appendCollectionThumbnail(title);
  }

  var titlePrefixHost = document.createElement("span");
  titlePrefixHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--titlePrefix";
  titlePrefixHost.dataset.reportContributionHost = "title-prefix";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title || humanize(docId) || docId;

  var trailingHost = document.createElement("span");
  trailingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--trailing";
  trailingHost.dataset.reportContributionHost = "row-trailing";

  var renderRow = contributionCallback(state.contribution, "renderRow");
  var rowResult = renderRow ? renderRow({
    collection: collectionTarget(state.collectionId),
    document: documentRecord(doc),
    leadingHost: leadingHost,
    titlePrefixHost: titlePrefixHost,
    trailingHost: trailingHost
  }) : null;
  if (titlePrefixHost.childNodes.length) title.appendChild(titlePrefixHost);
  title.appendChild(titleText);
  var accessibleLabels = rowResult && Array.isArray(rowResult.accessibleLabels)
    ? rowResult.accessibleLabels.map(cleanString).filter(Boolean)
    : [];
  if (accessibleLabels.length) {
    title.setAttribute("aria-label", [titleText.textContent].concat(accessibleLabels).join(", "));
  }
  if (leadingHost.childNodes.length) row.appendChild(leadingHost);
  row.appendChild(title);
  if (trailingHost.childNodes.length) row.appendChild(trailingHost);
  state.rowsNode.appendChild(row);
  return {
    hasLeadingContent: leadingHost.childNodes.length > 0,
    leadingHost: leadingHost,
    row: row
  };
}

function renderFilterShell(context, collection) {
  var toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar docsViewerReport__collectionFilterToolbar";
  toolbar.dataset.docsCollectionFilters = "true";
  filterIdSequence += 1;
  var searchId = "docs-collection-title-filter-" + collectionId(collection) + "-" + filterIdSequence;
  var searchLabel = document.createElement("label");
  searchLabel.className = "docsViewerReport__selectLabel visually-hidden";
  searchLabel.htmlFor = searchId;
  searchLabel.textContent = "Filter " + collectionItemsLabel(collection)
    + (collectionId(collection) === "catalogue" ? " by title or Work ID" : " by title");

  var search = document.createElement("span");
  search.className = "docsViewerReport__search";
  var input = document.createElement("input");
  input.className = "docsViewerReport__searchInput";
  input.id = searchId;
  input.type = "search";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.placeholder = ({ catalogue: "work", concepts: "concept", moments: "moment", works: "title" })[collectionId(collection)] || "search";

  search.appendChild(input);
  var clear = mountSearchField(input).clearButton;

  toolbar.appendChild(searchLabel);
  toolbar.appendChild(search);
  return {
    clearNode: clear,
    inputNode: input,
    toolbarNode: toolbar
  };
}

function renderShell(context, collection) {
  var root = context.reportRoot;
  clearNode(root);
  root.dataset.reportColumns = "1";
  root.dataset.reportCollection = collectionId(collection);

  var filters = renderFilterShell(context, collection);
  var status = document.createElement("p");
  status.className = "docsViewerReport__status visually-hidden";
  status.setAttribute("aria-live", "polite");
  status.setAttribute("role", "status");
  status.hidden = Boolean(context.managementContext);

  var table = document.createElement("div");
  table.className = "docsViewerReport__table";

  var rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  rows.setAttribute("aria-label", collectionItemsLabel(collection));

  table.appendChild(rows);
  root.appendChild(filters.toolbarNode);
  root.appendChild(status);
  root.appendChild(table);

  if (collectionId(collection) === "catalogue") status.classList.remove("visually-hidden");
  var collectionSort = null;
  if (context.managementContext && ["catalogue", "works"].includes(collectionId(collection))) {
    collectionSort = document.createElement("button");
    collectionSort.type = "button";
    collectionSort.className = "docsViewer__toolbarIconButton docsViewerReport__collectionSortButton";
    filters.toolbarNode.appendChild(collectionSort);
  }

  return {
    collectionSortNode: collectionSort,
    filterClearNode: filters.clearNode,
    filterInputNode: filters.inputNode,
    filterToolbarNode: filters.toolbarNode,
    rowsNode: rows,
    statusNode: status,
    tableNode: table
  };
}

function updateFilterControls(state) {
  if (state.filterInputNode.value !== state.query) {
    state.filterInputNode.value = state.query;
  }
  state.filterClearNode.setAttribute(
    "aria-label",
    state.collectionId === "works" ? "Clear document search"
      : "Clear " + collectionItemsLabel(state.collection) + (state.pagedBrowsing ? " search" : " title filter")
  );
  state.filterClearNode.title = state.filterClearNode.getAttribute("aria-label");
}

function compareText(left, right) {
  var leftValue = cleanString(left).normalize("NFKC").toLowerCase();
  var rightValue = cleanString(right).normalize("NFKC").toLowerCase();
  if (leftValue < rightValue) return -1;
  if (leftValue > rightValue) return 1;
  var leftRaw = cleanString(left);
  var rightRaw = cleanString(right);
  if (leftRaw < rightRaw) return -1;
  if (leftRaw > rightRaw) return 1;
  return 0;
}

function compareTitleAscending(left, right) {
  return compareText(left.title, right.title) || compareText(left.docId, right.docId);
}

function lastUpdatedTimestamp(doc) {
  var value = cleanString(doc && doc.record && doc.record.last_updated);
  var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return NaN;
  var parts = match.slice(1).map(Number);
  var timestamp = Date.UTC(
    parts[0],
    parts[1] - 1,
    parts[2]
  );
  var date = new Date(timestamp);
  if (
    date.getUTCFullYear() !== parts[0]
    || date.getUTCMonth() !== parts[1] - 1
    || date.getUTCDate() !== parts[2]
  ) return NaN;
  return timestamp;
}

function compareLastUpdatedDescending(left, right) {
  var leftTimestamp = lastUpdatedTimestamp(left);
  var rightTimestamp = lastUpdatedTimestamp(right);
  var leftValid = Number.isFinite(leftTimestamp);
  var rightValid = Number.isFinite(rightTimestamp);
  if (leftValid && !rightValid) return -1;
  if (!leftValid && rightValid) return 1;
  if (leftValid && rightValid && leftTimestamp !== rightTimestamp) {
    return rightTimestamp - leftTimestamp;
  }
  return compareTitleAscending(left, right);
}

function visibleDocuments(state) {
  if (state.browsingData) {
    return state.browsingData.project(state.docs, state.query, state.sortMode);
  }
  return projectDocsCollectionDocuments(state.docs, { query: state.query })
    .sort(state.sortMode === "last-updated-desc"
      ? compareLastUpdatedDescending : compareTitleAscending);
}

function bindFilterControls(state) {
  state.filterInputNode.addEventListener("input", function () {
    state.query = state.filterInputNode.value;
    if (state.pagedBrowsing) {
      cancelCollectionSearch(state);
      state.listNeedsRender = true;
      if (!normalizeDocsCollectionFilterValue(state.query)) {
        state.pageIndex = 0;
        renderListProjectionContained(state, "collection-search-clear");
        return;
      }
      state.searchTimer = setTimeout(function () {
        state.searchTimer = null;
        if (!state.mounted || !state.root.isConnected) return;
        state.pageIndex = 0;
        if (state.root.dataset.reportState === "list") {
          renderListProjectionContained(state, "collection-search");
        }
      }, COLLECTION_SEARCH_DELAY_MS);
      updateCollectionControls(state);
      return;
    }
    renderListProjectionContained(state, "title-filter");
  });
}

function cancelCollectionSearch(state) {
  if (state.searchTimer !== null) {
    clearTimeout(state.searchTimer);
    state.searchTimer = null;
    state.pageIndex = 0;
  }
}

function updateCollectionControls(state) {
  if (!state.pagedBrowsing) return;
  var pending = state.searchTimer !== null || !state.browsingData;
  var button = state.collectionSortNode;
  if (button) {
    var recentMode = state.sortMode === "last-updated-desc";
    var currentLabel = {
      "title-asc": "title A–Z",
      "last-updated-desc": "recently updated"
    }[state.sortMode];
    button.disabled = pending;
    button.dataset.docsCollectionSort = state.sortMode;
    button.replaceChildren(createDocsViewerToolbarIcon(button.ownerDocument,
      recentMode ? "docsViewer__icon--clock-3" : "docsViewer__icon--arrow-down-a-z"));
    button.title = "Sorted by " + currentLabel + ". Switch to "
      + (recentMode ? "title A–Z." : "recently updated.");
    button.setAttribute("aria-label", button.title);
  }
  state.pager.update(state.matches.length, state.pageIndex, pending);
}

function listSortContext(state) {
  return {
    mode: state.sortMode,
    setMode: function (mode) {
      if (state.pagedBrowsing && (state.searchTimer !== null || !state.browsingData)) return state.sortMode;
      var nextMode = cleanString(mode);
      if (!["title-asc", "last-updated-desc"].includes(nextMode)) {
        throw new Error("Docs collection sort mode is invalid: " + nextMode);
      }
      state.sortMode = nextMode;
      state.pageIndex = 0;
      renderListProjectionContained(state, "sort-change");
      return nextMode;
    }
  };
}

function renderListToolbar(state, documents) {
  state.listActionHost.replaceChildren();
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
    actionContext: state.actionContext,
    collection: state.actionContext.collectionTarget,
    documents: Object.freeze(documents.map(documentRecord)),
    host: host,
    actionHost: state.listActionHost,
    refreshAndOpenDocument: function (target) {
      return state.openDocument(target);
    },
    refreshCollection: function (target) {
      return refreshCollection(state, target);
    },
    sort: state.pagedBrowsing ? null : listSortContext(state)
  });
  if (!host.childNodes.length) return;
  state.filterToolbarNode.appendChild(host);
  state.listToolbarNode = host;
}

function renderRows(state, docs) {
  clearNode(state.rowsNode);
  state.root.removeAttribute("data-report-leading-column");
  state.statusNode.textContent = "";
  state.statusNode.hidden = true;
  if (!docs.length) {
    var empty = document.createElement("li");
    empty.className = "docsViewerReport__empty";
    empty.textContent = state.docs.length
      ? "No " + collectionItemsLabel(state.collection).toLowerCase() + " match the current filters."
      : state.collectionId === "works" ? "No documents are available."
        : "No documents are available in " + collectionItemsLabel(state.collection) + ".";
    state.rowsNode.appendChild(empty);
    return;
  }
  var reserveThumbnailSpace = state.collectionId !== "catalogue" && state.docs.some(function (doc) {
    return doc.record.has_thumbnail === true
      || state.collectionId === "works" && Boolean(state.browsingData.thumbnailForDocument(doc));
  });
  var rows = docs.map(function (doc) {
    return appendDocRow(state, doc, reserveThumbnailSpace);
  });
  if (!rows.some(function (record) { return record.hasLeadingContent; })) return;
  state.root.dataset.reportLeadingColumn = "true";
  rows.forEach(function (record) {
    if (!record.leadingHost.parentNode) {
      record.row.insertBefore(record.leadingHost, record.row.firstChild);
    }
  });
}

function publishState(state, reportState, target, reason) {
  if (reportState === "error" || reportState === "unmounted") cancelCollectionSearch(state);
  var active = !["inactive", "unmounted"].includes(reportState);
  state.actionContext = Object.freeze({
    state: reportState, reason: reason,
    parentTarget: active ? state.parentTarget : null,
    collectionTarget: active ? state.collectionTarget : null,
    collectionLabel: collectionTitle(state.collection, state.collectionId),
    documentTarget: reportState === "list" ? state.parentTarget : null,
    documentRecord: reportState === "list" ? state.parentRecord : null,
    actionHost: reportState === "list" ? state.listActionHost : null,
    refreshDocument: state.openDocument,
    refreshCollection: function (target) { return refreshCollection(state, target); }
  });
  if (typeof state.onDocumentState === "function") state.onDocumentState(state.actionContext);
  notifyContribution(state, { type: "state", state: reportState, reason: reason });
}

function renderListProjection(state) {
  state.listNeedsRender = true;
  var documents = visibleDocuments(state);
  state.matches = documents;
  renderListPage(state);
  notifyContribution(state, {
    type: "projection",
    documents: Object.freeze(documents.map(documentRecord)),
    sort: state.sortMode,
    reason: "filters-projected"
  });
  state.listNeedsRender = false;
}

/** Page turns reuse the complete match list, including management selection eligibility. */
function renderListPage(state) {
  var documents = state.matches;
  if (state.pagedBrowsing) {
    state.pageIndex = Math.min(state.pageIndex, Math.max(0, Math.ceil(documents.length / COLLECTION_PAGE_SIZE) - 1));
  }
  updateFilterControls(state);
  renderListToolbar(state, documents);
  renderRows(state, state.pagedBrowsing
    ? documents.slice(state.pageIndex * COLLECTION_PAGE_SIZE, (state.pageIndex + 1) * COLLECTION_PAGE_SIZE)
    : documents);
  updateCollectionControls(state);
}

function renderListProjectionContained(state, reason) {
  try {
    renderListProjection(state);
    return true;
  } catch (error) {
    try {
      publishState(state, "error", null, cleanString(reason) || "contribution-failed");
    } catch (_notifyError) {
      // The contained report error below remains authoritative.
    }
    renderError(
      state.root,
      error && error.message
        ? error.message
        : "Failed to render docs collection report."
    );
    return false;
  }
}

function captureListControls(state) {
  var captureContribution = contributionCallback(state.contribution, "captureListState");
  return { query: state.query, sort: state.sortMode,
    page: state.searchTimer !== null ? 0 : state.pageIndex,
    contribution: captureContribution ? captureContribution.call(state.contribution) : null };
}

/** Restore controls against the current inventory, never a saved payload. */
function restoreListControls(state, saved) {
  if (JSON.stringify(captureListControls(state)) === JSON.stringify(saved)) return;
  cancelCollectionSearch(state);
  if (typeof saved.query === "string") state.query = saved.query;
  if (["title-asc", "last-updated-desc"].includes(saved.sort)) state.sortMode = saved.sort;
  state.pageIndex = Number.isInteger(saved.page) && saved.page >= 0 ? saved.page : 0;
  var restoreContribution = contributionCallback(state.contribution, "restoreListState");
  if (restoreContribution) restoreContribution.call(state.contribution, saved.contribution);
  state.listNeedsRender = true;
}

/** Reveal the retained list, rebuilding only when its document data changed. */
function renderListView(state) {
  state.root.dataset.reportState = "list";
  state.filterToolbarNode.hidden = false;
  state.tableNode.hidden = false;
  publishState(state, "list", null, "list-view");
  if (state.listNeedsRender && !renderListProjectionContained(state, "list-projection-failed")) return;
  if (state.listToolbarNode) state.listToolbarNode.hidden = false;
  if (state.pager) state.pager.root.hidden = state.matches.length === 0;
}

function renderError(root, message) {
  clearNode(root);
  root.dataset.reportState = "error";
  var note = document.createElement("p");
  note.className = "docsViewerReport__status is-error";
  note.textContent = message;
  root.appendChild(note);
}

function assertExactCollectionTarget(state, target) {
  var keys = Object.keys(target || {}).sort();
  var targetCollection = cleanId(target && target.collection);
  if (
    keys.length !== 1
    || keys[0] !== "collection"
    || targetCollection !== state.collectionId
  ) {
    throw new Error("Imported package target did not match the mounted collection.");
  }
  return collectionTarget(targetCollection);
}

function publishDocumentsRefresh(state, reason) {
  state.listNeedsRender = true;
  notifyContribution(state, {
    type: "refresh",
    documents: Object.freeze(state.docs.map(documentRecord)),
    reason: cleanString(reason)
  });
}

function applyManifest(state, documents) {
  cancelCollectionSearch(state);
  if (state.browsingData) state.browsingData.prepare(documents);
  state.docs = documents;
  state.listNeedsRender = true;
  state.docIds = state.docs.map(function (doc) { return doc.docId; });
}

/** An explicit import/regeneration refresh belongs to this list, never to Back. */
function refreshCollection(state, target) {
  var collection = assertExactCollectionTarget(state, target);
  return state.loadManifest().then(function () { renderListView(state); return collection; });
}

function mountResolvedDocsCollectionReport(context, contribution) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var collectionIdValue = cleanId(reportMeta.collection);
  if (!root) return Promise.resolve(false);
  if (!collectionIdValue) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "missing-collection",
      target: null
    });
    renderError(root, "This report is missing report collection.");
    return Promise.resolve(true);
  }

  var collection = findCollection(context, collectionIdValue);
  if (!collection) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "unconfigured-collection",
      target: null
    });
    renderError(root, "Docs collection is not configured: " + collectionIdValue);
    return Promise.resolve(true);
  }

  var url = manifestUrl(collection);
  if (!url) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "missing-manifest",
      target: null
    });
    renderError(root, "Docs collection manifest is not configured: " + collectionIdValue);
    return Promise.resolve(true);
  }

  var refs = renderShell(context, collection);
  if (!context.managementContext) {
    refs.statusNode.textContent = "Loading " + collectionItemsLabel(collection) + "...";
  }
  var state = {
    root: root,
    collectionProvider: context.collectionProvider,
    openDocument: context.openDocument,
    mountRelatedLinks: context.mountRelatedLinks,
    mediaRoot: context.mediaRoot,
    thumbnailRevisions: new Map(),
    viewerBaseUrl: context.viewerBaseUrl,
    onDocumentState: context.onCollectionDocumentState,
    parentDocId: cleanString(context && context.doc && context.doc.doc_id),
    parentTarget: Object.freeze({
      doc_id: cleanString(context.doc && context.doc.doc_id)
    }),
    parentRecord: context.doc,
    collectionTarget: Object.freeze(collectionTarget(collectionIdValue)),
    listActionHost: root.ownerDocument.createElement("div"),
    collection: collection,
    collectionId: collectionIdValue,
    manifestUrl: url,
    manifestLoaded: false,
    docs: [],
    docIds: [],
    query: "",
    sortMode: collectionIdValue === "catalogue" ? "last-updated-desc" : "title-asc",
    pagedBrowsing: ["catalogue", "works"].includes(collectionIdValue),
    browsingData: null,
    collectionSortNode: refs.collectionSortNode,
    matches: [],
    pageIndex: 0,
    searchTimer: null,
    pager: null,
    contribution: contribution,
    managementContext: Boolean(context && context.managementContext),
    filterClearNode: refs.filterClearNode,
    filterInputNode: refs.filterInputNode,
    filterToolbarNode: refs.filterToolbarNode,
    listToolbarNode: null,
    listNeedsRender: true,
    listReturnPosition: null,
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode,
    mounted: true
  };
  state.listActionHost.className = "docsViewer__collectionActions";
  if (state.pagedBrowsing) {
    state.filterInputNode.disabled = true;
    state.pager = createCollectionPager(root.ownerDocument,
      state.collectionId === "works" ? "document" : collectionItemsLabel(state.collection), function (pageIndex) {
      if (!state.mounted || state.searchTimer !== null || pageIndex < 0
        || pageIndex * COLLECTION_PAGE_SIZE >= state.matches.length) return;
      state.pageIndex = pageIndex;
      try {
        renderListPage(state);
      } catch (error) {
        publishState(state, "error", null, "collection-page-failed");
        renderError(root, error.message);
      }
    });
    root.appendChild(state.pager.root);
    if (state.collectionSortNode) {
      state.collectionSortNode.addEventListener("click", function () {
        listSortContext(state).setMode(state.sortMode === "last-updated-desc" ? "title-asc" : "last-updated-desc");
      });
    }
    updateCollectionControls(state);
  }
  bindFilterControls(state);
  updateFilterControls(state);

  var parent = root.parentNode;
  var windowRef = root.ownerDocument && root.ownerDocument.defaultView;
  var remembered = createDocsCollectionReportState({
    root: root, collectionId: state.collectionId, hostDocId: state.parentDocId,
    isReady: function () { return state.mounted && state.manifestLoaded && root.dataset.reportState === "list"; },
    captureControls: function () { return captureListControls(state); },
    restoreControls: function (saved) { restoreListControls(state, saved); }
  });
  function restoreRememberedList() {
    if (!state.manifestLoaded || !state.mounted) return;
    remembered.restore();
    renderListView(state);
    remembered.restorePosition();
  }
  function dispose() {
    if (!state.mounted) return;
    remembered.dispose();
    state.mounted = false;
    if (state.unmountObserver) { state.unmountObserver.disconnect(); state.unmountObserver = null; }
    if (state.unsubscribeChanges) { state.unsubscribeChanges(); state.unsubscribeChanges = null; }
    cancelCollectionSearch(state);
    publishState(state, "unmounted", null, "report-unmount");
    notifyContribution(state, { type: "unmount", reason: "report-unmount" });
  }
  if (parent && windowRef && typeof windowRef.MutationObserver === "function") {
    state.unmountObserver = new windowRef.MutationObserver(function () {
      if (root.parentNode === parent) return;
      dispose();
    });
    state.unmountObserver.observe(parent, { childList: true });
  }

  notifyContribution(state, {
    type: "mount",
    root: root
  });
  publishState(state, "loading", null, "report-loading");
  state.loadManifest = function () {
    return Promise.all([
      fetchJson(url, "Failed to load docs collection manifest").then(manifestDocs),
      state.pagedBrowsing ? loadCatalogueCollectionThumbnailSettings(context) : null
    ]).then(function (loaded) {
      if (!state.mounted || !root.isConnected) return false;
      if (state.pagedBrowsing) {
        state.browsingData = createCollectionBrowsingData({
          collectionId: state.collectionId,
          managementContext: state.managementContext,
          thumbnailSettings: loaded[1],
          updatedTimestamp: lastUpdatedTimestamp,
          workIdForDocument: context.catalogueWorkIdForDocument
        });
        state.filterInputNode.disabled = false;
      }
      applyManifest(state, loaded[0]);
      state.manifestLoaded = true;
      notifyContribution(state, {
        type: "refresh",
        documents: Object.freeze(state.docs.map(documentRecord)),
        reason: "documents-loaded"
      });
      return true;
    });
  };
  if (context.registerRetainedView) context.registerRetainedView({
    id: "collection:" + state.collectionId,
    dispose: dispose,
    capture: remembered.save,
    restore: restoreRememberedList,
    resume: restoreRememberedList
  });
  if (state.collectionProvider.subscribeDocumentChanges) {
    state.unsubscribeChanges = state.collectionProvider.subscribeDocumentChanges(function (change) {
      if (!state.mounted || change.target.collection !== state.collectionId) return;
      var docId = change.target.doc_id;
      if (change.deleted) state.thumbnailRevisions.delete(docId);
      else state.thumbnailRevisions.set(docId, String(Date.now()));
      state.docs = state.docs.filter(function (doc) { return doc.docId !== docId; });
      if (!change.deleted) state.docs.push(normalizeDocument(change.record));
      state.docIds = state.docs.map(function (doc) { return doc.docId; });
      if (state.browsingData) state.browsingData.prepare(state.docs);
      publishDocumentsRefresh(state, "document-committed");
      renderListProjectionContained(state, "document-committed");
    });
  }
  return state.loadManifest().then(function (loaded) {
      if (loaded) {
        // The document inventory must exist before restoring saved controls.
        root.dataset.reportState = "list";
        restoreRememberedList();
      }
      return true;
    })
    .catch(function (error) {
      try {
        publishState(state, "error", null, "report-load-failed");
      } catch (_notifyError) {
        // The contained report error below remains authoritative.
      }
      renderError(root, error && error.message ? error.message : "Failed to render docs collection report.");
      return true;
    });
}

export function mountDocsCollectionReport(context) {
  var root = context && context.reportRoot;
  if (!root) return Promise.resolve(false);
  return resolveReportContribution(context)
    .then(function (contribution) {
      return mountResolvedDocsCollectionReport(
        Object.assign({}, context, {
          resolvedCollectionReportContribution: contribution
        }),
        contribution
      );
    })
    .catch(function (error) {
      renderError(
        root,
        error && error.message
          ? error.message
          : "Failed to resolve docs collection controls."
      );
      if (typeof context.onCollectionDocumentState === "function") {
        context.onCollectionDocumentState({
          state: "error",
          parentTarget: {  doc_id: context.doc.doc_id },
          documentTarget: null
        });
      }
      return true;
    });
}
