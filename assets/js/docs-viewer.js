(function () {
  var root = document.getElementById("docsViewerRoot");
  if (!root) return;

  var nav = document.getElementById("docsViewerNav");
  var sidebarMeta = document.getElementById("docsViewerSidebarMeta");
  var status = document.getElementById("docsViewerStatus");
  var meta = document.getElementById("docsViewerMeta");
  var pathEl = document.getElementById("docsViewerPath");
  var updatedEl = document.getElementById("docsViewerUpdated");
  var content = document.getElementById("docsViewerContent");

  var indexUrl = root.dataset.indexUrl;
  var viewerBaseUrl = root.dataset.viewerBaseUrl || "/docs/";
  var viewerPathname = new URL(viewerBaseUrl, window.location.origin).pathname;

  var state = {
    docs: [],
    docsById: new Map(),
    childrenByParent: new Map(),
    payloadCache: new Map(),
    selectedDocId: "",
    requestId: 0
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

  function viewerUrl(docId, hash) {
    var url = new URL(viewerBaseUrl, window.location.origin);
    url.searchParams.set("doc", docId);
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

  function renderSidebar() {
    nav.textContent = "";
    if (state.docs.length === 0) {
      sidebarMeta.textContent = "No docs available.";
      return;
    }

    sidebarMeta.textContent = state.docs.length + (state.docs.length === 1 ? " doc" : " docs");
    nav.appendChild(renderNavList(""));
  }

  function renderNavList(parentId) {
    var list = document.createElement("ul");
    list.className = parentId ? "docsViewer__navList docsViewer__navList--child" : "docsViewer__navList";

    var docs = state.childrenByParent.get(parentId) || [];
    docs.forEach(function (doc) {
      var item = document.createElement("li");
      item.className = "docsViewer__navItem";

      var link = document.createElement("a");
      link.className = "docsViewer__navLink";
      if (doc.doc_id === state.selectedDocId) {
        link.className += " is-active";
        link.setAttribute("aria-current", "page");
      }
      link.href = viewerUrl(doc.doc_id);
      link.dataset.docId = doc.doc_id;
      link.textContent = doc.title;
      item.appendChild(link);

      var children = state.childrenByParent.get(doc.doc_id) || [];
      if (children.length > 0) {
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

  function renderPayload(doc, payload, hash) {
    state.selectedDocId = doc.doc_id;
    renderSidebar();
    renderMeta(doc);
    content.innerHTML = payload.content_html || "";
    document.title = doc.title + " | dotlineform";
    setStatus("", false);

    window.requestAnimationFrame(function () {
      scrollToHash(hash);
    });
  }

  function setHistory(docId, hash, mode) {
    if (mode === "none") return;

    var nextUrl = viewerUrl(docId, hash);
    if (mode === "replace") {
      window.history.replaceState({ docId: docId, hash: hash || "" }, "", nextUrl);
      return;
    }

    window.history.pushState({ docId: docId, hash: hash || "" }, "", nextUrl);
  }

  function loadDoc(docId, options) {
    var mode = options && options.historyMode ? options.historyMode : "push";
    var hash = options && options.hash ? options.hash : "";
    var doc = state.docsById.get(docId);
    if (!doc) {
      setStatus("Document not found.", true);
      meta.hidden = true;
      content.textContent = "";
      return;
    }

    setHistory(docId, hash, mode);

    if (state.payloadCache.has(docId)) {
      renderPayload(doc, state.payloadCache.get(docId), hash);
      return;
    }

    state.selectedDocId = docId;
    renderSidebar();
    renderMeta(doc);
    setStatus("Loading " + doc.title + "...", false);
    content.textContent = "";

    var requestId = state.requestId + 1;
    state.requestId = requestId;

    window
      .fetch(doc.content_url, { headers: { Accept: "application/json" } })
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
      var anchor = event.target.closest("a[href]");
      if (!anchor) return;

      var route = routeFromAnchor(anchor);
      if (!route) return;

      event.preventDefault();
      loadDoc(route.docId, { historyMode: "push", hash: route.hash });
    });
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

    var initialDocId = getCurrentDocId();
    if (!state.docsById.has(initialDocId)) {
      initialDocId = defaultDocId();
    }

    if (!initialDocId) {
      setStatus("No docs available.", true);
      return;
    }

    loadDoc(initialDocId, { historyMode: "replace", hash: getCurrentHash() });
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
        sidebarMeta.textContent = "Index unavailable";
        content.textContent = "";
      });
  }

  window.addEventListener("popstate", function () {
    if (state.docs.length === 0) return;

    var docId = getCurrentDocId();
    if (!state.docsById.has(docId)) {
      docId = defaultDocId();
    }
    if (!docId) return;

    loadDoc(docId, { historyMode: "none", hash: getCurrentHash() });
  });

  bindLinkInterception();
  loadIndex();
})();
