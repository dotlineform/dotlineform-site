import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";
import { createDocsCollectionReportState } from "./docs-collection-report-state.js";
import { appendAssetVersion } from "./docs-viewer-asset-url.js";
import { normalizeDocsCollectionFilterValue } from "./docs-collection-report-filter.js";
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
 * complete-inventory IDs, filtered-result IDs, and unmount events.
 * Manage supplies its local list controller; public browsing has no edit or
 * selection bookkeeping. Document navigation belongs to the shared reader.
 *
 * @typedef {Object} DocsCollectionReportContribution
 * @property {function(Object): void} [notify]
 * @property {function(Object): (Object|void)} [renderRow]
 * @property {function(Object): void} [renderListToolbar]
 * @property {function(): *} [captureListState] Optional JSON-safe list restoration state.
 * @property {function(*): void} [restoreListState] Restore a previously captured caller state.
 * @property {function(Object): Object} createListManagement Manage-owned data, updates and refresh.
 * @property {boolean} [paginationDefault] Caller-owned initial pagination choice.
 * @property {function(Object): Object} [mountPaginationControl] Local control over shared pagination state.
 * @property {function(): void} [resetSelection] Clear selection when the pagination control changes mode.
 */

var filterIdSequence = 0;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function fetchJson(url, failureMessage) {
  return fetch(appendAssetVersion(url), {
    headers: { Accept: "application/json" },
    cache: "no-cache"
  }).then(function (response) {
    if (!response.ok) throw new Error(failureMessage + " (" + response.status + ")");
    return response.json();
  });
}

function contributionCallback(contribution, name) {
  return contribution && typeof contribution[name] === "function"
    ? contribution[name]
    : null;
}

function collectionId(record) {
  return record.collection;
}

function collectionTitle(record) {
  return record.title;
}

/** Select shared capabilities independently of the current page-display choice. */
function collectionBrowsingFeatures(collection) {
  var boundedBrowsing = ["catalogue", "works"].includes(collection.collection)
    || collection.collectionType === "book-collection";
  return { pagination: boundedBrowsing, delayedSearch: boundedBrowsing, filterToolbarSort: boundedBrowsing };
}

function collectionItemsLabel(collection) {
  return collectionId(collection) === "works" ? "documents" : collectionTitle(collection);
}

function collectionTarget(collection) {
  return {
    collection: collection
  };
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
  title.href = doc.href;
  if (reserveThumbnailSpace) appendCollectionThumbnail(title, doc.thumbnailSrc || undefined,
    state.pagedBrowsing ? "eager" : "lazy");

  var titlePrefixHost = document.createElement("span");
  titlePrefixHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--titlePrefix";
  titlePrefixHost.dataset.reportContributionHost = "title-prefix";

  var titleText = document.createElement("span");
  titleText.className = "docsViewerReport__title";
  titleText.textContent = doc.title;

  var trailingHost = document.createElement("span");
  trailingHost.className = "docsViewerReport__rowContribution docsViewerReport__rowContribution--trailing";
  trailingHost.dataset.reportContributionHost = "row-trailing";

  var renderRow = contributionCallback(state.contribution, "renderRow");
  var rowResult = renderRow ? renderRow({
    collection: collectionTarget(state.collectionId),
    document: doc.record,
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

function renderShell(context, collection, features) {
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
  if (context.managementContext && features.filterToolbarSort) {
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
      : "Clear " + collectionItemsLabel(state.collection) + (state.features.delayedSearch ? " search" : " title filter")
  );
  state.filterClearNode.title = state.filterClearNode.getAttribute("aria-label");
}

function visibleDocuments(state) {
  return state.browsingData.project(state.query, state.sortMode);
}

function bindFilterControls(state) {
  state.filterInputNode.addEventListener("input", function () {
    if (!state.mounted) return;
    state.query = state.filterInputNode.value;
    if (state.features.delayedSearch) {
      cancelCollectionSearch(state);
      state.listNeedsRender = true;
      if (!normalizeDocsCollectionFilterValue(state.query)) {
        state.pageIndex = 0;
        renderListProjectionContained(state, "collection-search-clear");
        return;
      }
      state.searchTimer = setTimeout(function () {
        state.searchTimer = null;
        if (!state.mounted) return;
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
  var pending = state.searchTimer !== null || !state.manifestLoaded;
  state.paginationControl?.update(state.pagedBrowsing);
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
  if (state.pager) {
    state.pager.update(state.matches.length, state.pageIndex, pending, state.pagedBrowsing);
  }
}

function listSortContext(state) {
  return {
    mode: state.sortMode,
    setMode: function (mode) {
      if (!state.mounted || state.features.delayedSearch && (state.searchTimer !== null || !state.manifestLoaded)) return state.sortMode;
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

function renderListToolbar(state) {
  var renderToolbar = contributionCallback(state.contribution, "renderListToolbar");
  if (!renderToolbar) return;
  state.listActionHost.replaceChildren();
  if (state.listToolbarNode) {
    state.listToolbarNode.remove();
    state.listToolbarNode = null;
  }
  var host = document.createElement("div");
  host.className = "docsViewerReport__contributionToolbar docsViewerReport__contributionToolbar--list";
  host.dataset.reportContributionHost = "list-toolbar";
  renderToolbar({
    actionContext: state.actionContext,
    collection: state.actionContext.collectionTarget,
    docIds: state.management.docIds,
    host: host,
    actionHost: state.listActionHost,
    refreshAndOpenDocument: function (target) {
      return state.openDocument(target);
    },
    refreshCollection: state.management.refreshCollection,
    sort: state.features.filterToolbarSort ? null : listSortContext(state)
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
    empty.textContent = state.browsingData.rows.length
      ? "No " + collectionItemsLabel(state.collection).toLowerCase() + " match the current filters."
      : state.collectionId === "works" ? "No documents are available."
        : "No documents are available in " + collectionItemsLabel(state.collection) + ".";
    state.rowsNode.appendChild(empty);
    return;
  }
  var reserveThumbnailSpace = state.browsingData.hasThumbnails;
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
    collectionLabel: collectionTitle(state.collection),
    documentTarget: reportState === "list" ? state.parentTarget : null,
    documentRecord: reportState === "list" ? state.parentRecord : null,
    actionHost: reportState === "list" ? state.listActionHost : null,
    refreshDocument: state.openDocument,
    ...(state.management ? { refreshCollection: state.management.refreshCollection } : {})
  });
  if (typeof state.onDocumentState === "function") state.onDocumentState(state.actionContext);
  notifyContribution(state, { type: "state", state: reportState, reason: reason });
}

function renderListProjection(state) {
  state.listNeedsRender = true;
  var documents = visibleDocuments(state);
  state.matches = documents;
  state.management?.prepareProjection(documents);
  renderListPage(state);
  state.listNeedsRender = false;
}

/** Page turns reuse the complete match list, including management selection eligibility. */
function renderListPage(state) {
  var documents = state.matches;
  if (state.pagedBrowsing) {
    state.pageIndex = Math.min(state.pageIndex, Math.max(0, Math.ceil(documents.length / COLLECTION_PAGE_SIZE) - 1));
  }
  updateFilterControls(state);
  renderListToolbar(state);
  renderRows(state, state.pagedBrowsing
    ? documents.slice(state.pageIndex * COLLECTION_PAGE_SIZE, (state.pageIndex + 1) * COLLECTION_PAGE_SIZE)
    : documents);
  updateCollectionControls(state);
  state.management?.projected(state.sortMode);
}

function renderListProjectionContained(state, reason) {
  try {
    renderListProjection(state);
    return true;
  } catch (error) {
    return reportFailure(state, error, reason);
  }
}

function reportFailure(state, error, reason) {
  if (!state.mounted) return false;
  try {
    publishState(state, "error", null, reason);
  } catch (_notifyError) {
    // Preserve the original operation failure if contribution notification fails.
  }
  renderError(state.root, error.message || "Failed to render docs collection report.");
  return false;
}

function captureListControls(state) {
  var captureContribution = contributionCallback(state.contribution, "captureListState");
  return { query: state.query, sort: state.sortMode,
    page: state.searchTimer !== null ? 0 : state.pageIndex,
    ...(typeof state.contribution?.paginationDefault === "boolean" ? { pagination: state.pagedBrowsing } : {}),
    contribution: captureContribution ? captureContribution.call(state.contribution) : null };
}

/** Restore controls against the current inventory, never a saved payload. */
function restoreListControls(state, saved) {
  if (JSON.stringify(captureListControls(state)) === JSON.stringify(saved)) return;
  cancelCollectionSearch(state);
  if (typeof saved.query === "string") state.query = saved.query;
  if (["title-asc", "last-updated-desc"].includes(saved.sort)) state.sortMode = saved.sort;
  if (typeof state.contribution?.paginationDefault === "boolean" && typeof saved.pagination === "boolean") {
    state.pagedBrowsing = saved.pagination;
  }
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
}

function renderError(root, message) {
  clearNode(root);
  root.dataset.reportState = "error";
  var note = document.createElement("p");
  note.className = "docsViewerReport__status is-error";
  note.textContent = message;
  root.appendChild(note);
}

function mountResolvedDocsCollectionReport(context, contribution, lifetime) {
  var root = context && context.reportRoot;
  var reportMeta = context && context.reportMeta ? context.reportMeta : {};
  var collectionIdValue = reportMeta.collection;
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

  var collection = context.collectionConfig;
  if (!collection || collection.collection !== collectionIdValue) {
    contributionEvent(context, collectionIdValue, {
      type: "state",
      state: "error",
      reason: "unconfigured-collection",
      target: null
    });
    renderError(root, "Docs collection is not configured: " + collectionIdValue);
    return Promise.resolve(true);
  }

  var url = collection.manifestUrl;
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

  var features = collectionBrowsingFeatures(collection);
  var refs = renderShell(context, collection, features);
  var state = {
    root: root,
    openDocument: context.openDocument,
    onDocumentState: context.onCollectionDocumentState,
    parentDocId: cleanString(context && context.doc && context.doc.doc_id),
    parentTarget: Object.freeze({
      doc_id: cleanString(context.doc && context.doc.doc_id)
    }),
    parentRecord: context.doc,
    collectionTarget: Object.freeze(collectionTarget(collectionIdValue)),
    listActionHost: contribution ? root.ownerDocument.createElement("div") : null,
    collection: collection,
    collectionId: collectionIdValue,
    manifestLoaded: false,
    query: "",
    sortMode: collectionIdValue === "catalogue" ? "last-updated-desc" : "title-asc",
    features: features,
    pagedBrowsing: contribution?.paginationDefault ?? features.pagination,
    paginationControl: null,
    thumbnailSettingsRead: null,
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
    statusNode: refs.statusNode,
    tableNode: refs.tableNode,
    rowsNode: refs.rowsNode,
    mounted: true
  };
  var browsingOptions = {
    collectionId: collectionIdValue, mediaRoot: context.mediaRoot,
    documentHref: function (docId) {
      return context.collectionProvider.documentHref({ collection: collectionIdValue, doc_id: docId });
    }
  };
  state.management = contribution ? contribution.createListManagement({
    browsingOptions: browsingOptions,
    collectionId: collectionIdValue,
    collectionProvider: context.collectionProvider,
    isMounted: function () { return state.mounted; },
    isReady: function () { return state.manifestLoaded; },
    notify: function (detail) { notifyContribution(state, detail); },
    render: function (reason) { return renderListProjectionContained(state, reason); },
    reveal: function () { renderListView(state); },
    fail: function (error, reason) { return reportFailure(state, error, reason); },
    loadManifest: function () { return state.loadManifest(); },
    resolveThumbnails: resolvePendingThumbnails
  }) : null;
  state.browsingData = state.management ? state.management.data : createCollectionBrowsingData(browsingOptions);
  if (state.listActionHost) state.listActionHost.className = "docsViewer__collectionActions";
  if (features.pagination) {
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
  }
  if (state.collectionSortNode) {
    state.collectionSortNode.addEventListener("click", function () {
      listSortContext(state).setMode(state.sortMode === "last-updated-desc" ? "title-asc" : "last-updated-desc");
    });
  }
  var mountPaginationControl = contributionCallback(contribution, "mountPaginationControl");
  if (mountPaginationControl) {
    state.paginationControl = mountPaginationControl({
      host: state.filterToolbarNode,
      change: function (enabled) {
        cancelCollectionSearch(state);
        state.pagedBrowsing = enabled;
        state.pageIndex = 0;
        contribution.resetSelection();
        renderListProjectionContained(state, "pagination-change");
        remembered.save();
      }
    });
  }
  updateCollectionControls(state);
  bindFilterControls(state);
  updateFilterControls(state);

  var remembered = createDocsCollectionReportState({
    root: root, collectionId: state.collectionId, hostDocId: state.parentDocId,
    isReady: function () { return state.mounted && state.manifestLoaded && root.dataset.reportState === "list"; },
    captureControls: function () { return captureListControls(state); },
    restoreControls: function (saved) { restoreListControls(state, saved); }
  });
  function restoreRememberedList() {
    if (!state.manifestLoaded || !state.mounted || root.dataset.reportState === "error") return;
    remembered.restore();
    renderListView(state);
    remembered.restorePosition();
  }
  function dispose() {
    if (!state.mounted) return;
    remembered.dispose();
    state.mounted = false;
    cancelCollectionSearch(state);
    publishState(state, "unmounted", null, "report-unmount");
    notifyContribution(state, { type: "unmount", reason: "report-unmount" });
    state.management?.dispose();
    state.browsingData.clear();
    state.matches = [];
    state.thumbnailSettingsRead = null;
  }
  lifetime.view = {
    dispose: dispose, capture: remembered.save, restore: restoreRememberedList, resume: restoreRememberedList
  };

  async function resolvePendingThumbnails() {
    if (!state.browsingData.needsThumbnailSettings) return false;
    if (!state.thumbnailSettingsRead) state.thumbnailSettingsRead = loadCatalogueCollectionThumbnailSettings(context);
    var settings = await state.thumbnailSettingsRead;
    return state.mounted && state.browsingData.setThumbnailSettings(settings);
  }

  notifyContribution(state, {
    type: "mount",
    root: root
  });
  publishState(state, "loading", null, "report-loading");
  state.loadManifest = function () {
    if (!state.mounted) return Promise.resolve(false);
    return fetchJson(url, "Failed to load docs collection manifest").then(async function (payload) {
      if (!state.mounted) return false;
      cancelCollectionSearch(state);
      state.browsingData.replace(payload.docs);
      await resolvePendingThumbnails();
      if (!state.mounted) return false;
      state.filterInputNode.disabled = false;
      state.manifestLoaded = true;
      state.listNeedsRender = true;
      state.management?.inventoryChanged("documents-loaded", true);
      return true;
    });
  };
  state.management?.connect();
  return state.loadManifest().then(function (loaded) {
      if (loaded) {
        // The document inventory must exist before restoring saved controls.
        root.dataset.reportState = "list";
        restoreRememberedList();
      }
      return true;
    })
    .catch(function (error) {
      reportFailure(state, error, "report-load-failed");
      return true;
    });
}

export function mountDocsCollectionReport(context) {
  var root = context && context.reportRoot;
  if (!root) return Promise.resolve(false);
  var lifetime = { active: true, view: null };
  context.registerRetainedView?.({
    id: "collection:" + context.reportMeta.collection,
    dispose: function () { lifetime.active = false; lifetime.view?.dispose(); lifetime.view = null; },
    capture: function () { return lifetime.view?.capture() || null; },
    restore: function () { lifetime.view?.restore(); },
    resume: function () { lifetime.view?.resume(); }
  });
  return Promise.resolve(context.collectionReportContributionPromise)
    .then(function (contribution) {
      if (!lifetime.active) return false;
      return mountResolvedDocsCollectionReport(
        Object.assign({}, context, {
          resolvedCollectionReportContribution: contribution
        }),
        contribution,
        lifetime
      );
    })
    .catch(function (error) {
      if (!lifetime.active) return false;
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
