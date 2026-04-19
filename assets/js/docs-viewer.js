(function () {
  var root = document.getElementById("docsViewerRoot");
  if (!root) return;

  var nav = document.getElementById("docsViewerNav");
  var status = document.getElementById("docsViewerStatus");
  var meta = document.getElementById("docsViewerMeta");
  var pathEl = document.getElementById("docsViewerPath");
  var updatedEl = document.getElementById("docsViewerUpdated");
  var bookmarkRow = document.getElementById("docsViewerBookmarkRow");
  var bookmarkToggle = document.getElementById("docsViewerBookmarkToggle");
  var content = document.getElementById("docsViewerContent");
  var searchInput = document.getElementById("docsViewerSearchInput");
  var results = document.getElementById("docsViewerResults");
  var more = document.getElementById("docsViewerMore");
  var manageRow = document.getElementById("docsViewerManageRow");
  var manageActions = manageRow ? manageRow.querySelector(".docsViewer__manageActions") : null;
  var manageNote = document.getElementById("docsViewerManageNote");
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var manageArchiveButton = document.getElementById("docsViewerManageArchiveButton");
  var manageDeleteButton = document.getElementById("docsViewerManageDeleteButton");

  var indexUrl = appendAssetVersion(root.dataset.indexUrl);
  var viewerBaseUrl = root.dataset.viewerBaseUrl || "/docs/";
  var viewerScope = String(root.dataset.viewerScope || "").trim();
  var includeScopeParam = root.dataset.includeScopeParam === "true";
  var defaultRouteDocId = String(root.dataset.defaultDocId || "").trim();
  var viewerPathname = new URL(viewerBaseUrl, window.location.origin).pathname;
  var searchIndexUrl = appendAssetVersion(root.dataset.searchIndexUrl);
  var searchEnabled = Boolean(searchInput && results && more && searchIndexUrl);
  var managementBaseUrl = String(root.dataset.managementBaseUrl || "").trim().replace(/\/+$/, "");
  var SEARCH_BATCH_SIZE = 50;
  var SEARCH_DEBOUNCE_MS = 140;
  var BOOKMARK_DB_NAME = "dotlineform-docs-viewer";
  var BOOKMARK_DB_VERSION = 1;
  var BOOKMARK_STORE_NAME = "favorites";
  var MANAGEMENT_MODE = "manage";
  var RELOAD_RETRY_ATTEMPTS = 12;
  var RELOAD_RETRY_DELAY_MS = 250;
  var bookmarkScope = viewerScope || viewerPathname || "docs";

  var state = {
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    payloadCache: new Map(),
    selectedDocId: "",
    expandedDocIds: new Set(),
    requestId: 0,
    searchEntries: [],
    searchLoaded: false,
    searchRequestPromise: null,
    searchQuery: "",
    searchVisibleCount: SEARCH_BATCH_SIZE,
    searchDebounceId: null,
    searchRouteActive: false,
    bookmarks: [],
    bookmarksLoaded: false,
    bookmarkDbPromise: null,
    bookmarkSupport: Boolean(window.indexedDB),
    editingBookmarkKey: "",
    pendingBookmarkFocusKey: "",
    managementMode: false,
    managementChecked: false,
    managementAvailable: false,
    managementBusy: false,
    managementCapabilities: null,
    managementMessage: "",
    managementMessageIsError: false,
    reloadNonce: "",
    reloadExpectedDocId: "",
    dragDocId: "",
    dropTargetDocId: "",
    dropPosition: ""
  };

  function sortKey(doc) {
    return [
      doc.sort_order == null ? 1 : 0,
      doc.sort_order == null ? 0 : doc.sort_order,
      String(doc.title || "").toLowerCase(),
      String(doc.doc_id || "")
    ];
  }

  function compareDocs(left, right) {
    var leftKey = sortKey(left);
    var rightKey = sortKey(right);
    for (var i = 0; i < leftKey.length; i += 1) {
      if (leftKey[i] < rightKey[i]) return -1;
      if (leftKey[i] > rightKey[i]) return 1;
    }
    return 0;
  }

  function getCurrentDocId() {
    return new URLSearchParams(window.location.search).get("doc") || "";
  }

  function getCurrentHash() {
    return window.location.hash ? window.location.hash.slice(1) : "";
  }

  function getCurrentQuery() {
    return (new URLSearchParams(window.location.search).get("q") || "").trim();
  }

  function getCurrentMode() {
    return new URLSearchParams(window.location.search).get("mode") || "";
  }

  function hasCanonicalScopeInUrl() {
    if (!includeScopeParam || !viewerScope) return true;
    return new URLSearchParams(window.location.search).get("scope") === viewerScope;
  }

  function hasActiveQuery(query) {
    return Boolean(normalize(typeof query === "string" ? query : state.searchQuery));
  }

  function bookmarkKey(scope, docId) {
    return String(scope || "") + "::" + String(docId || "");
  }

  function isoNow() {
    return new Date().toISOString();
  }

  function compareBookmarks(left, right) {
    var leftOrder = typeof left.order === "number" ? left.order : 0;
    var rightOrder = typeof right.order === "number" ? right.order : 0;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return String(left.created_at_utc || "").localeCompare(String(right.created_at_utc || ""));
  }

  function normalizeBookmarkRecord(record) {
    if (!record || typeof record !== "object") return null;
    var scope = String(record.scope || "").trim();
    var docId = String(record.doc_id || "").trim();
    if (!scope || !docId) return null;
    var defaultTitle = String(record.default_title || record.label || docId).trim() || docId;
    return {
      key: bookmarkKey(scope, docId),
      scope: scope,
      doc_id: docId,
      label: String(record.label || defaultTitle).trim() || defaultTitle,
      default_title: defaultTitle,
      created_at_utc: String(record.created_at_utc || record.updated_at_utc || isoNow()),
      updated_at_utc: String(record.updated_at_utc || record.created_at_utc || isoNow()),
      order: typeof record.order === "number" ? record.order : 0
    };
  }

  function getScopeBookmarks() {
    return state.bookmarks
      .filter(function (record) { return record.scope === bookmarkScope; })
      .sort(compareBookmarks);
  }

  function getBookmarkForDoc(docId) {
    return findBookmarkByKey(bookmarkKey(bookmarkScope, docId));
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
    if (!found) {
      next.push(normalized);
    }
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

  function renderBookmarkUi() {
    renderBookmarkToggle();
    renderBookmarkRow();
  }

  function renderBookmarkToggle() {
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

  function renderBookmarkRow() {
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
    bookmarkRow.innerHTML = bookmarks.map(function (record) {
      var isActive = record.doc_id === state.selectedDocId;
      var isEditing = record.key === state.editingBookmarkKey;
      var pillClass = "docsViewer__bookmarkPill" + (isActive ? " is-active" : "");
      if (isEditing) {
        return (
          '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
            '<input class="docsViewer__bookmarkInput" type="text" value="' + escapeHtml(record.label || record.default_title || record.doc_id) + '" data-bookmark-input="' + escapeHtml(record.key) + '" aria-label="Rename bookmark">' +
            '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
          '</div>'
        );
      }
      return (
        '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
          '<button type="button" class="docsViewer__bookmarkOpen" data-bookmark-open="' + escapeHtml(record.doc_id) + '" title="Open bookmark. Right-click to rename." aria-current="' + (isActive ? "page" : "false") + '">' +
            '<span class="docsViewer__bookmarkLabel">' + escapeHtml(record.label || record.default_title || record.doc_id) + '</span>' +
          '</button>' +
          '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
        '</div>'
      );
    }).join("");

    if (state.pendingBookmarkFocusKey) {
      var focusTarget = bookmarkRow.querySelector('[data-bookmark-input="' + cssEscape(state.pendingBookmarkFocusKey) + '"]');
      if (focusTarget) {
        window.requestAnimationFrame(function () {
          focusTarget.focus();
          focusTarget.select();
        });
      }
      state.pendingBookmarkFocusKey = "";
    }
  }

  function openBookmarksDb() {
    if (!state.bookmarkSupport) {
      return Promise.reject(new Error("Bookmarks unavailable in this browser."));
    }
    if (state.bookmarkDbPromise) {
      return state.bookmarkDbPromise;
    }

    state.bookmarkDbPromise = new Promise(function (resolve, reject) {
      var request = window.indexedDB.open(BOOKMARK_DB_NAME, BOOKMARK_DB_VERSION);

      request.onupgradeneeded = function () {
        var db = request.result;
        if (!db.objectStoreNames.contains(BOOKMARK_STORE_NAME)) {
          db.createObjectStore(BOOKMARK_STORE_NAME, { keyPath: "key" });
        }
      };

      request.onsuccess = function () {
        var db = request.result;
        db.onversionchange = function () {
          db.close();
          state.bookmarkDbPromise = null;
        };
        resolve(db);
      };

      request.onerror = function () {
        reject(request.error || new Error("Failed to open bookmark storage."));
      };
    }).catch(function (error) {
      state.bookmarkSupport = false;
      renderBookmarkUi();
      throw error;
    });

    return state.bookmarkDbPromise;
  }

  function loadBookmarks() {
    return openBookmarksDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(BOOKMARK_STORE_NAME, "readonly");
        var store = tx.objectStore(BOOKMARK_STORE_NAME);
        var request = store.getAll();
        request.onsuccess = function () {
          var records = Array.isArray(request.result) ? request.result.map(normalizeBookmarkRecord).filter(Boolean) : [];
          resolve(records);
        };
        request.onerror = function () {
          reject(request.error || new Error("Failed to load bookmarks."));
        };
      });
    });
  }

  function persistBookmark(record) {
    return openBookmarksDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(BOOKMARK_STORE_NAME, "readwrite");
        tx.oncomplete = function () { resolve(record); };
        tx.onerror = function () { reject(tx.error || new Error("Failed to save bookmark.")); };
        tx.objectStore(BOOKMARK_STORE_NAME).put(record);
      });
    });
  }

  function deleteBookmarkRecord(key) {
    return openBookmarksDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(BOOKMARK_STORE_NAME, "readwrite");
        tx.oncomplete = function () { resolve(); };
        tx.onerror = function () { reject(tx.error || new Error("Failed to remove bookmark.")); };
        tx.objectStore(BOOKMARK_STORE_NAME).delete(key);
      });
    });
  }

  function initializeBookmarks() {
    if (!state.bookmarkSupport) {
      state.bookmarksLoaded = true;
      renderBookmarkUi();
      return;
    }

    loadBookmarks()
      .then(function (records) {
        state.bookmarks = records;
        state.bookmarksLoaded = true;
        renderBookmarkUi();
      })
      .catch(function () {
        state.bookmarks = [];
        state.bookmarksLoaded = true;
        renderBookmarkUi();
      });
  }

  function addBookmarkForDoc(doc) {
    if (!doc || !state.bookmarkSupport) return;
    var now = isoNow();
    var record = normalizeBookmarkRecord({
      scope: bookmarkScope,
      doc_id: doc.doc_id,
      label: defaultBookmarkLabel(doc),
      default_title: defaultBookmarkLabel(doc),
      created_at_utc: now,
      updated_at_utc: now,
      order: nextBookmarkOrder()
    });
    upsertBookmarkState(record);
    renderBookmarkUi();
    persistBookmark(record).catch(function (error) {
      removeBookmarkState(record.key);
      renderBookmarkUi();
      setStatus(error.message || "Failed to save bookmark.", true);
    });
  }

  function removeBookmarkByKey(key) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) return;
    removeBookmarkState(key);
    renderBookmarkUi();
    deleteBookmarkRecord(key).catch(function (error) {
      upsertBookmarkState(record);
      renderBookmarkUi();
      setStatus(error.message || "Failed to remove bookmark.", true);
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

  function startBookmarkRename(key) {
    if (!key) return;
    state.editingBookmarkKey = key;
    state.pendingBookmarkFocusKey = key;
    renderBookmarkRow();
  }

  function finishBookmarkRename(key, nextValue, cancel) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderBookmarkRow();
      return;
    }

    if (cancel) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderBookmarkRow();
      return;
    }

    var nextLabel = String(nextValue || "").trim() || record.default_title || record.doc_id;
    state.editingBookmarkKey = "";
    state.pendingBookmarkFocusKey = "";
    if (nextLabel === record.label) {
      renderBookmarkRow();
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
    renderBookmarkUi();
    persistBookmark(updated).catch(function (error) {
      upsertBookmarkState(record);
      renderBookmarkUi();
      setStatus(error.message || "Failed to rename bookmark.", true);
    });
  }

  function viewerUrl(docId, hash, query) {
    var url = new URL(viewerBaseUrl, window.location.origin);
    if (includeScopeParam && viewerScope) {
      url.searchParams.set("scope", viewerScope);
    }
    if (state.managementMode) {
      url.searchParams.set("mode", MANAGEMENT_MODE);
    }
    url.searchParams.set("doc", docId);
    if (typeof query === "string" && query.trim()) {
      url.searchParams.set("q", query.trim());
    }
    url.hash = hash || "";
    return url.pathname + url.search + url.hash;
  }

  function buildChildrenMap(docs) {
    var childrenByParent = new Map();
    docs.forEach(function (doc) {
      var parentId = doc.parent_id || "";
      if (!childrenByParent.has(parentId)) {
        childrenByParent.set(parentId, []);
      }
      childrenByParent.get(parentId).push(doc);
    });
    childrenByParent.forEach(function (group) {
      group.sort(compareDocs);
    });
    return childrenByParent;
  }

  function flattenRoots() {
    var roots = state.childrenByParent.get("") || [];
    if (roots.length > 0) return roots;
    return state.docs.slice().sort(compareDocs);
  }

  function defaultDocId() {
    var roots = flattenRoots();
    return roots.length > 0 ? roots[0].doc_id : "";
  }

  function buildTrail(docId) {
    var trail = [];
    var current = state.docsById.get(docId);
    while (current) {
      trail.unshift(current);
      current = current.parent_id ? state.docsById.get(current.parent_id) : null;
    }
    return trail;
  }

  function expandTrail(docId) {
    buildTrail(docId).forEach(function (doc) {
      if ((state.childrenByParent.get(doc.doc_id) || []).length > 0) {
        state.expandedDocIds.add(doc.doc_id);
      }
    });
  }

  function renderSidebar() {
    nav.textContent = "";
    if (state.docs.length === 0) {
      return;
    }

    nav.appendChild(renderNavList(""));
    updateNavDragState();
  }

  function renderNavList(parentId) {
    var list = document.createElement("ul");
    list.className = parentId ? "docsViewer__navList docsViewer__navList--child" : "docsViewer__navList";

    var docs = state.childrenByParent.get(parentId) || [];
    docs.forEach(function (doc) {
      var item = document.createElement("li");
      item.className = "docsViewer__navItem";
      var row = document.createElement("div");
      row.className = "docsViewer__navRow";
      row.dataset.docRowId = doc.doc_id;
      var children = docChildren(doc.doc_id);
      var hasChildren = children.length > 0;

      if (hasChildren) {
        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "docsViewer__toggle";
        toggle.dataset.toggleDocId = doc.doc_id;
        toggle.setAttribute("aria-expanded", state.expandedDocIds.has(doc.doc_id) ? "true" : "false");
        toggle.setAttribute("aria-label", state.expandedDocIds.has(doc.doc_id) ? "Collapse section" : "Expand section");
        toggle.textContent = state.expandedDocIds.has(doc.doc_id) ? "▼" : "►";
        row.appendChild(toggle);
      } else {
        var spacer = document.createElement("span");
        spacer.className = "docsViewer__toggleSpacer";
        spacer.setAttribute("aria-hidden", "true");
        spacer.textContent = "";
        row.appendChild(spacer);
      }

      var link = document.createElement("a");
      link.className = "docsViewer__navLink";
      if (doc.doc_id === state.selectedDocId) {
        link.className += " is-active";
        link.setAttribute("aria-current", "page");
      }
      link.href = viewerUrl(doc.doc_id);
      link.dataset.docId = doc.doc_id;
      if (canDragDoc(doc)) {
        link.draggable = true;
        link.dataset.dragDocId = doc.doc_id;
      }
      link.textContent = doc.title;
      row.appendChild(link);
      item.appendChild(row);

      if (hasChildren && state.expandedDocIds.has(doc.doc_id)) {
        item.appendChild(renderNavList(doc.doc_id));
      }

      list.appendChild(item);
    });

    return list;
  }

  function renderMeta(doc) {
    var trail = buildTrail(doc.doc_id);
    pathEl.textContent = "";

    trail.forEach(function (entry, index) {
      if (index > 0) {
        var separator = document.createElement("span");
        separator.className = "docsViewer__pathSep";
        separator.textContent = "/";
        pathEl.appendChild(separator);
      }

      if (index === trail.length - 1) {
        var current = document.createElement("span");
        current.textContent = entry.title;
        pathEl.appendChild(current);
        return;
      }

      var link = document.createElement("a");
      link.href = viewerUrl(entry.doc_id);
      link.dataset.docId = entry.doc_id;
      link.textContent = entry.title;
      pathEl.appendChild(link);
    });

    if (doc.last_updated) {
      updatedEl.textContent = "Updated " + doc.last_updated;
      updatedEl.hidden = false;
    } else {
      updatedEl.textContent = "";
      updatedEl.hidden = true;
    }
    meta.hidden = false;
    renderBookmarkToggle();
  }

  function setStatus(message, isError) {
    status.textContent = message;
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function setManagementMessage(message, isError) {
    state.managementMessage = String(message || "");
    state.managementMessageIsError = Boolean(isError);
    renderManagementUi();
  }

  function scopeManagementCapabilities() {
    if (!state.managementCapabilities || !state.managementCapabilities.scopes) return null;
    return state.managementCapabilities.scopes[viewerScope] || null;
  }

  function currentSelectedDoc() {
    return state.docsById.get(state.selectedDocId) || null;
  }

  function docChildren(docId) {
    return state.childrenByParent.get(docId) || [];
  }

  function docHasChildren(docId) {
    return docChildren(docId).length > 0;
  }

  function managementDragEnabled() {
    return state.managementMode && state.managementAvailable && !state.managementBusy && !state.searchRouteActive;
  }

  function canDragDoc(doc) {
    if (!managementDragEnabled() || !doc) return false;
    if (doc.doc_id === "_archive") return false;
    return !docHasChildren(doc.doc_id);
  }

  function dropPositionForDoc(docId) {
    if (!managementDragEnabled()) return "";
    if (!docId || !state.docsById.has(docId)) return "";
    if (state.dragDocId === docId) return "";
    if (docHasChildren(docId) && !state.expandedDocIds.has(docId)) {
      return "inside";
    }
    return "after";
  }

  function canDropOnDoc(docId) {
    if (!state.dragDocId || !managementDragEnabled()) return false;
    var dragDoc = state.docsById.get(state.dragDocId);
    var targetDoc = state.docsById.get(docId);
    if (!dragDoc || !targetDoc) return false;
    if (!canDragDoc(dragDoc)) return false;
    if (dragDoc.doc_id === targetDoc.doc_id) return false;
    return Boolean(dropPositionForDoc(docId));
  }

  function clearDragState() {
    state.dragDocId = "";
    state.dropTargetDocId = "";
    state.dropPosition = "";
    updateNavDragState();
  }

  function updateNavDragState() {
    if (!nav) return;
    nav.querySelectorAll(".docsViewer__navRow").forEach(function (row) {
      row.classList.remove("is-dragging", "is-drop-after", "is-drop-inside");
    });
    if (state.dragDocId) {
      var dragRow = nav.querySelector('[data-doc-row-id="' + cssEscape(state.dragDocId) + '"]');
      if (dragRow) {
        dragRow.classList.add("is-dragging");
      }
    }
    if (state.dropTargetDocId && state.dropPosition) {
      var dropRow = nav.querySelector('[data-doc-row-id="' + cssEscape(state.dropTargetDocId) + '"]');
      if (dropRow) {
        dropRow.classList.add(state.dropPosition === "inside" ? "is-drop-inside" : "is-drop-after");
      }
    }
  }

  function managementArchiveAvailable() {
    var scopeCaps = scopeManagementCapabilities();
    return Boolean(scopeCaps && scopeCaps.archive_available);
  }

  function managementNoteText() {
    if (state.managementMessage) return state.managementMessage;
    if (state.searchRouteActive) {
      return "Clear search to archive or delete the current doc.";
    }
    if (!managementArchiveAvailable()) {
      return "Archive is unavailable for this scope until `_archive` exists.";
    }
    return "Manage mode is local-only and writes through the docs-management server.";
  }

  function renderManagementUi() {
    if (!manageRow) return;

    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    if (!state.managementMode) {
      manageRow.hidden = true;
      return;
    }

    manageRow.hidden = false;
    if (manageActions) {
      manageActions.hidden = !state.managementChecked || !state.managementAvailable;
    }

    if (manageNote) {
      var noteText = "";
      var noteIsError = false;
      if (!state.managementChecked) {
        noteText = "Checking manage mode...";
      } else if (!state.managementAvailable) {
        noteText = "Manage mode unavailable: local docs server unavailable for this scope.";
        noteIsError = true;
      } else {
        noteText = managementNoteText();
        noteIsError = state.managementMessageIsError;
      }
      manageNote.textContent = noteText;
      manageNote.classList.toggle("is-error", noteIsError);
    }

    if (!manageNewButton || !manageArchiveButton || !manageDeleteButton) return;

    var doc = currentSelectedDoc();
    var reserved = Boolean(doc && doc.doc_id === "_archive");
    var archiveDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive ||
      !managementArchiveAvailable() ||
      reserved ||
      doc.parent_id === "_archive"
    );
    var deleteDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive ||
      reserved
    );

    manageNewButton.disabled = state.managementBusy || !state.managementAvailable;
    manageArchiveButton.disabled = !state.managementAvailable || archiveDisabled;
    manageDeleteButton.disabled = !state.managementAvailable || deleteDisabled;
  }

  function fetchManagementJson(path, method, payload) {
    if (!managementBaseUrl) {
      return Promise.reject(new Error("Local docs-management server is not configured."));
    }

    var options = {
      method: method || "GET",
      headers: {
        Accept: "application/json"
      }
    };
    if (payload !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(payload);
    }

    return window.fetch(managementBaseUrl + path, options).then(function (response) {
      return response.json().catch(function () {
        throw new Error("HTTP " + response.status);
      }).then(function (responsePayload) {
        if (!response.ok || !responsePayload || !responsePayload.ok) {
          throw new Error(responsePayload && responsePayload.error ? responsePayload.error : "HTTP " + response.status);
        }
        return responsePayload;
      });
    });
  }

  function initializeManagement() {
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    renderManagementUi();
    if (!state.managementMode) return;

    if (!managementBaseUrl) {
      state.managementChecked = true;
      state.managementAvailable = false;
      renderManagementUi();
      return;
    }

    fetchManagementJson("/capabilities", "GET")
      .then(function (payload) {
        var scopeCaps = payload && payload.capabilities && payload.capabilities.scopes
          ? payload.capabilities.scopes[viewerScope]
          : null;
        state.managementCapabilities = payload.capabilities || null;
        state.managementChecked = true;
        state.managementAvailable = Boolean(scopeCaps && scopeCaps.available);
        renderManagementUi();
      })
      .catch(function () {
        state.managementCapabilities = null;
        state.managementChecked = true;
        state.managementAvailable = false;
        renderManagementUi();
      });
  }

  function reloadDocsIndex(targetDocId, summaryText) {
    state.payloadCache.clear();
    state.searchEntries = [];
    state.searchLoaded = false;
    state.searchRequestPromise = null;
    state.reloadNonce = String(Date.now());
    state.reloadExpectedDocId = String(targetDocId || "").trim();
    state.searchQuery = "";
    state.searchVisibleCount = SEARCH_BATCH_SIZE;
    state.searchRouteActive = false;
    cancelSearchDebounce();
    if (searchInput) {
      searchInput.value = "";
    }

    if (targetDocId) {
      setHistory(targetDocId, "", "", "replace");
    }

    return loadIndex().then(function () {
      setStatus(summaryText ? summaryText : "", false);
      renderManagementUi();
    });
  }

  function handleCreateDoc() {
    var titleInput = window.prompt("New doc title", "New Doc");
    if (titleInput == null) return;

    var title = String(titleInput || "").trim() || "New Doc";
    var currentDoc = currentSelectedDoc();

    state.managementBusy = true;
    setManagementMessage("Creating doc...", false);
    setStatus("Creating doc...", false);

    fetchManagementJson("/docs/create", "POST", {
      scope: viewerScope,
      title: title,
      after_doc_id: currentDoc ? currentDoc.doc_id : ""
    })
      .then(function (payload) {
        setManagementMessage(payload.summary_text || "Doc created.", false);
        return reloadDocsIndex(payload.doc_id, payload.summary_text || "Doc created.");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Create failed.", true);
        setStatus(error.message || "Create failed.", true);
      })
      .finally(function () {
        state.managementBusy = false;
        renderManagementUi();
      });
  }

  function handleArchiveDoc() {
    var doc = currentSelectedDoc();
    if (!doc) return;
    if (!window.confirm("Archive " + doc.title + "?")) return;

    state.managementBusy = true;
    setManagementMessage("Archiving " + doc.title + "...", false);
    setStatus("Archiving " + doc.title + "...", false);

    fetchManagementJson("/docs/archive", "POST", {
      scope: viewerScope,
      doc_id: doc.doc_id
    })
      .then(function (payload) {
        setManagementMessage(payload.summary_text || "Doc archived.", false);
        return reloadDocsIndex(payload.doc_id, payload.summary_text || "Doc archived.");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Archive failed.", true);
        setStatus(error.message || "Archive failed.", true);
      })
      .finally(function () {
        state.managementBusy = false;
        renderManagementUi();
      });
  }

  function buildDeleteConfirmation(preview) {
    var lines = ["Delete " + preview.title + "?"];
    if (Array.isArray(preview.warnings) && preview.warnings.length) {
      lines.push("");
      lines.push("Warnings:");
      preview.warnings.forEach(function (item) {
        lines.push("- " + item);
      });
    }
    if (Array.isArray(preview.inbound_refs) && preview.inbound_refs.length) {
      lines.push("");
      lines.push("Inbound refs:");
      preview.inbound_refs.slice(0, 6).forEach(function (item) {
        lines.push("- " + item.doc_id);
      });
      if (preview.inbound_refs.length > 6) {
        lines.push("- +" + (preview.inbound_refs.length - 6) + " more");
      }
    }
    return lines.join("\n");
  }

  function handleDeleteDoc() {
    var doc = currentSelectedDoc();
    if (!doc) return;

    state.managementBusy = true;
    setManagementMessage("Checking delete impact for " + doc.title + "...", false);
    setStatus("Checking delete impact for " + doc.title + "...", false);

    fetchManagementJson("/docs/delete-preview", "POST", {
      scope: viewerScope,
      doc_id: doc.doc_id
    })
      .then(function (preview) {
        if (!preview.allowed) {
          var blockerText = (preview.blockers || []).join("; ") || "Delete is blocked.";
          setManagementMessage(blockerText, true);
          setStatus(blockerText, true);
          return null;
        }
        if (!window.confirm(buildDeleteConfirmation(preview))) {
          setManagementMessage("", false);
          setStatus("", false);
          return null;
        }
        setManagementMessage("Deleting " + doc.title + "...", false);
        setStatus("Deleting " + doc.title + "...", false);
        return fetchManagementJson("/docs/delete-apply", "POST", {
          scope: viewerScope,
          doc_id: doc.doc_id,
          confirm: true
        });
      })
      .then(function (payload) {
        if (!payload) return;
        var fallbackDocId = doc.parent_id || defaultRouteDocId || defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(fallbackDocId, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Delete failed.", true);
        setStatus(error.message || "Delete failed.", true);
      })
      .finally(function () {
        state.managementBusy = false;
        renderManagementUi();
      });
  }

  function handleMoveDoc(docId, targetDocId, position) {
    if (!docId || !targetDocId || !position) return;
    var movingDoc = state.docsById.get(docId);
    var targetDoc = state.docsById.get(targetDocId);
    if (!movingDoc || !targetDoc) return;

    state.managementBusy = true;
    clearDragState();
    setManagementMessage("Moving " + movingDoc.title + "...", false);
    setStatus("Moving " + movingDoc.title + "...", false);

    fetchManagementJson("/docs/move", "POST", {
      scope: viewerScope,
      doc_id: movingDoc.doc_id,
      target_doc_id: targetDoc.doc_id,
      position: position
    })
      .then(function (payload) {
        setManagementMessage(payload.summary_text || "Doc moved.", false);
        return reloadDocsIndex(movingDoc.doc_id, payload.summary_text || "Doc moved.");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Move failed.", true);
        setStatus(error.message || "Move failed.", true);
      })
      .finally(function () {
        state.managementBusy = false;
        renderManagementUi();
      });
  }

  function scrollToHash(hash) {
    if (!hash) {
      window.scrollTo({ top: 0, behavior: "auto" });
      return;
    }

    var target = document.getElementById(hash);
    if (!target) return;

    target.scrollIntoView({ block: "start", behavior: "auto" });
  }

  function hideDocPane() {
    meta.hidden = true;
    content.hidden = true;
    renderBookmarkToggle();
  }

  function showDocPane() {
    content.hidden = false;
    results.hidden = true;
    more.hidden = true;
    more.innerHTML = "";
  }

  function showSearchPane() {
    hideDocPane();
    results.hidden = false;
  }

  function renderPayload(doc, payload, hash) {
    state.selectedDocId = doc.doc_id;
    renderSidebar();
    renderBookmarkUi();
    renderManagementUi();

    if (hasActiveQuery()) {
      renderSearchMode();
      return;
    }

    showDocPane();
    renderMeta(doc);
    content.innerHTML = payload.content_html || "";
    document.title = doc.title + " | dotlineform";
    setStatus("", false);

    window.requestAnimationFrame(function () {
      scrollToHash(hash);
    });
  }

  function setHistory(docId, hash, query, mode) {
    if (mode === "none") return;

    var nextUrl = viewerUrl(docId, hash, query);
    var nextState = { docId: docId, hash: hash || "", q: query || "" };
    if (mode === "replace") {
      window.history.replaceState(nextState, "", nextUrl);
      return;
    }

    window.history.pushState(nextState, "", nextUrl);
  }

  function cancelSearchDebounce() {
    if (state.searchDebounceId == null) return;
    window.clearTimeout(state.searchDebounceId);
    state.searchDebounceId = null;
  }

  function loadDoc(docId, options) {
    var mode = options && options.historyMode ? options.historyMode : "push";
    var hash = options && options.hash ? options.hash : "";
    var shouldExpandTrail = !options || options.expandTrail !== false;
    var doc = state.docsById.get(docId);
    if (!doc) {
      setStatus("Document not found.", true);
      hideDocPane();
      content.textContent = "";
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      renderManagementUi();
      return;
    }

    state.selectedDocId = docId;
    if (shouldExpandTrail) {
      expandTrail(docId);
    }
    renderBookmarkUi();

    setHistory(docId, hash, "", mode);

    if (state.payloadCache.has(docId)) {
      renderPayload(doc, state.payloadCache.get(docId), hash);
      return;
    }

    renderSidebar();
    showDocPane();
    renderMeta(doc);
    setStatus("Loading " + doc.title + "...", false);
    content.textContent = "";

    var requestId = state.requestId + 1;
    state.requestId = requestId;

    fetchJsonWithRetry(
      doc.content_url,
      "Failed to load " + doc.content_url,
      managementReloadPath("/docs/doc", { scope: viewerScope, doc_id: docId })
    )
      .then(function (payload) {
        if (state.requestId !== requestId) return;
        state.payloadCache.set(docId, payload);
        state.reloadNonce = "";
        state.reloadExpectedDocId = "";
        renderPayload(doc, payload, hash);
      })
      .catch(function (error) {
        if (state.requestId !== requestId) return;
        setStatus(error.message || "Failed to load document.", true);
        content.textContent = "";
      });
  }

  function routeFromAnchor(anchor) {
    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return null;
    if (url.pathname !== viewerPathname) return null;

    var docId = url.searchParams.get("doc");
    if (!docId) return null;

    return {
      docId: docId,
      hash: url.hash ? url.hash.slice(1) : ""
    };
  }

  function bindLinkInterception() {
    if (nav) {
      nav.addEventListener("dragstart", function (event) {
        var dragHandle = event.target.closest("[data-drag-doc-id]");
        if (!dragHandle || !managementDragEnabled()) return;
        state.dragDocId = dragHandle.dataset.dragDocId || "";
        state.dropTargetDocId = "";
        state.dropPosition = "";
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", state.dragDocId);
        }
        updateNavDragState();
      });

      nav.addEventListener("dragover", function (event) {
        var row = event.target.closest("[data-doc-row-id]");
        if (!row) {
          if (state.dropTargetDocId || state.dropPosition) {
            state.dropTargetDocId = "";
            state.dropPosition = "";
            updateNavDragState();
          }
          return;
        }

        var targetDocId = row.dataset.docRowId || "";
        if (!canDropOnDoc(targetDocId)) {
          if (state.dropTargetDocId || state.dropPosition) {
            state.dropTargetDocId = "";
            state.dropPosition = "";
            updateNavDragState();
          }
          return;
        }

        event.preventDefault();
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = "move";
        }
        var nextPosition = dropPositionForDoc(targetDocId);
        if (state.dropTargetDocId !== targetDocId || state.dropPosition !== nextPosition) {
          state.dropTargetDocId = targetDocId;
          state.dropPosition = nextPosition;
          updateNavDragState();
        }
      });

      nav.addEventListener("drop", function (event) {
        var row = event.target.closest("[data-doc-row-id]");
        if (!row) {
          clearDragState();
          return;
        }
        var targetDocId = row.dataset.docRowId || "";
        var position = dropPositionForDoc(targetDocId);
        if (!canDropOnDoc(targetDocId) || !position) {
          clearDragState();
          return;
        }
        event.preventDefault();
        var movingDocId = state.dragDocId;
        clearDragState();
        handleMoveDoc(movingDocId, targetDocId, position);
      });

      nav.addEventListener("dragend", function () {
        clearDragState();
      });
    }

    root.addEventListener("click", function (event) {
      var toggle = event.target.closest("[data-toggle-doc-id]");
      if (toggle) {
        var toggleDocId = toggle.dataset.toggleDocId;
        if (state.expandedDocIds.has(toggleDocId)) {
          state.expandedDocIds.delete(toggleDocId);
        } else {
          state.expandedDocIds.add(toggleDocId);
        }
        renderSidebar();
        return;
      }

      var anchor = event.target.closest("a[href]");
      if (!anchor) return;

      var route = routeFromAnchor(anchor);
      if (!route) return;

      event.preventDefault();
      cancelSearchDebounce();
      state.searchQuery = "";
      state.searchVisibleCount = SEARCH_BATCH_SIZE;
      if (searchInput) {
        searchInput.value = "";
      }
      loadDoc(route.docId, { historyMode: "push", hash: route.hash });
    });

    if (bookmarkToggle) {
      bookmarkToggle.addEventListener("click", function () {
        toggleCurrentBookmark();
      });
    }

    if (bookmarkRow) {
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
          var targetDocId = openButton.dataset.bookmarkOpen;
          if (!targetDocId) return;
          cancelSearchDebounce();
          state.searchQuery = "";
          state.searchVisibleCount = SEARCH_BATCH_SIZE;
          if (searchInput) {
            searchInput.value = "";
          }
          loadDoc(targetDocId, { historyMode: "push", hash: "" });
        }
      });

      bookmarkRow.addEventListener("contextmenu", function (event) {
        var openButton = event.target.closest("[data-bookmark-open]");
        if (!openButton) return;
        event.preventDefault();
        startBookmarkRename(bookmarkKey(bookmarkScope, openButton.dataset.bookmarkOpen));
      });

      bookmarkRow.addEventListener("keydown", function (event) {
        var openButton = event.target.closest("[data-bookmark-open]");
        if (openButton && event.key === "F2") {
          event.preventDefault();
          startBookmarkRename(bookmarkKey(bookmarkScope, openButton.dataset.bookmarkOpen));
          return;
        }

        var input = event.target.closest("[data-bookmark-input]");
        if (!input) return;
        if (event.key === "Enter") {
          event.preventDefault();
          finishBookmarkRename(input.dataset.bookmarkInput, input.value, false);
        } else if (event.key === "Escape") {
          event.preventDefault();
          finishBookmarkRename(input.dataset.bookmarkInput, input.value, true);
        }
      });

      bookmarkRow.addEventListener("focusout", function (event) {
        var input = event.target.closest("[data-bookmark-input]");
        if (!input) return;
        finishBookmarkRename(input.dataset.bookmarkInput, input.value, false);
      });
    }

    if (manageNewButton) {
      manageNewButton.addEventListener("click", function () {
        handleCreateDoc();
      });
    }

    if (manageArchiveButton) {
      manageArchiveButton.addEventListener("click", function () {
        handleArchiveDoc();
      });
    }

    if (manageDeleteButton) {
      manageDeleteButton.addEventListener("click", function () {
        handleDeleteDoc();
      });
    }

    if (searchEnabled) {
      more.addEventListener("click", function (event) {
        var button = event.target.closest("button[data-role='more']");
        if (!button) return;
        state.searchVisibleCount += SEARCH_BATCH_SIZE;
        renderSearchMode();
      });

      searchInput.addEventListener("input", function () {
        var nextQuery = String(searchInput.value || "").trim();
        var nextModeActive = Boolean(normalize(nextQuery));
        var previousModeActive = state.searchRouteActive;
        var activeDocId = state.selectedDocId || resolveDocId().docId || "";

        cancelSearchDebounce();
        state.searchQuery = nextQuery;
        state.searchVisibleCount = SEARCH_BATCH_SIZE;

        if (!activeDocId) {
          return;
        }

        if (!nextModeActive) {
          state.searchRouteActive = false;
          setHistory(activeDocId, "", "", previousModeActive ? "replace" : "none");
          applyCurrentRoute({ historyMode: "none", hash: "" });
          return;
        }

        state.searchRouteActive = true;
        setHistory(activeDocId, "", nextQuery, previousModeActive ? "replace" : "push");
        renderSearchPendingState();
        state.searchDebounceId = window.setTimeout(function () {
          state.searchDebounceId = null;
          applyCurrentRoute({ historyMode: "none", hash: "" });
        }, SEARCH_DEBOUNCE_MS);
      });
    }
  }

  function resolveDocId() {
    var requestedDocId = getCurrentDocId();
    var resolvedDocId = requestedDocId;
    if (!state.docsById.has(resolvedDocId) && defaultRouteDocId && state.docsById.has(defaultRouteDocId)) {
      resolvedDocId = defaultRouteDocId;
    }
    if (!state.docsById.has(resolvedDocId)) {
      resolvedDocId = defaultDocId();
    }
    return {
      requestedDocId: requestedDocId,
      docId: resolvedDocId,
      corrected: resolvedDocId !== requestedDocId
    };
  }

  function initializeIndex(payload) {
    state.docs = Array.isArray(payload.docs) ? payload.docs.slice().sort(compareDocs) : [];
    state.docsById = new Map(
      state.docs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.childrenByParent = buildChildrenMap(state.docs);

    renderSidebar();
    renderBookmarkUi();

    if (state.docs.length === 0) {
      setStatus("No docs available.", true);
      return;
    }

    applyCurrentRoute({ historyMode: "replace", hash: getCurrentHash() });
  }

  function applyCurrentRoute(options) {
    var route = resolveDocId();
    var docId = route.docId;
    if (!docId) {
      setStatus("No docs available.", true);
      return;
    }

    var query = getCurrentQuery();
    state.searchQuery = query;
    state.searchRouteActive = hasActiveQuery(query);
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    state.selectedDocId = docId;
    if (searchInput) {
      searchInput.value = query;
    }

    expandTrail(docId);
    renderSidebar();
    renderBookmarkUi();
    renderManagementUi();

    if (route.corrected || !hasCanonicalScopeInUrl()) {
      setHistory(docId, "", query, "replace");
    }

    if (state.searchRouteActive) {
      renderSearchMode();
      return;
    }

    loadDoc(docId, {
      historyMode: options && options.historyMode ? options.historyMode : "push",
      hash: options && options.hash ? options.hash : getCurrentHash(),
      expandTrail: Boolean(state.docsById.get(docId).parent_id)
    });
  }

  function loadIndex() {
    return fetchIndexWithRetry()
      .then(function (payload) {
        initializeIndex(payload);
      })
      .catch(function (error) {
        state.reloadExpectedDocId = "";
        setStatus(error.message || "Failed to load docs index.", true);
        hideDocPane();
        content.textContent = "";
        throw error;
      });
  }

  function loadSearchEntries() {
    if (!searchEnabled) {
      return Promise.reject(new Error("Search unavailable."));
    }
    if (state.searchLoaded) {
      return Promise.resolve(state.searchEntries);
    }
    if (state.searchRequestPromise) {
      return state.searchRequestPromise;
    }

    state.searchRequestPromise = fetchJsonWithRetry(
      searchIndexUrl,
      "Failed to load search data",
      managementReloadPath("/docs/search", { scope: viewerScope })
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
        state.searchRequestPromise = null;
      });

    return state.searchRequestPromise;
  }

  function normalizeSearchEntries(entries) {
    return entries
      .filter(function (entry) {
        return entry && typeof entry === "object";
      })
      .map(function (entry) {
        var kind = normalize(String(entry.kind || ""));
        var id = String(entry.id || "").trim();
        var title = String(entry.title || "").trim();
        var href = String(entry.href || "").trim();
        var displayMeta = String(entry.display_meta || "").trim();
        var parentTitle = String(entry.parent_title || "").trim();
        var searchTerms = Array.isArray(entry.search_terms)
          ? entry.search_terms.map(function (item) { return normalize(String(item || "")); }).filter(Boolean)
          : [];
        return {
          kind: kind,
          id: id,
          title: title,
          href: href,
          displayMeta: displayMeta,
          parentTitle: parentTitle,
          searchTerms: searchTerms,
          searchText: normalize(String(entry.search_text || "")),
          titleNorm: normalize(title),
          idNorm: normalize(id),
          titleTokens: normalize(title).split(" ").filter(Boolean),
          parentTitleNorm: normalize(parentTitle)
        };
      })
      .filter(function (entry) {
        return entry.kind === "doc" && entry.id && entry.title;
      });
  }

  function scoreSearchEntry(entry, query, queryTokens) {
    if (entry.idNorm === query) return 900;
    if (entry.titleNorm === query) return 860;
    if (entry.searchTerms.indexOf(query) >= 0) return 780;
    if (entry.titleNorm.indexOf(query) === 0) return 720;
    if (entry.idNorm.indexOf(query) === 0) return 690;
    if (queryTokens.every(function (token) {
      return entry.titleTokens.some(function (candidate) {
        return candidate === token || candidate.indexOf(token) === 0;
      });
    })) return 620;
    if (entry.parentTitleNorm && entry.parentTitleNorm.indexOf(query) >= 0) return 460;
    if (entry.searchText.indexOf(query) >= 0) return 320;
    return null;
  }

  function matchesAllTokens(entry, queryTokens) {
    return queryTokens.every(function (token) {
      if (entry.searchTerms.some(function (candidate) { return candidate === token || candidate.indexOf(token) === 0; })) {
        return true;
      }
      return entry.searchText.indexOf(token) >= 0;
    });
  }

  function collectSearchMatches(query) {
    var queryTokens = query.split(" ").filter(Boolean);
    if (!queryTokens.length) return [];

    var matches = [];
    state.searchEntries.forEach(function (entry) {
      if (!matchesAllTokens(entry, queryTokens)) return;
      var score = scoreSearchEntry(entry, query, queryTokens);
      if (score == null) return;
      matches.push({ entry: entry, score: score });
    });

    matches.sort(function (left, right) {
      if (left.score !== right.score) return right.score - left.score;
      var titleCmp = left.entry.title.localeCompare(right.entry.title, undefined, { sensitivity: "base", numeric: true });
      if (titleCmp !== 0) return titleCmp;
      return left.entry.id.localeCompare(right.entry.id, undefined, { sensitivity: "base", numeric: true });
    });

    return matches;
  }

  function renderSearchEntry(entry) {
    var metaText = entry.displayMeta || entry.parentTitle || "";
    return (
      '<li class="docsViewer__resultItem">' +
        '<a class="docsViewer__resultTitle" href="' + escapeHtml(viewerUrl(entry.id, "", "")) + '">' + escapeHtml(entry.title) + '</a>' +
        '<p class="docsViewer__resultId">' + escapeHtml(entry.id) + '</p>' +
        (metaText ? '<p class="docsViewer__resultMeta">' + escapeHtml(metaText) + '</p>' : '') +
      '</li>'
    );
  }

  function renderSearchPendingState() {
    if (!searchEnabled || !hasActiveQuery()) return;
    showSearchPane();
    setStatus(state.searchLoaded ? "Searching..." : "Loading search index...", false);
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    document.title = "Search | dotlineform";
  }

  function renderSearchMode() {
    if (!searchEnabled) {
      setStatus("Search unavailable.", true);
      hideDocPane();
      results.hidden = true;
      more.hidden = true;
      return;
    }

    var query = normalize(state.searchQuery);
    if (!query) {
      return;
    }

    showSearchPane();
    document.title = "Search | dotlineform";

    if (!state.searchLoaded) {
      renderSearchPendingState();
      loadSearchEntries()
        .then(function () {
          if (hasActiveQuery()) {
            renderSearchMode();
          }
        })
        .catch(function (error) {
          if (!hasActiveQuery()) return;
          setStatus(error.message || "Failed to load search data.", true);
          results.innerHTML = "";
          more.innerHTML = "";
          more.hidden = true;
        });
      return;
    }

    var matches = collectSearchMatches(query);
    if (!matches.length) {
      setStatus("No results.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    var visible = matches.slice(0, state.searchVisibleCount);
    setStatus(matches.length === 1
      ? "1 result"
      : matches.length > visible.length
        ? "Showing " + visible.length + " of " + matches.length + " results"
        : matches.length + " results",
    false);
    results.innerHTML = visible.map(function (match) {
      return renderSearchEntry(match.entry);
    }).join("");
    if (matches.length > visible.length) {
      more.hidden = false;
      more.innerHTML = '<button type="button" class="docsViewer__moreBtn" data-role="more">more</button>';
    } else {
      more.hidden = true;
      more.innerHTML = "";
    }
  }

  window.addEventListener("popstate", function () {
    if (state.docs.length === 0) return;
    cancelSearchDebounce();
    applyCurrentRoute({ historyMode: "none", hash: getCurrentHash() });
  });

  bindLinkInterception();
  initializeBookmarks();
  initializeManagement();
  loadIndex().catch(function () {});

  function appendAssetVersion(url) {
    var cleanUrl = String(url || "");
    if (!cleanUrl) return "";

    var assetVersion = readAssetVersion();
    if (!assetVersion) return cleanUrl;

    var separator = cleanUrl.indexOf("?") >= 0 ? "&" : "?";
    return cleanUrl + separator + "v=" + encodeURIComponent(assetVersion);
  }

  function requestUrl(url) {
    var nextUrl = appendAssetVersion(url);
    if (!state.reloadNonce) {
      return nextUrl;
    }
    var separator = nextUrl.indexOf("?") >= 0 ? "&" : "?";
    return nextUrl + separator + "reload=" + encodeURIComponent(state.reloadNonce);
  }

  function requestOptions() {
    return {
      headers: { Accept: "application/json" },
      cache: state.reloadNonce ? "no-store" : "default"
    };
  }

  function waitForReloadRetry() {
    return new Promise(function (resolve) {
      window.setTimeout(resolve, RELOAD_RETRY_DELAY_MS);
    });
  }

  function shouldRetryReload(error, attempt) {
    if (!state.reloadNonce) return false;
    if (attempt >= RELOAD_RETRY_ATTEMPTS - 1) return false;
    if (error && (error.status === 404 || error.status === 500 || error.status === 503)) {
      return true;
    }
    return Boolean(error && /failed to fetch/i.test(String(error.message || "")));
  }

  function fetchJsonOnce(url, failureLabel, reloadPath) {
    var fetchUrl = requestUrl(url);
    var options = requestOptions();
    if (state.reloadNonce && reloadPath && state.managementAvailable && managementBaseUrl) {
      fetchUrl = managementBaseUrl + reloadPath;
      options = {
        headers: { Accept: "application/json" }
      };
    }
    return window.fetch(fetchUrl, options)
      .then(function (response) {
        if (!response.ok) {
          var httpError = new Error(failureLabel + " (" + response.status + ")");
          httpError.status = response.status;
          throw httpError;
        }
        return response.json();
      });
  }

  function fetchJsonWithRetry(url, failureLabel, reloadPath, attempt) {
    var currentAttempt = typeof attempt === "number" ? attempt : 0;
    return fetchJsonOnce(url, failureLabel, reloadPath).catch(function (error) {
      if (!shouldRetryReload(error, currentAttempt)) {
        throw error;
      }
      return waitForReloadRetry().then(function () {
        return fetchJsonWithRetry(url, failureLabel, reloadPath, currentAttempt + 1);
      });
    });
  }

  function indexIncludesExpectedDoc(payload) {
    if (!state.reloadExpectedDocId) return true;
    var docs = payload && Array.isArray(payload.docs) ? payload.docs : [];
    return docs.some(function (doc) {
      return doc && doc.doc_id === state.reloadExpectedDocId;
    });
  }

  function fetchIndexWithRetry(attempt) {
    var currentAttempt = typeof attempt === "number" ? attempt : 0;
    return fetchJsonWithRetry(
      indexUrl,
      "Failed to load docs index",
      managementReloadPath("/docs/index", { scope: viewerScope }),
      currentAttempt
    )
      .then(function (payload) {
        if (indexIncludesExpectedDoc(payload)) {
          return payload;
        }
        if (!state.reloadNonce || currentAttempt >= RELOAD_RETRY_ATTEMPTS - 1) {
          var missingError = new Error("Updated docs index is missing " + state.reloadExpectedDocId + ".");
          missingError.status = 404;
          throw missingError;
        }
        return waitForReloadRetry().then(function () {
          return fetchIndexWithRetry(currentAttempt + 1);
        });
      });
  }

  function managementReloadPath(path, params) {
    if (!path || !params) return "";
    var query = [];
    Object.keys(params).forEach(function (key) {
      var value = String(params[key] || "").trim();
      if (!value) return;
      query.push(encodeURIComponent(key) + "=" + encodeURIComponent(value));
    });
    return query.length ? path + "?" + query.join("&") : path;
  }

  function readAssetVersion() {
    var meta = document.querySelector('meta[name="dlf-asset-version"]');
    if (!meta) return "";
    return String(meta.getAttribute("content") || "").trim();
  }

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(String(value || ""));
    }
    return String(value || "").replace(/["\\]/g, "\\$&");
  }
})();
