import { renderResultEntry } from "./docs-viewer-render.js";
import { collectRecentDocs, collectSearchMatches, normalizeSearchText } from "./docs-viewer-search.js";

/** Give Index lists history and URL commands without document-opening or list-reset authority. */
export function createDocsViewerSearchRouteCommands(context) {
  var settings = context || {};
  var routeCommands = settings.routeCommands;
  return {
    updateIndexHistory: routeCommands.updateIndexHistory,
    viewerTargetDocId: settings.viewerTargetDocId,
    viewerUrl: routeCommands.viewerUrl
  };
}

/** Retain Index results independently of document navigation; providers own input validation. */
export function initDocsViewerSearchController(context) {
  var searchRecent = context.searchRecent;
  var resultsStatus = context.resultsStatus;
  var results = context.results;
  var more = context.more;
  var resultsView = context.resultsView;
  var routeCommands = context.routeCommands;
  var renderedIndex = null;
  var renderedQuery = "";
  var renderedCount = 0;
  var searchMatches = [];
  var renderedRecent = null;
  var renderedRecentLimit = 0;
  var renderedView = "";
  var searchError = "";
  var recentError = "";

  function enabled(feature) {
    return Boolean(context[feature + "Enabled"] && results && more);
  }

  function loadSearchIndex() {
    if (searchRecent.searchLoaded) return Promise.resolve(searchRecent.searchIndex);
    if (searchRecent.searchRequestPromise) return searchRecent.searchRequestPromise;
    var stopBusy = context.startBusy();
    searchRecent.searchRequestPromise = context.collectionProvider.readSearch()
      .then(function (payload) {
        searchRecent.searchIndex = payload;
        searchRecent.searchLoaded = true;
        return payload;
      }).finally(function () {
        stopBusy();
        searchRecent.searchRequestPromise = null;
      });
    return searchRecent.searchRequestPromise;
  }

  function loadRecentEntries() {
    if (searchRecent.recentLoaded) return Promise.resolve(searchRecent.recentEntries);
    if (searchRecent.recentRequestPromise) return searchRecent.recentRequestPromise;
    var stopBusy = context.startBusy();
    searchRecent.recentRequestPromise = context.collectionProvider.readRecent()
      .then(function (payload) {
        searchRecent.recentEntries = payload.docs;
        searchRecent.recentLoaded = true;
        return payload.docs;
      }).finally(function () {
        stopBusy();
        searchRecent.recentRequestPromise = null;
      });
    return searchRecent.recentRequestPromise;
  }

  function setResultsStatus(message, isError) {
    resultsStatus.textContent = String(message || "");
    resultsStatus.hidden = !message;
    resultsStatus.classList.toggle("is-error", Boolean(isError));
  }

  function cancelSearchDebounce() {
    if (searchRecent.searchDebounceId == null) return;
    window.clearTimeout(searchRecent.searchDebounceId);
    searchRecent.searchDebounceId = null;
  }

  function setView(viewId) {
    context.setIndexView(viewId);
  }

  function recentActive() {
    return context.activeIndexViewId() === "recent-results";
  }

  function resultEntry(entry, docId) {
    var config = context.workspaceConfig.activeConfig;
    var collectionId = entry.collection || "";
    var collection = collectionId
      ? config.collectionsById.get(collectionId)
      : config.collectionsByReportHostId.get(docId);
    var iconUrl = collectionId ? collection.iconUrl : collection ? collection.iconUrl : "";
    var href = collectionId
      ? routeCommands.viewerUrl(entry.report_doc_id, "", searchRecent.searchQuery, { subdoc: docId })
      : routeCommands.viewerUrl(routeCommands.viewerTargetDocId(docId), "", searchRecent.searchQuery);
    return renderResultEntry({
      docId: docId, title: entry.title, collection: collectionId,
      iconUrl: iconUrl, href: href
    });
  }

  /** Compare exact in-memory targets; navigation does not rerender rows or move list scroll/focus. */
  function syncSelection() {
    var target = context.currentDocumentTarget();
    results.querySelectorAll("[data-result-doc-id]").forEach(function (link) {
      var active = Boolean(target && link.dataset.resultDocId === target.doc_id
        && link.dataset.resultCollection === (target.collection || ""));
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  function clearRows(message, isError) {
    setResultsStatus(message, isError);
    results.replaceChildren();
    more.replaceChildren();
    more.hidden = true;
    renderedView = "";
  }

  function renderRecentMode() {
    if (!enabled("recent")) return;
    setView("recent-results");
    if (recentError) { clearRows(recentError, true); return; }
    if (!searchRecent.recentLoaded) {
      clearRows("Loading recently edited docs...", false);
      if (searchRecent.recentRequestPromise) return;
      loadRecentEntries().then(function () {
        if (recentActive()) renderRecentMode();
      }).catch(function (error) {
        recentError = error.message || "Failed to load Recent docs.";
        if (recentActive()) clearRows(recentError, true);
      });
      return;
    }
    if (renderedView === "recent-results" && renderedRecent === searchRecent.recentEntries
      && renderedRecentLimit === searchRecent.recentLimit) { syncSelection(); return; }
    try {
      renderRecentRows();
    } catch (error) {
      clearRows(error.message || "Could not render Recent docs.", true);
    }
  }

  function renderRecentRows() {
    var docs = collectRecentDocs(searchRecent.recentEntries, searchRecent.recentLimit);
    setResultsStatus(docs.length ? "" : "No recently edited docs.", false);
    results.innerHTML = docs.map(function (doc) { return resultEntry(doc, doc.doc_id); }).join("");
    more.replaceChildren();
    more.hidden = true;
    renderedRecent = searchRecent.recentEntries;
    renderedRecentLimit = searchRecent.recentLimit;
    renderedView = "recent-results";
    resultsView.scrollTop = 0;
    syncSelection();
  }

  function renderSearchPendingState() {
    if (!enabled("search") || !context.hasActiveQuery()) return;
    setView("search-results");
    clearRows("Searching...", false);
    resultsView.scrollTop = 0;
  }

  function renderSearchMode() {
    if (!enabled("search") || !context.hasActiveQuery()) return;
    var query = normalizeSearchText(searchRecent.searchQuery);
    setView("search-results");
    if (searchError) { clearRows(searchError, true); return; }
    if (!searchRecent.searchLoaded) {
      clearRows("Loading search data...", false);
      if (searchRecent.searchRequestPromise) return;
      loadSearchIndex().then(function () {
        if (context.hasActiveQuery()) renderSearchMode();
      }).catch(function (error) {
        searchError = error.message || "Failed to load search data.";
        if (context.hasActiveQuery()) clearRows(searchError, true);
      });
      return;
    }
    try {
      renderSearchRows(query);
    } catch (error) {
      clearRows(error.message || "Could not render search results.", true);
    }
  }

  function renderSearchRows(query) {
    var changedQuery = renderedQuery !== query || renderedIndex !== searchRecent.searchIndex;
    if (changedQuery) {
      searchMatches = collectSearchMatches(searchRecent.searchIndex, query);
      renderedQuery = query;
      renderedIndex = searchRecent.searchIndex;
    }
    if (!changedQuery && renderedView === "search-results"
      && renderedCount === searchRecent.searchVisibleCount) { syncSelection(); return; }
    var visible = searchMatches.slice(0, searchRecent.searchVisibleCount);
    var scrollTop = changedQuery ? 0 : resultsView.scrollTop;
    setResultsStatus(searchMatches.length ? "" : "No results.", false);
    results.innerHTML = visible.map(function (match) { return resultEntry(match.entry, match.entry.id); }).join("");
    more.hidden = searchMatches.length <= visible.length;
    more.innerHTML = more.hidden ? "" : '<button type="button" class="docsViewer__moreBtn" data-role="more">more</button>';
    renderedCount = searchRecent.searchVisibleCount;
    renderedView = "search-results";
    resultsView.scrollTop = scrollTop;
    syncSelection();
  }

  function bind() {
    more.addEventListener("click", function (event) {
      if (!event.target.closest("button[data-role='more']")) return;
      searchRecent.searchVisibleCount += context.searchBatchSize;
      renderSearchMode();
    });
  }

  function handleRecentControl() {
    if (!enabled("recent")) return;
    context.hideContextMenu();
    cancelSearchDebounce();
    var viewId = recentActive() ? "index-tree" : "recent-results";
    searchRecent.searchQuery = "";
    searchRecent.searchVisibleCount = context.searchBatchSize;
    context.setSearchInput("");
    setView(viewId);
    routeCommands.updateIndexHistory("", viewId, "push");
    if (viewId === "recent-results") renderRecentMode();
  }

  function handleSearchInput(value) {
    if (!enabled("search")) return;
    var query = String(value || "").trim();
    var wasSearching = context.hasActiveQuery();
    cancelSearchDebounce();
    searchRecent.searchQuery = query;
    searchRecent.searchVisibleCount = context.searchBatchSize;
    var viewId = normalizeSearchText(query) ? "search-results" : "index-tree";
    setView(viewId);
    routeCommands.updateIndexHistory(query, viewId, wasSearching ? "replace" : "push");
    if (viewId === "index-tree") return;
    renderSearchPendingState();
    searchRecent.searchDebounceId = window.setTimeout(function () {
      searchRecent.searchDebounceId = null;
      renderSearchMode();
    }, context.searchDebounceMs);
  }

  /** Apply URL/history view state separately from opening the route's document. */
  function applyRoute(query, indexViewId) {
    var nextQuery = enabled("search") ? String(query || "").trim() : "";
    if (searchRecent.searchQuery !== nextQuery) searchRecent.searchVisibleCount = context.searchBatchSize;
    searchRecent.searchQuery = nextQuery;
    context.setSearchInput(nextQuery);
    if (normalizeSearchText(nextQuery)) renderSearchMode();
    else if (enabled("recent") && indexViewId === "recent-results") renderRecentMode();
    else setView("index-tree");
  }

  /** Explicit management reload invalidates lists; changing visibility never does. */
  function resetForReload() {
    cancelSearchDebounce();
    renderedIndex = null;
    renderedRecent = null;
    renderedView = "";
    searchError = "";
    recentError = "";
    searchRecent.searchQuery = "";
    context.setSearchInput("");
    setView("index-tree");
  }

  return {
    applyRoute: applyRoute,
    bind: bind,
    handleRecentControl: handleRecentControl,
    handleSearchInput: handleSearchInput,
    renderRecentMode: renderRecentMode,
    renderSearchMode: renderSearchMode,
    resetForReload: resetForReload,
    syncSelection: syncSelection
  };
}
