import {
  renderRecentEntry,
  renderSearchEntry
} from "./docs-viewer-render.js";
import {
  collectRecentDocs,
  collectSearchMatches,
  normalizeSearchEntries,
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  isDocViewable
} from "./docs-viewer-tree.js";

export function createDocsViewerSearchRouteCommands(context) {
  var settings = context || {};
  var routeWorkflow = settings.routeWorkflow;
  return {
    applyCurrentRoute: function (options) {
      return routeWorkflow.applyCurrentRoute(options);
    },
    defaultDocId: function () {
      return typeof settings.defaultDocId === "function" ? settings.defaultDocId() : "";
    },
    resolveDocId: function () {
      return routeWorkflow.resolveDocId();
    },
    setHistory: function (docId, hash, query, mode) {
      return routeWorkflow.setHistory(docId, hash, query, mode);
    },
    viewerTargetDocId: function (docId) {
      return typeof settings.viewerTargetDocId === "function" ? settings.viewerTargetDocId(docId) : docId;
    },
    viewerUrl: function (docId, hash, query) {
      return routeWorkflow.viewerUrl(docId, hash, query);
    }
  };
}

export function initDocsViewerSearchController(context) {
  var searchRecent = context.searchRecent;
  var documentIndex = context.documentIndex;
  var selectedDocument = context.selectedDocument;
  var resultsStatus = context.resultsStatus;
  var results = context.results;
  var more = context.more;
  var searchInput = context.searchInput;
  var paneCommands = context.paneCommands || {};
  var routeCommands = context.routeCommands || {};

  function currentSearchIndexUrl() {
    return typeof context.searchIndexUrl === "function" ? context.searchIndexUrl() : context.searchIndexUrl;
  }

  function currentViewerScope() {
    return typeof context.viewerScope === "function" ? context.viewerScope() : context.viewerScope;
  }

  function searchIsEnabled() {
    return Boolean(searchInput && results && more && currentSearchIndexUrl());
  }

  function searchControlsAvailable() {
    return Boolean(searchInput && results && more);
  }

  function applyCurrentRoute(options) {
    var callback = routeCommands.applyCurrentRoute;
    if (typeof callback === "function") return callback(options);
    return null;
  }

  function defaultDocId() {
    var callback = routeCommands.defaultDocId;
    return typeof callback === "function" ? callback() : "";
  }

  function hideDocPane() {
    var callback = paneCommands.hideDocPane;
    if (typeof callback === "function") callback();
  }

  function resolveDocId() {
    var callback = routeCommands.resolveDocId;
    return typeof callback === "function" ? callback() : { docId: "" };
  }

  function setHistory(docId, hash, query, mode) {
    var callback = routeCommands.setHistory;
    if (typeof callback === "function") callback(docId, hash, query, mode);
  }

  function showRecentPane() {
    var callback = paneCommands.showRecentPane;
    if (typeof callback === "function") callback();
  }

  function showSearchPane() {
    var callback = paneCommands.showSearchPane;
    if (typeof callback === "function") callback();
  }

  function viewerTargetDocId(docId) {
    var callback = routeCommands.viewerTargetDocId;
    return typeof callback === "function" ? callback(docId) : docId;
  }

  function viewerUrl(docId, hash, query) {
    var callback = routeCommands.viewerUrl;
    return typeof callback === "function" ? callback(docId, hash, query) : "#";
  }

  function loadSearchEntries() {
    if (!searchIsEnabled()) {
      return Promise.reject(new Error("Search unavailable."));
    }
    if (searchRecent.searchLoaded) {
      return Promise.resolve(searchRecent.searchEntries);
    }
    if (searchRecent.searchRequestPromise) {
      return searchRecent.searchRequestPromise;
    }

    var stopBusy = typeof context.startBusy === "function" ? context.startBusy() : function () {};

    searchRecent.searchRequestPromise = context.generatedData.readSearchIndex({
      searchIndexUrl: currentSearchIndexUrl(),
      viewerScope: currentViewerScope()
    })
      .then(function (payload) {
        searchRecent.searchEntries = normalizeSearchEntries(payload && Array.isArray(payload.entries) ? payload.entries : []);
        searchRecent.searchLoaded = true;
        return searchRecent.searchEntries;
      })
      .catch(function (error) {
        searchRecent.searchLoaded = false;
        throw error;
      })
      .finally(function () {
        stopBusy();
        searchRecent.searchRequestPromise = null;
      });

    return searchRecent.searchRequestPromise;
  }

  function setResultsStatus(message, isError) {
    if (!resultsStatus) {
      if (isError && typeof context.setStatus === "function") context.setStatus(message, true);
      return;
    }
    resultsStatus.textContent = String(message || "");
    resultsStatus.hidden = !message;
    resultsStatus.classList.toggle("is-error", Boolean(isError));
  }

  function clearResultsStatus() {
    setResultsStatus("", false);
  }

  function cancelSearchDebounce() {
    if (searchRecent.searchDebounceId == null) return;
    window.clearTimeout(searchRecent.searchDebounceId);
    searchRecent.searchDebounceId = null;
  }

  function displayRecentMetaForDoc(doc) {
    if (!doc) return "";
    var parts = [];
    var addedDate = String(doc.added_date || doc.last_updated || "").trim();
    if (addedDate) parts.push(addedDate);
    if (doc.parent_id) {
      var parent = documentIndex.docsById.get(doc.parent_id);
      var parentTitle = parent ? String(parent.title || "").trim() : "";
      if (parentTitle) parts.push(parentTitle);
    }
    return parts.join(" • ");
  }

  function renderSearchResultEntry(entry) {
    return renderSearchEntry(entry, viewerUrl(viewerTargetDocId(entry.id), "", ""));
  }

  function renderRecentResultEntry(doc) {
    return renderRecentEntry(doc, displayRecentMetaForDoc(doc), viewerUrl(viewerTargetDocId(doc.doc_id), "", ""));
  }

  function renderRecentMode() {
    if (!searchIsEnabled()) return;
    context.setRecentModeActive(true);
    showRecentPane();
    document.title = "Recently Added | dotlineform";
    var recentDocs = collectRecentDocs(documentIndex.docs.filter(isDocViewable), searchRecent.recentLimit);
    if (!recentDocs.length) {
      setResultsStatus("No recently added docs.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    setResultsStatus(recentDocs.length === 1 ? "1 recently added doc" : recentDocs.length + " recently added docs", false);
    results.innerHTML = recentDocs.map(renderRecentResultEntry).join("");
    more.innerHTML = "";
    more.hidden = true;
  }

  function renderSearchPendingState() {
    if (!searchIsEnabled() || !context.hasActiveQuery()) return;
    context.setRecentModeActive(false);
    showSearchPane();
    clearResultsStatus();
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    document.title = "Search | dotlineform";
  }

  function renderSearchMode() {
    if (!searchIsEnabled()) {
      if (searchControlsAvailable()) {
        showSearchPane();
        setResultsStatus("Search unavailable.", true);
        results.innerHTML = "";
        more.innerHTML = "";
        more.hidden = true;
      } else {
        context.setStatus("Search unavailable.", true);
        hideDocPane();
        if (results) results.hidden = true;
        if (more) more.hidden = true;
      }
      return;
    }

    var query = normalizeSearchText(searchRecent.searchQuery);
    if (!query) {
      return;
    }

    showSearchPane();
    context.setRecentModeActive(false);
    document.title = "Search | dotlineform";

    if (!searchRecent.searchLoaded) {
      renderSearchPendingState();
      loadSearchEntries()
        .then(function () {
          if (context.hasActiveQuery()) {
            renderSearchMode();
          }
        })
        .catch(function (error) {
          if (!context.hasActiveQuery()) return;
          setResultsStatus(error.message || "Failed to load search data.", true);
          results.innerHTML = "";
          more.innerHTML = "";
          more.hidden = true;
        });
      return;
    }

    var matches = collectSearchMatches(searchRecent.searchEntries, query);
    if (!matches.length) {
      setResultsStatus("No results.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    var visible = matches.slice(0, searchRecent.searchVisibleCount);
    setResultsStatus(matches.length === 1
      ? "1 result"
      : matches.length > visible.length
        ? "Showing " + visible.length + " of " + matches.length + " results"
        : matches.length + " results",
    false);
    results.innerHTML = visible.map(function (match) {
      return renderSearchResultEntry(match.entry);
    }).join("");
    if (matches.length > visible.length) {
      more.hidden = false;
      more.innerHTML = '<button type="button" class="docsViewer__moreBtn" data-role="more">more</button>';
    } else {
      more.hidden = true;
      more.innerHTML = "";
    }
  }

  function bind() {
    if (context.recentButton) {
      context.recentButton.addEventListener("click", function () {
        context.hideContextMenu();
        cancelSearchDebounce();
        var activeDocId = selectedDocument.selectedDocId || resolveDocId().docId || defaultDocId();
        searchRecent.searchQuery = "";
        searchRecent.searchRouteActive = false;
        searchRecent.searchVisibleCount = context.searchBatchSize;
        if (searchInput) {
          searchInput.value = "";
        }
        if (activeDocId) {
          setHistory(activeDocId, "", "", "push");
        }
        renderRecentMode();
      });
    }

    if (!searchControlsAvailable()) return;

    more.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-role='more']");
      if (!button) return;
      searchRecent.searchVisibleCount += context.searchBatchSize;
      renderSearchMode();
    });

    searchInput.addEventListener("input", function () {
      var nextQuery = String(searchInput.value || "").trim();
      var nextModeActive = Boolean(normalizeSearchText(nextQuery));
      var previousModeActive = searchRecent.searchRouteActive;
      var activeDocId = selectedDocument.selectedDocId || resolveDocId().docId || "";

      cancelSearchDebounce();
      context.setRecentModeActive(false);
      searchRecent.searchQuery = nextQuery;
      searchRecent.searchVisibleCount = context.searchBatchSize;

      if (!activeDocId) {
        return;
      }

      if (!nextModeActive) {
        searchRecent.searchRouteActive = false;
        setHistory(activeDocId, "", "", previousModeActive ? "replace" : "none");
        applyCurrentRoute({ historyMode: "none", hash: "" });
        return;
      }

      searchRecent.searchRouteActive = true;
      setHistory(activeDocId, "", nextQuery, previousModeActive ? "replace" : "push");
      renderSearchPendingState();
      searchRecent.searchDebounceId = window.setTimeout(function () {
        searchRecent.searchDebounceId = null;
        applyCurrentRoute({ historyMode: "none", hash: "" });
      }, context.searchDebounceMs);
    });
  }

  return {
    bind: bind,
    renderRecentMode: renderRecentMode,
    renderSearchMode: renderSearchMode,
    renderSearchPendingState: renderSearchPendingState
  };
}
