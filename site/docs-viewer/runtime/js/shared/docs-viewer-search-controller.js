import { renderResultEntry } from "./docs-viewer-render.js";
import { collectRecentDocs, collectSearchMatches, normalizeSearchText, tokenizeSearchValue } from "./docs-viewer-search.js";

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
      ? routeCommands.viewerUrl(docId, "", searchRecent.searchQuery, { collection: collectionId })
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

  /** Discard cached Recent data and errors after its owner refreshes the artifact. */
  function refreshRecent() {
    searchRecent.recentLoaded = false;
    searchRecent.recentEntries = [];
    recentError = "";
    if (recentActive()) renderRecentMode();
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
      searchMatches = collectSearchMatches(searchRecent.searchIndex, query).filter(function (match) { return !deletedResults.has((match.entry.collection || "") + ":" + match.entry.id); });
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

  function commitDocumentChange(change) {
    var target = change.target;
    var matches = function (entry) { return (entry.collection || "") === (target.collection || "") && (entry.id || entry.doc_id) === target.doc_id; };
    var scroll = resultsView.scrollTop;
    if (searchRecent.searchLoaded) {
      var index = searchRecent.searchIndex;
      var position = index.docs.findIndex(matches);
      if (position >= 0) {
        var fields = ["title", "summary", "last_updated"];
        Object.values(index.terms).forEach(function (posting) {
          fields.forEach(function (field) { if (posting[field]) posting[field] = posting[field].filter(function (item) { return item !== position; }); });
        });
        if (change.deleted) deletedResults.add((target.collection || "") + ":" + target.doc_id);
        else {
          deletedResults.delete((target.collection || "") + ":" + target.doc_id);
          index.docs[position] = Object.assign({}, index.docs[position], change.record, { id: target.doc_id, collection: target.collection || "" });
          fields.forEach(function (field) {
            var terms = field === "last_updated" ? [normalizeSearchText(change.record[field])] : tokenizeSearchValue(change.record[field]);
            terms.filter(Boolean).forEach(function (term) {
              var posting = index.terms[term] || (index.terms[term] = {});
              var positions = posting[field] || (posting[field] = []);
              positions.push(position); positions.sort(function (left, right) { return left - right; });
            });
          });
        }
        renderedIndex = null;
      }
    }
    if (searchRecent.recentLoaded) {
      var existing = searchRecent.recentEntries.find(matches);
      searchRecent.recentEntries = searchRecent.recentEntries.filter(function (entry) { return !matches(entry); });
      if (!change.deleted && existing) searchRecent.recentEntries.push(Object.assign({}, existing, change.record, { timestamp: change.record.last_updated }));
    }
    if (context.activeIndexViewId() === "search-results") renderSearchMode();
    if (recentActive()) renderRecentMode();
    resultsView.scrollTop = scroll;
  }
  var deletedResults = new Set();
  if (context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(commitDocumentChange);

  function bind() {
    more.addEventListener("click", function (event) {
      if (!event.target.closest("button[data-role='more']")) return;
      searchRecent.searchVisibleCount += context.searchBatchSize;
      renderSearchMode();
      routeCommands.updateIndexHistory(searchRecent.searchQuery);
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
    routeCommands.updateIndexHistory("");
    if (viewId === "recent-results") renderRecentMode();
  }

  function handleSearchInput(value) {
    if (!enabled("search")) return;
    var query = String(value || "").trim();
    cancelSearchDebounce();
    searchRecent.searchQuery = query;
    searchRecent.searchVisibleCount = context.searchBatchSize;
    var viewId = normalizeSearchText(query) ? "search-results" : "index-tree";
    setView(viewId);
    routeCommands.updateIndexHistory(query);
    if (viewId === "index-tree") return;
    renderSearchPendingState();
    searchRecent.searchDebounceId = window.setTimeout(function () {
      searchRecent.searchDebounceId = null;
      renderSearchMode();
    }, context.searchDebounceMs);
  }

  /** Apply the initial URL's Search query separately from opening its document. */
  function applyRoute(query) {
    var nextQuery = enabled("search") ? String(query || "").trim() : "";
    if (searchRecent.searchQuery !== nextQuery) searchRecent.searchVisibleCount = context.searchBatchSize;
    searchRecent.searchQuery = nextQuery;
    context.setSearchInput(nextQuery);
    if (normalizeSearchText(nextQuery)) renderSearchMode();
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
    refreshRecent: refreshRecent,
    renderSearchMode: renderSearchMode,
    resetForReload: resetForReload,
    syncSelection: syncSelection
  };
}
