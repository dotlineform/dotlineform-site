(function () {
  var root = document.getElementById("docsViewerRoot");
  if (!root) return;

  var nav = document.getElementById("docsViewerNav");
  var status = document.getElementById("docsViewerStatus");
  var meta = document.getElementById("docsViewerMeta");
  var pathEl = document.getElementById("docsViewerPath");
  var updatedEl = document.getElementById("docsViewerUpdated");
  var content = document.getElementById("docsViewerContent");
  var searchInput = document.getElementById("docsViewerSearchInput");
  var results = document.getElementById("docsViewerResults");
  var more = document.getElementById("docsViewerMore");

  var indexUrl = appendAssetVersion(root.dataset.indexUrl);
  var viewerBaseUrl = root.dataset.viewerBaseUrl || "/docs/";
  var viewerScope = String(root.dataset.viewerScope || "").trim();
  var includeScopeParam = root.dataset.includeScopeParam === "true";
  var defaultRouteDocId = String(root.dataset.defaultDocId || "").trim();
  var viewerPathname = new URL(viewerBaseUrl, window.location.origin).pathname;
  var searchIndexUrl = appendAssetVersion(root.dataset.searchIndexUrl);
  var searchEnabled = Boolean(searchInput && results && more && searchIndexUrl);
  var SEARCH_BATCH_SIZE = 50;
  var SEARCH_DEBOUNCE_MS = 140;

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
    searchRouteActive: false
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

  function hasCanonicalScopeInUrl() {
    if (!includeScopeParam || !viewerScope) return true;
    return new URLSearchParams(window.location.search).get("scope") === viewerScope;
  }

  function hasActiveQuery(query) {
    return Boolean(normalize(typeof query === "string" ? query : state.searchQuery));
  }

  function viewerUrl(docId, hash, query) {
    var url = new URL(viewerBaseUrl, window.location.origin);
    if (includeScopeParam && viewerScope) {
      url.searchParams.set("scope", viewerScope);
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
      var children = state.childrenByParent.get(doc.doc_id) || [];
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
  }

  function setStatus(message, isError) {
    status.textContent = message;
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
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
      return;
    }

    state.selectedDocId = docId;
    if (shouldExpandTrail) {
      expandTrail(docId);
    }

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

    window
      .fetch(appendAssetVersion(doc.content_url), { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Failed to load " + doc.content_url + " (" + response.status + ")");
        }
        return response.json();
      })
      .then(function (payload) {
        if (state.requestId !== requestId) return;
        state.payloadCache.set(docId, payload);
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
    state.selectedDocId = docId;
    if (searchInput) {
      searchInput.value = query;
    }

    expandTrail(docId);
    renderSidebar();

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
    window
      .fetch(indexUrl, { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Failed to load docs index (" + response.status + ")");
        }
        return response.json();
      })
      .then(function (payload) {
        initializeIndex(payload);
      })
      .catch(function (error) {
        setStatus(error.message || "Failed to load docs index.", true);
        hideDocPane();
        content.textContent = "";
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

    state.searchRequestPromise = window
      .fetch(searchIndexUrl, { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Failed to load search data (" + response.status + ")");
        }
        return response.json();
      })
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
  loadIndex();

  function appendAssetVersion(url) {
    var cleanUrl = String(url || "");
    if (!cleanUrl) return "";

    var assetVersion = readAssetVersion();
    if (!assetVersion) return cleanUrl;

    var separator = cleanUrl.indexOf("?") >= 0 ? "&" : "?";
    return cleanUrl + separator + "v=" + encodeURIComponent(assetVersion);
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
})();
