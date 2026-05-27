import {
  bookmarkKey,
  compareBookmarks,
  deleteBookmarkRecord,
  isoNow,
  loadBookmarks,
  normalizeBookmarkRecord,
  persistBookmark
} from "./docs-viewer-favourites.js";
import {
  renderBookmarkRowsMarkup
} from "./docs-viewer-render.js";

export function createDocsViewerBookmarkRouteCallbacks(context) {
  var settings = context || {};
  var routeWorkflow = settings.routeWorkflow;
  return {
    cancelSearchDebounce: function () {
      if (typeof settings.cancelSearchDebounce === "function") settings.cancelSearchDebounce();
    },
    loadDoc: function (docId, options) {
      return routeWorkflow.loadDoc(docId, options);
    }
  };
}

export function initDocsViewerBookmarks(context) {
  var state = context.state;
  var bookmarkRow = context.bookmarkRow;
  var bookmarkToggle = context.bookmarkToggle;
  var routeCallbacks = context.routeCallbacks || {};

  function bookmarkScope() {
    return context.bookmarkScope();
  }

  function getScopeBookmarks() {
    var scope = bookmarkScope();
    return state.bookmarks
      .filter(function (record) { return record.scope === scope; })
      .sort(compareBookmarks);
  }

  function getBookmarkForDoc(docId) {
    return findBookmarkByKey(bookmarkKey(bookmarkScope(), docId));
  }

  function findBookmarkByKey(key) {
    for (var i = 0; i < state.bookmarks.length; i += 1) {
      if (state.bookmarks[i].key === key) return state.bookmarks[i];
    }
    return null;
  }

  function nextBookmarkOrder() {
    var bookmarks = getScopeBookmarks();
    if (!bookmarks.length) return 1;
    return bookmarks[bookmarks.length - 1].order + 1;
  }

  function defaultBookmarkLabel(doc) {
    if (!doc) return "";
    return String(doc.title || doc.doc_id || "").trim();
  }

  function upsertBookmarkState(record) {
    var normalized = normalizeBookmarkRecord(record);
    if (!normalized) return;
    var next = [];
    var found = false;
    state.bookmarks.forEach(function (entry) {
      if (entry.key === normalized.key) {
        next.push(normalized);
        found = true;
      } else {
        next.push(entry);
      }
    });
    if (!found) next.push(normalized);
    state.bookmarks = next.sort(compareBookmarks);
  }

  function removeBookmarkState(key) {
    state.bookmarks = state.bookmarks.filter(function (entry) {
      return entry.key !== key;
    });
    if (state.editingBookmarkKey === key) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
    }
  }

  function renderUi() {
    renderToggle();
    renderRow();
    context.renderStatusPills();
  }

  function renderToggle() {
    if (!bookmarkToggle) return;
    var doc = state.docsById.get(state.selectedDocId);
    var canShow = Boolean(doc) && state.bookmarksLoaded && state.bookmarkSupport && !state.searchRouteActive;
    bookmarkToggle.hidden = !canShow;
    if (!canShow) return;

    var record = getBookmarkForDoc(doc.doc_id);
    var active = Boolean(record);
    bookmarkToggle.classList.toggle("is-active", active);
    bookmarkToggle.textContent = active ? "★" : "☆";
    bookmarkToggle.setAttribute("aria-pressed", active ? "true" : "false");
    bookmarkToggle.setAttribute("aria-label", active ? "Remove bookmark" : "Add bookmark");
    bookmarkToggle.title = active ? "Remove bookmark" : "Add bookmark";
  }

  function renderRow() {
    if (!bookmarkRow) return;
    if (!state.bookmarksLoaded || !state.bookmarkSupport) {
      bookmarkRow.hidden = true;
      bookmarkRow.innerHTML = "";
      return;
    }

    var bookmarks = getScopeBookmarks();
    if (!bookmarks.length) {
      bookmarkRow.hidden = true;
      bookmarkRow.innerHTML = "";
      return;
    }

    bookmarkRow.hidden = false;
    bookmarkRow.innerHTML = renderBookmarkRowsMarkup(bookmarks, {
      editingBookmarkKey: state.editingBookmarkKey,
      selectedDocId: state.selectedDocId
    });

    if (state.pendingBookmarkFocusKey) {
      var focusTarget = bookmarkRow.querySelector('[data-bookmark-input="' + context.cssEscape(state.pendingBookmarkFocusKey) + '"]');
      if (focusTarget) {
        window.requestAnimationFrame(function () {
          focusTarget.focus();
          focusTarget.select();
        });
      }
      state.pendingBookmarkFocusKey = "";
    }
  }

  function bookmarkStorageOptions() {
    return {
      indexedDB: window.indexedDB,
      dbName: context.dbName,
      dbVersion: context.dbVersion,
      storeName: context.storeName
    };
  }

  function handleBookmarkStorageError(error) {
    if (error && error.bookmarkStorageUnavailable) {
      state.bookmarkSupport = false;
      renderUi();
    }
    return error;
  }

  function initialize() {
    if (!state.bookmarkSupport) {
      state.bookmarksLoaded = true;
      renderUi();
      return;
    }

    loadBookmarks(bookmarkStorageOptions())
      .then(function (records) {
        state.bookmarks = records;
        state.bookmarksLoaded = true;
        renderUi();
      })
      .catch(function (error) {
        handleBookmarkStorageError(error);
        state.bookmarks = [];
        state.bookmarksLoaded = true;
        renderUi();
      });
  }

  function addBookmarkForDoc(doc) {
    if (!doc || !state.bookmarkSupport) return;
    var now = isoNow();
    var label = defaultBookmarkLabel(doc);
    var record = normalizeBookmarkRecord({
      scope: bookmarkScope(),
      doc_id: doc.doc_id,
      label: label,
      default_title: label,
      created_at_utc: now,
      updated_at_utc: now,
      order: nextBookmarkOrder()
    });
    upsertBookmarkState(record);
    renderUi();
    persistBookmark(record, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      removeBookmarkState(record.key);
      renderUi();
      context.setStatus(error.message || "Failed to save bookmark.", true);
    });
  }

  function removeBookmarkByKey(key) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) return;
    removeBookmarkState(key);
    renderUi();
    deleteBookmarkRecord(key, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      upsertBookmarkState(record);
      renderUi();
      context.setStatus(error.message || "Failed to remove bookmark.", true);
    });
  }

  function toggleCurrentBookmark() {
    var doc = state.docsById.get(state.selectedDocId);
    if (!doc || !state.bookmarksLoaded || !state.bookmarkSupport) return;
    var existing = getBookmarkForDoc(doc.doc_id);
    if (existing) {
      removeBookmarkByKey(existing.key);
      return;
    }
    addBookmarkForDoc(doc);
  }

  function startRename(key) {
    if (!key) return;
    state.editingBookmarkKey = key;
    state.pendingBookmarkFocusKey = key;
    renderRow();
  }

  function finishRename(key, nextValue, cancel) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderRow();
      return;
    }

    if (cancel) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderRow();
      return;
    }

    var nextLabel = String(nextValue || "").trim() || record.default_title || record.doc_id;
    state.editingBookmarkKey = "";
    state.pendingBookmarkFocusKey = "";
    if (nextLabel === record.label) {
      renderRow();
      return;
    }

    var updated = normalizeBookmarkRecord({
      key: record.key,
      scope: record.scope,
      doc_id: record.doc_id,
      label: nextLabel,
      default_title: record.default_title,
      created_at_utc: record.created_at_utc,
      updated_at_utc: isoNow(),
      order: record.order
    });

    upsertBookmarkState(updated);
    renderUi();
    persistBookmark(updated, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      upsertBookmarkState(record);
      renderUi();
      context.setStatus(error.message || "Failed to rename bookmark.", true);
    });
  }

  function commitInput(input, cancel) {
    if (!input || input.dataset.bookmarkCommitted === "true") return;
    input.dataset.bookmarkCommitted = "true";
    finishRename(input.dataset.bookmarkInput, input.value, cancel);
  }

  function cancelSearchDebounce() {
    var callback = routeCallbacks.cancelSearchDebounce || context.cancelSearchDebounce;
    if (typeof callback === "function") callback();
  }

  function loadDoc(docId, options) {
    var callback = routeCallbacks.loadDoc || context.loadDoc;
    if (typeof callback === "function") return callback(docId, options);
    return null;
  }

  function openBookmark(docId) {
    if (!docId) return;
    cancelSearchDebounce();
    state.searchQuery = "";
    state.searchVisibleCount = context.searchBatchSize;
    if (context.searchInput) context.searchInput.value = "";
    loadDoc(docId, { historyMode: "push", hash: "" });
  }

  function bind() {
    if (bookmarkToggle) {
      bookmarkToggle.addEventListener("click", function () {
        context.hideContextMenu();
        toggleCurrentBookmark();
      });
    }
    if (!bookmarkRow) return;

    bookmarkRow.addEventListener("click", function (event) {
      var removeButton = event.target.closest("[data-bookmark-remove]");
      if (removeButton) {
        event.preventDefault();
        removeBookmarkByKey(removeButton.dataset.bookmarkRemove);
        return;
      }

      var openButton = event.target.closest("[data-bookmark-open]");
      if (openButton) {
        event.preventDefault();
        openBookmark(openButton.dataset.bookmarkOpen);
      }
    });

    bookmarkRow.addEventListener("contextmenu", function (event) {
      var openButton = event.target.closest("[data-bookmark-open]");
      if (!openButton) return;
      event.preventDefault();
      startRename(bookmarkKey(bookmarkScope(), openButton.dataset.bookmarkOpen));
    });

    bookmarkRow.addEventListener("keydown", function (event) {
      var openButton = event.target.closest("[data-bookmark-open]");
      if (openButton && event.key === "F2") {
        event.preventDefault();
        startRename(bookmarkKey(bookmarkScope(), openButton.dataset.bookmarkOpen));
        return;
      }

      var input = event.target.closest("[data-bookmark-input]");
      if (!input) return;
      if (event.key === "Enter") {
        event.preventDefault();
        commitInput(input, false);
      } else if (event.key === "Escape") {
        event.preventDefault();
        commitInput(input, true);
      }
    });

    bookmarkRow.addEventListener("focusout", function (event) {
      var input = event.target.closest("[data-bookmark-input]");
      if (!input) return;
      commitInput(input, false);
    });
  }

  return {
    bind: bind,
    initialize: initialize,
    renderToggle: renderToggle,
    renderUi: renderUi
  };
}
