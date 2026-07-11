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

export function createDocsViewerBookmarkRouteCommands(context) {
  var settings = context || {};
  var routeCommands = settings.routeCommands || {};
  return {
    loadDoc: function (docId, options) {
      return typeof routeCommands.loadDoc === "function" ? routeCommands.loadDoc(docId, options) : null;
    }
  };
}

export function initDocsViewerBookmarks(context) {
  var bookmarkState = context.bookmarks;
  var documentIndex = context.documentIndex;
  var selectedDocument = context.selectedDocument;
  var searchRecent = context.searchRecent;
  var bookmarkRow = context.bookmarkRow;
  var bookmarkToggle = context.bookmarkToggle;
  var routeCommands = context.routeCommands || {};
  var searchResetCommand = context.searchResetCommand || {};

  function bookmarkScope() {
    return context.bookmarkScope();
  }

  function getScopeBookmarks() {
    var scope = bookmarkScope();
    return bookmarkState.bookmarks
      .filter(function (record) { return record.scope === scope; })
      .sort(compareBookmarks);
  }

  function getBookmarkForDoc(docId) {
    return findBookmarkByKey(bookmarkKey(bookmarkScope(), docId));
  }

  function findBookmarkByKey(key) {
    for (var i = 0; i < bookmarkState.bookmarks.length; i += 1) {
      if (bookmarkState.bookmarks[i].key === key) return bookmarkState.bookmarks[i];
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
    bookmarkState.bookmarks.forEach(function (entry) {
      if (entry.key === normalized.key) {
        next.push(normalized);
        found = true;
      } else {
        next.push(entry);
      }
    });
    if (!found) next.push(normalized);
    bookmarkState.bookmarks = next.sort(compareBookmarks);
  }

  function removeBookmarkState(key) {
    bookmarkState.bookmarks = bookmarkState.bookmarks.filter(function (entry) {
      return entry.key !== key;
    });
    if (bookmarkState.editingBookmarkKey === key) {
      bookmarkState.editingBookmarkKey = "";
      bookmarkState.pendingBookmarkFocusKey = "";
    }
  }

  function renderUi() {
    renderToggle();
    renderRow();
  }

  function renderToggle() {
    if (!bookmarkToggle) return;
    var doc = documentIndex.docsById.get(selectedDocument.selectedDocId);
    var eligible = typeof context.controlActive !== "function" || context.controlActive("bookmark");
    var canShow = eligible && Boolean(doc) && bookmarkState.bookmarksLoaded && bookmarkState.bookmarkSupport && !searchRecent.searchRouteActive;
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
    if (!bookmarkState.bookmarksLoaded || !bookmarkState.bookmarkSupport) {
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
      editingBookmarkKey: bookmarkState.editingBookmarkKey,
      selectedDocId: selectedDocument.selectedDocId
    });

    if (bookmarkState.pendingBookmarkFocusKey) {
      var focusTarget = bookmarkRow.querySelector('[data-bookmark-input="' + context.cssEscape(bookmarkState.pendingBookmarkFocusKey) + '"]');
      if (focusTarget) {
        window.requestAnimationFrame(function () {
          focusTarget.focus();
          focusTarget.select();
        });
      }
      bookmarkState.pendingBookmarkFocusKey = "";
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
      bookmarkState.bookmarkSupport = false;
      renderUi();
    }
    return error;
  }

  function initialize() {
    if (!bookmarkState.bookmarkSupport) {
      bookmarkState.bookmarksLoaded = true;
      renderUi();
      return;
    }

    loadBookmarks(bookmarkStorageOptions())
      .then(function (records) {
        bookmarkState.bookmarks = records;
        bookmarkState.bookmarksLoaded = true;
        renderUi();
      })
      .catch(function (error) {
        handleBookmarkStorageError(error);
        bookmarkState.bookmarks = [];
        bookmarkState.bookmarksLoaded = true;
        renderUi();
      });
  }

  function addBookmarkForDoc(doc) {
    if (!doc || !bookmarkState.bookmarkSupport) return;
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
    var doc = documentIndex.docsById.get(selectedDocument.selectedDocId);
    if (!doc || !bookmarkState.bookmarksLoaded || !bookmarkState.bookmarkSupport) return;
    var existing = getBookmarkForDoc(doc.doc_id);
    if (existing) {
      removeBookmarkByKey(existing.key);
      return;
    }
    addBookmarkForDoc(doc);
  }

  function startRename(key) {
    if (!key) return;
    bookmarkState.editingBookmarkKey = key;
    bookmarkState.pendingBookmarkFocusKey = key;
    renderRow();
  }

  function finishRename(key, nextValue, cancel) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) {
      bookmarkState.editingBookmarkKey = "";
      bookmarkState.pendingBookmarkFocusKey = "";
      renderRow();
      return;
    }

    if (cancel) {
      bookmarkState.editingBookmarkKey = "";
      bookmarkState.pendingBookmarkFocusKey = "";
      renderRow();
      return;
    }

    var nextLabel = String(nextValue || "").trim() || record.default_title || record.doc_id;
    bookmarkState.editingBookmarkKey = "";
    bookmarkState.pendingBookmarkFocusKey = "";
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

  function loadDoc(docId, options) {
    var callback = routeCommands.loadDoc;
    if (typeof callback === "function") return callback(docId, options);
    return null;
  }

  function resetSearchForBookmarkOpen() {
    var callback = searchResetCommand.resetForBookmarkOpen;
    if (typeof callback === "function") callback();
  }

  function openBookmark(docId) {
    if (!docId) return;
    resetSearchForBookmarkOpen();
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
