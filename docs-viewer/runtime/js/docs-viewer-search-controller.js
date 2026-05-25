import {
  fetchPreferredGeneratedJson,
  managementReloadPath
} from "./docs-viewer-data.js";
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

export function initDocsViewerSearchController(context) {
  var state = context.state;
  var resultsStatus = context.resultsStatus;
  var results = context.results;
  var more = context.more;
  var searchInput = context.searchInput;

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

  function loadSearchEntries() {
    if (!searchIsEnabled()) {
      return Promise.reject(new Error("Search unavailable."));
    }
    if (state.searchLoaded) {
      return Promise.resolve(state.searchEntries);
    }
    if (state.searchRequestPromise) {
      return state.searchRequestPromise;
    }

    var stopBusy = typeof context.startBusy === "function" ? context.startBusy() : function () {};

    state.searchRequestPromise = fetchPreferredGeneratedJson(
      currentSearchIndexUrl(),
      "Failed to load search data",
      managementReloadPath("/docs/generated/search", { scope: currentViewerScope() }),
      context.dataRequestOptions({ useSearchCapability: true })
    )
      .then(function (payload) {
        state.searchEntries = normalizeSearchEntries(payload && Array.isArray(payload.entries) ? payload.entries : []);
        state.searchLoaded = true;
        return state.searchEntries;
      })
      .catch(function (error) {
        state.searchLoaded = false;
        throw error;
      })
      .finally(function () {
        stopBusy();
        state.searchRequestPromise = null;
      });

    return state.searchRequestPromise;
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

  function displayRecentMetaForDoc(doc) {
    if (!doc) return "";
    var parts = [];
    var addedDate = String(doc.added_date || doc.last_updated || "").trim();
    if (addedDate) parts.push(addedDate);
    if (doc.parent_id) {
      var parent = state.docsById.get(doc.parent_id);
      var parentTitle = parent ? String(parent.title || "").trim() : "";
      if (parentTitle) parts.push(parentTitle);
    }
    return parts.join(" • ");
  }

  function renderSearchResultEntry(entry) {
    return renderSearchEntry(entry, context.viewerUrl(context.viewerTargetDocId(entry.id), "", ""));
  }

  function renderRecentResultEntry(doc) {
    return renderRecentEntry(doc, displayRecentMetaForDoc(doc), context.viewerUrl(context.viewerTargetDocId(doc.doc_id), "", ""));
  }

  function renderRecentMode() {
    if (!searchIsEnabled()) return;
    context.showRecentPane();
    document.title = "Recently Added | dotlineform";
    var recentDocs = collectRecentDocs(state.docs.filter(isDocViewable), state.recentLimit);
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
    context.showSearchPane();
    clearResultsStatus();
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    document.title = "Search | dotlineform";
  }

  function renderSearchMode() {
    if (!searchIsEnabled()) {
      if (searchControlsAvailable()) {
        context.showSearchPane();
        setResultsStatus("Search unavailable.", true);
        results.innerHTML = "";
        more.innerHTML = "";
        more.hidden = true;
      } else {
        context.setStatus("Search unavailable.", true);
        context.hideDocPane();
        if (results) results.hidden = true;
        if (more) more.hidden = true;
      }
      return;
    }

    var query = normalizeSearchText(state.searchQuery);
    if (!query) {
      return;
    }

    context.showSearchPane();
    context.setRecentModeActive(false);
    document.title = "Search | dotlineform";

    if (!state.searchLoaded) {
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

    var matches = collectSearchMatches(state.searchEntries, query);
    if (!matches.length) {
      setResultsStatus("No results.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    var visible = matches.slice(0, state.searchVisibleCount);
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
        context.cancelSearchDebounce();
        var activeDocId = state.selectedDocId || context.resolveDocId().docId || context.defaultDocId();
        state.searchQuery = "";
        state.searchRouteActive = false;
        state.searchVisibleCount = context.searchBatchSize;
        if (searchInput) {
          searchInput.value = "";
        }
        if (activeDocId) {
          context.setHistory(activeDocId, "", "", "push");
        }
        renderRecentMode();
      });
    }

    if (!searchControlsAvailable()) return;

    more.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-role='more']");
      if (!button) return;
      state.searchVisibleCount += context.searchBatchSize;
      renderSearchMode();
    });

    searchInput.addEventListener("input", function () {
      var nextQuery = String(searchInput.value || "").trim();
      var nextModeActive = Boolean(normalizeSearchText(nextQuery));
      var previousModeActive = state.searchRouteActive;
      var activeDocId = state.selectedDocId || context.resolveDocId().docId || "";

      context.cancelSearchDebounce();
      context.setRecentModeActive(false);
      state.searchQuery = nextQuery;
      state.searchVisibleCount = context.searchBatchSize;

      if (!activeDocId) {
        return;
      }

      if (!nextModeActive) {
        state.searchRouteActive = false;
        context.setHistory(activeDocId, "", "", previousModeActive ? "replace" : "none");
        context.applyCurrentRoute({ historyMode: "none", hash: "" });
        return;
      }

      state.searchRouteActive = true;
      context.setHistory(activeDocId, "", nextQuery, previousModeActive ? "replace" : "push");
      renderSearchPendingState();
      state.searchDebounceId = window.setTimeout(function () {
        state.searchDebounceId = null;
        context.applyCurrentRoute({ historyMode: "none", hash: "" });
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
