import { RETIRED_ANALYSIS_STATE, isSavedStateOwner } from "./docs-viewer-saved-state.js";

var bookmarkDbPromise = null;

export function bookmarkKey(owner, docId) {
  return "v2:" + String(owner || "") + "::" + String(docId || "");
}

export function isoNow() {
  return new Date().toISOString();
}

export function compareBookmarks(left, right) {
  var leftOrder = typeof left.order === "number" ? left.order : 0;
  var rightOrder = typeof right.order === "number" ? right.order : 0;
  if (leftOrder !== rightOrder) return leftOrder - rightOrder;
  return String(left.created_at_utc || "").localeCompare(String(right.created_at_utc || ""));
}

export function normalizeBookmarkRecord(record) {
  if (!record || typeof record !== "object") return null;
  var owner = record.owner;
  var docId = String(record.doc_id || "").trim();
  if (!isSavedStateOwner(owner) || !docId) return null;
  var defaultTitle = String(record.default_title || record.label || docId).trim() || docId;
  return {
    key: bookmarkKey(owner, docId),
    owner: owner,
    doc_id: docId,
    label: String(record.label || defaultTitle).trim() || defaultTitle,
    default_title: defaultTitle,
    created_at_utc: String(record.created_at_utc || record.updated_at_utc || isoNow()),
    updated_at_utc: String(record.updated_at_utc || record.created_at_utc || isoNow()),
    order: typeof record.order === "number" ? record.order : 0
  };
}

function bookmarkStorageError(message, error) {
  var storageError = error || new Error(message);
  storageError.bookmarkStorageUnavailable = true;
  return storageError;
}

export function openBookmarksDb(options) {
  var settings = options || {};
  var indexedDb = settings.indexedDB;
  var dbName = settings.dbName;
  var dbVersion = settings.dbVersion;
  var storeName = settings.storeName;

  if (!indexedDb) {
    return Promise.reject(bookmarkStorageError("Bookmarks unavailable in this browser."));
  }
  if (bookmarkDbPromise) {
    return bookmarkDbPromise;
  }

  bookmarkDbPromise = new Promise(function (resolve, reject) {
    var request = indexedDb.open(dbName, dbVersion);

    request.onupgradeneeded = function (event) {
      var db = request.result;
      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: "key" });
        return;
      }
      if (event.oldVersion < 3) {
        var store = request.transaction.objectStore(storeName);
        var cursorRequest = store.openCursor();
        cursorRequest.onsuccess = function () {
          var cursor = cursorRequest.result;
          if (!cursor) return;
          var record = cursor.value;
          var owner = record.owner === "published" ? "preview" : "";
          if (event.oldVersion < 2 && Object.prototype.hasOwnProperty.call(RETIRED_ANALYSIS_STATE, record.scope)) {
            owner = RETIRED_ANALYSIS_STATE[record.scope];
          }
          if (owner) {
            if (typeof record.doc_id !== "string" || !record.doc_id) {
              request.transaction.abort();
              return;
            }
            var converted = Object.assign({}, record, { owner: owner, key: bookmarkKey(owner, record.doc_id) });
            delete converted.scope;
            // add (rather than put) aborts the whole upgrade on a key collision.
            store.add(converted);
            cursor.delete();
          }
          cursor.continue();
        };
      }
    };

    request.onsuccess = function () {
      var db = request.result;
      db.onversionchange = function () {
        db.close();
        bookmarkDbPromise = null;
      };
      resolve(db);
    };

    request.onblocked = function () {
      reject(bookmarkStorageError("Close older Docs Viewer tabs to convert bookmarks, then reload."));
    };
    request.onerror = function () {
      reject(bookmarkStorageError("Failed to open or convert bookmark storage.", request.error));
    };
  }).catch(function (error) {
    bookmarkDbPromise = null;
    throw error;
  });

  return bookmarkDbPromise;
}

export function loadBookmarks(options) {
  var settings = options || {};
  return openBookmarksDb(settings).then(function (db) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(settings.storeName, "readonly");
      var store = tx.objectStore(settings.storeName);
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

export function persistBookmark(record, options) {
  var settings = options || {};
  return openBookmarksDb(settings).then(function (db) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(settings.storeName, "readwrite");
      tx.oncomplete = function () { resolve(record); };
      tx.onerror = function () { reject(tx.error || new Error("Failed to save bookmark.")); };
      tx.objectStore(settings.storeName).put(record);
    });
  });
}

export function deleteBookmarkRecord(key, options) {
  var settings = options || {};
  return openBookmarksDb(settings).then(function (db) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(settings.storeName, "readwrite");
      tx.oncomplete = function () { resolve(); };
      tx.onerror = function () { reject(tx.error || new Error("Failed to remove bookmark.")); };
      tx.objectStore(settings.storeName).delete(key);
    });
  });
}
