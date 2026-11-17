import { renderResultEntry } from "./docs-viewer-render.js";
import {
  COLLECTION_SEARCH_SCOPES, PORTFOLIO_SEARCH_SCOPE, REFERENCE_SEARCH_SCOPES,
  collectSearchMatches, normalizeSearchText
} from "./docs-viewer-search.js";

/** Give Index lists history and URL commands without document-opening or list-reset authority. */
export function createDocsViewerSearchRouteCommands(context) {
  var settings = context || {};
  var routeCommands = settings.routeCommands;
  return {
    updateIndexHistory: routeCommands.updateIndexHistory,
    viewerUrl: routeCommands.viewerUrl
  };
}

/** Retain Index results independently of document navigation; providers own input validation. */
export function initDocsViewerSearchController(context) {
  var searchRecent = context.searchRecent;
  var searchInput = context.searchInput;
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
  var renderedView = "";
  var scopeIndexes = new Map();
  var portfolioSelected = false;
  var recentError = "";

  function enabled(feature) {
    return Boolean(context[feature + "Enabled"] && results && more);
  }

  function collectionScope(target = context.currentDocumentTarget()) {
    var config = context.workspaceConfig.activeConfig;
    var id = target?.collection || config?.collectionsByReportHostId.get(target?.doc_id)?.collection;
    return COLLECTION_SEARCH_SCOPES.has(id) && config?.collectionsById.has(id) ? id : "";
  }

  function preferredScope(collection = collectionScope()) {
    return (portfolioSelected ? "" : collection) || PORTFOLIO_SEARCH_SCOPE;
  }

  function currentScope(collection) {
    return searchRecent.searchScope || preferredScope(collection);
  }

  function controls() {
    var local = collectionScope();
    var active = currentScope(local);
    var collections = context.workspaceConfig.activeConfig?.collectionsById;
    var destination = active === PORTFOLIO_SEARCH_SCOPE && local ? collections.get(local) : null;
    return {
      label: active === PORTFOLIO_SEARCH_SCOPE ? "Search portfolio" : "Search " + collections.get(active).title,
      scopeButton: {
        disabled: !local,
        label: destination ? "Search " + destination.title : "Search portfolio",
        iconUrl: destination?.iconUrl
      }
    };
  }

  function activeScope(scope) {
    return context.activeIndexViewId() === "search-results" && searchRecent.searchScope === scope;
  }

  function requestScopeIndex(scope) {
    var record = {};
    scopeIndexes.set(scope, record);
    var stopBusy = context.startBusy();
    record.ready = context.collectionProvider.readSearch(scope).then(function (payload) {
      record.payload = payload;
    }).catch(function (error) {
      record.error = error.message || "Failed to load search data.";
    }).finally(stopBusy).then(function () {
      if (scopeIndexes.get(scope) === record && activeScope(scope)) renderSearchMode();
    });
    return record;
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
    if (entry.kind === "catalogue-gallery") {
      return renderResultEntry({ title: entry.title, galleryId: entry.id });
    }
    var config = context.workspaceConfig.activeConfig;
    var collectionId = entry.collection || "";
    var collection = collectionId
      ? config.collectionsById.get(collectionId)
      : config.collectionsByReportHostId.get(docId);
    var iconUrl = collectionId ? collection.iconUrl : collection ? collection.iconUrl : "";
    var href = collectionId
      ? routeCommands.viewerUrl(docId, "", searchRecent.searchQuery, { collection: collectionId })
      : routeCommands.viewerUrl(docId, "", searchRecent.searchQuery);
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
      clearRows("", false);
      if (searchRecent.recentRequestPromise) return;
      loadRecentEntries().then(function () {
        if (recentActive()) renderRecentMode();
      }).catch(function (error) {
        recentError = error.message || "Failed to load Recent docs.";
        if (recentActive()) clearRows(recentError, true);
      });
      return;
    }
    if (renderedView === "recent-results" && renderedRecent === searchRecent.recentEntries) { syncSelection(); return; }
    try {
      renderRecentRows();
    } catch (error) {
      clearRows(error.message || "Could not render Recent docs.", true);
    }
  }

  /** Discard cached Recent data and errors after its owner refreshes the artifact. */
  async function refreshRecent() {
    if (!enabled("recent")) return;
    var scroll = resultsView.scrollTop;
    searchRecent.recentLoaded = false;
    searchRecent.recentEntries = [];
    recentError = "";
    if (recentActive()) {
      await loadRecentEntries();
      renderRecentMode();
      resultsView.scrollTop = scroll;
    }
  }

  /** The explicit Search refresh replaces cached snapshots across all scopes. */
  async function refreshSearch() {
    if (!enabled("search")) return;
    var scroll = resultsView.scrollTop;
    scopeIndexes.clear();
    renderedIndex = null;
    deletedResults.clear();
    var scope = searchRecent.searchScope;
    if (activeScope(scope)) {
      renderSearchMode();
      var record = scopeIndexes.get(scope);
      await record?.ready;
      if (activeScope(scope)) resultsView.scrollTop = scroll;
      if (record?.error) throw new Error(record.error);
    }
  }

  function renderRecentRows() {
    var docs = searchRecent.recentEntries;
    setResultsStatus(docs.length ? "" : "No recent additions.", false);
    results.innerHTML = docs.map(function (doc) { return resultEntry(doc, doc.doc_id); }).join("");
    more.replaceChildren();
    more.hidden = true;
    renderedRecent = searchRecent.recentEntries;
    renderedView = "recent-results";
    resultsView.scrollTop = 0;
    syncSelection();
  }

  function renderSearchPendingState() {
    if (!enabled("search") || !context.hasActiveQuery()) return;
    setView("search-results");
    clearRows("", false);
    resultsView.scrollTop = 0;
  }

  function renderSearchMode() {
    if (!enabled("search") || !context.hasActiveQuery()) return;
    var query = normalizeSearchText(searchRecent.searchQuery);
    setView("search-results");
    var scope = currentScope();
    var record = scopeIndexes.get(scope) || requestScopeIndex(scope);
    if (record.error) { clearRows(record.error, true); return; }
    if (!record.payload) { clearRows("", false); return; }
    try {
      renderSearchRows(query, record.payload);
    } catch (error) {
      clearRows(error.message || "Could not render search results.", true);
    }
  }

  function renderSearchRows(query, index) {
    var changedQuery = renderedQuery !== query || renderedIndex !== index;
    if (changedQuery) {
      searchMatches = collectSearchMatches(index, query).filter(function (match) { return !deletedResults.has((match.entry.collection || "") + ":" + match.entry.id); });
      renderedQuery = query;
      renderedIndex = index;
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
    if (!change.deleted) return;
    var target = change.target;
    var scroll = resultsView.scrollTop;
    deletedResults.add((target.collection || "") + ":" + target.doc_id);
    renderedIndex = null;
    if (context.activeIndexViewId() === "search-results") renderSearchMode();
    var entries = searchRecent.recentEntries;
    var remaining = entries.filter(function (entry) {
      return entry.doc_id !== target.doc_id || (entry.collection || "") !== (target.collection || "");
    });
    if (remaining.length !== entries.length) {
      searchRecent.recentEntries = remaining;
      if (recentActive()) renderRecentMode();
    }
    resultsView.scrollTop = scroll;
  }
  var deletedResults = new Set();
  if (context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(commitDocumentChange);

  /** Move focus through the displayed list; normal links retain opening authority. */
  function handleResultKeyDown(event) {
    if (event.defaultPrevented || event.isComposing || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (!["ArrowDown", "ArrowUp", "Escape"].includes(event.key)) return;
    if (!["search-results", "recent-results"].includes(context.activeIndexViewId())) return;
    if (event.target === searchInput) {
      if (event.key !== "ArrowDown") return;
      event.preventDefault();
      event.stopPropagation();
      if (searchRecent.searchDebounceId != null) {
        cancelSearchDebounce();
        renderSearchMode();
      }
      results.querySelector(".docsViewer__resultTitle")?.focus();
      return;
    }
    var link = event.target.closest(".docsViewer__resultTitle");
    if (!link || !results.contains(link)) return;
    if (event.key === "Escape" && !searchInput) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.key === "Escape") {
      searchInput.focus();
      return;
    }
    var row = link.parentElement;
    var adjacent = event.key === "ArrowUp" ? row.previousElementSibling : row.nextElementSibling;
    if (adjacent) {
      adjacent.querySelector(".docsViewer__resultTitle").focus();
    } else if (event.key === "ArrowUp" && searchInput) {
      searchInput.focus();
    }
  }

  function bind() {
    if (searchInput) searchInput.addEventListener("keydown", handleResultKeyDown);
    results.addEventListener("keydown", handleResultKeyDown);
    results.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-result-gallery-id]");
      if (!button) return;
      context.openGallery(button.dataset.resultGalleryId, button).catch(function (error) {
        setResultsStatus(error.message || "Gallery could not open.", true);
      });
    });
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
    searchRecent.searchScope = "";
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
    if (!searchRecent.searchQuery && query) searchRecent.searchScope = preferredScope();
    if (!normalizeSearchText(query)) searchRecent.searchScope = "";
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

  function togglePortfolio() {
    var local = collectionScope();
    if (!local) return;
    portfolioSelected = currentScope(local) !== PORTFOLIO_SEARCH_SCOPE;
    if (context.hasActiveQuery()) {
      cancelSearchDebounce();
      searchRecent.searchScope = preferredScope(local);
      searchRecent.searchVisibleCount = context.searchBatchSize;
      routeCommands.updateIndexHistory(searchRecent.searchQuery);
      renderSearchMode();
    }
    context.renderControls();
  }

  function selectIndexTarget(target) {
    var scope = collectionScope(target);
    if (!REFERENCE_SEARCH_SCOPES.has(scope)) return;
    portfolioSelected = false;
    if (context.hasActiveQuery()) {
      searchRecent.searchScope = scope;
      routeCommands.updateIndexHistory(searchRecent.searchQuery);
      renderSearchMode();
    }
    context.renderControls();
  }

  /** Apply a shared search URL independently from opening its document. */
  function applyRoute(query, scope, target) {
    var nextQuery = enabled("search") ? String(query || "").trim() : "";
    var validScope = scope === PORTFOLIO_SEARCH_SCOPE
      || COLLECTION_SEARCH_SCOPES.has(scope) && context.workspaceConfig.activeConfig.collectionsById.has(scope);
    portfolioSelected = validScope && scope === PORTFOLIO_SEARCH_SCOPE;
    searchRecent.searchQuery = nextQuery;
    searchRecent.searchScope = nextQuery ? (validScope ? scope : preferredScope(collectionScope(target))) : "";
    searchRecent.searchVisibleCount = context.searchBatchSize;
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
    for (var [scope, record] of scopeIndexes) {
      if (record.error) scopeIndexes.delete(scope);
    }
    recentError = "";
    searchRecent.searchQuery = "";
    searchRecent.searchScope = "";
    context.setSearchInput("");
    setView("index-tree");
  }

  return {
    applyRoute: applyRoute,
    controls: controls,
    togglePortfolio: togglePortfolio,
    selectIndexTarget: selectIndexTarget,
    bind: bind,
    handleRecentControl: handleRecentControl,
    handleSearchInput: handleSearchInput,
    renderRecentMode: renderRecentMode,
    refreshRecent: refreshRecent,
    refreshSearch: refreshSearch,
    renderSearchMode: renderSearchMode,
    resetForReload: resetForReload,
    syncSelection: syncSelection
  };
}
