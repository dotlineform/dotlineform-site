import { normalizeDocIdSet } from "./docs-viewer-tree.js";
import { buildViewerUrl, routeFromAnchorHref } from "./docs-viewer-router.js";
import { documentTarget, documentTargetKey } from "./docs-viewer-document-target.js";
import { createDocsViewerNavigation } from "./docs-viewer-navigation.js";

function currentValue(value) { return typeof value === "function" ? value() : value; }

/** The common reader resolves exact targets; view owners retain their models. */
export function initDocsViewerRouteWorkflow(context) {
  var window = context.window;
  var index = context.documentIndex;
  var selected = context.selectedDocument;
  var search = context.searchRecent;
  var displayedHash = "";
  var initialized = false;
  var pendingDocumentOpen = null;
  var navigation;

  function currentDocId() { return new URLSearchParams(window.location.search).get("doc") || ""; }
  function currentHash() { return window.location.hash.slice(1); }
  function currentQuery() { return (new URLSearchParams(window.location.search).get("q") || "").trim(); }
  function managementUiEnabled() { return Boolean(currentValue(context.managementUiEnabled)); }
  function setStatus(message, error) { context.statusCommands.setStatus(message, error); }
  function preservedQueryParams() {
    var params = new URLSearchParams(window.location.search);
    var result = {};
    (currentValue(context.preserveQueryParams) || []).forEach(function (name) {
      if (params.get(name)) result[name] = params.get(name);
    });
    return result;
  }
  function viewerUrl(docId, hash, query, targetOptions = {}) {
    return buildViewerUrl({ docId: docId, collection: targetOptions.collection || "", hash: hash,
      query: query, origin: window.location.origin, preservedQueryParams: preservedQueryParams(),
      viewerBaseUrl: currentValue(context.viewerBaseUrl) });
  }
  function viewerUrlForDocument(docId, options = {}) { return viewerUrl(docId, "", "", options); }
  function routeFromAnchor(anchor) {
    return routeFromAnchorHref(anchor.href, { currentHref: window.location.href,
      origin: window.location.origin, viewerPathname: currentValue(context.viewerPathname) });
  }
  function requestedTarget() {
    var route = routeFromAnchor({ href: window.location.href });
    if (route && route.error) throw new Error(route.error);
    return route ? route.target : documentTarget({ doc_id: currentValue(context.defaultRouteDocId) || context.defaultDocId() }, { review: currentValue(context.viewerPathname) === "/docs-review/" });
  }
  function capturePositions() {
    var positions = [];
    for (var node = context.activeMount(); node; node = node.parentElement) {
      positions.push({ node: node, top: node.scrollTop, left: node.scrollLeft });
    }
    return positions;
  }
  async function capture() {
    return { document: context.captureDocument(), hash: displayedHash,
      positions: capturePositions(), x: window.scrollX, y: window.scrollY,
      focus: context.root.ownerDocument.activeElement,
      focusHref: context.root.ownerDocument.activeElement && context.root.ownerDocument.activeElement.href || "" };
  }
  async function restore(record) {
    if (!record) throw new Error("This navigation entry is unavailable.");
    context.restoreDocument(record.document);
    displayedHash = record.hash;
    // Index state belongs to the panel; align the restored route with its current query.
    var target = selected.documentTarget;
    if (target) navigation.replaceUrl(viewerUrl(target.doc_id, displayedHash, search.searchQuery, target));
    record.positions.forEach(function (position) {
      if (position.node.isConnected) { position.node.scrollTop = position.top; position.node.scrollLeft = position.left; }
    });
    window.scrollTo(record.x, record.y);
    var focus = record.focus && record.focus.isConnected && !record.focus.closest("[hidden]") ? record.focus :
      Array.from(context.root.querySelectorAll("a[href]")).find(function (node) { return record.focusHref && node.href === record.focusHref && !node.closest("[hidden]"); });
    if (focus) focus.focus({ preventScroll: true });
  }
  async function open(destination) {
    displayedHash = destination.hash || "";
    var target = destination.target;
    if (destination.indexDocId) {
      index.indexSelectedDocId = destination.indexDocId;
      context.trackSidebarSelection();
    }
    if (!destination.force && context.restoreRetainedDocument(target, displayedHash)) return target;
    selected.documentTarget = target;
    selected.displayedRecord = null;
    selected.displayedPayload = null;
    var request = ++selected.requestId;
    context.renderDocLoadingState({ doc_id: target.doc_id, collection: target.collection || "" });
    var stop = context.statusCommands.startBusy();
    try {
      var payload = await context.collectionProvider.readDocument(target);
      if (request !== selected.requestId) return null;
      if (!payload || payload.doc_id !== target.doc_id) throw new Error("Document payload did not match its exact target.");
      var policy = target.collection ? {} : index.docsById.get(target.doc_id) || {};
      var doc = Object.assign({}, policy, payload, target);
      selected.payloadCache.set(documentTargetKey(target), payload);
      await context.renderPayload(doc, payload, displayedHash);
      return target;
    } catch (error) {
      context.handlePayloadError(error);
      return null;
    } finally { stop(); }
  }
  navigation = createDocsViewerNavigation({ window: window, capture: capture,
    prepare: context.prepareDocumentNavigation,
    retain: function (records) { context.retainDocuments(records.map(function (record) { return record.document; })); },
    confirm: context.confirmDocumentNavigation, open: open, restore: restore,
    onNavigationChange: context.onNavigationChange, reportError: function (error) { setStatus(error.message, true); } });
  function loadDoc(value, options = {}) {
    var target = documentTarget(typeof value === "string" ? { doc_id: value, collection: options.collection || "" } : value, { review: currentValue(context.viewerPathname) === "/docs-review/" });
    var key = documentTargetKey(target);
    if (pendingDocumentOpen) return pendingDocumentOpen.key === key ? pendingDocumentOpen.promise : Promise.resolve(null);
    var hash = options.hash || "";
    if (selected.documentTarget && documentTargetKey(target) === documentTargetKey(selected.documentTarget) && !options.force) {
      return (async function () {
        if (!await context.confirmDocumentNavigation()) return null;
        await context.prepareDocumentNavigation();
        if (options.indexDocId) { index.indexSelectedDocId = options.indexDocId; context.trackSidebarSelection(); }
        displayedHash = hash;
        navigation.replaceUrl(viewerUrl(target.doc_id, hash, search.searchQuery, target));
        if (!hash && selected.displayedPayload && selected.displayedPayload.report
          && selected.displayedPayload.report.id === "docs_collection") {
          await navigation.update();
          context.restoreRetainedDocument(target, "");
        } else {
          context.scrollToHash(hash);
          await navigation.update();
        }
        return target;
      })();
    }
    var promise = navigation.open({ target: target, hash: hash, indexDocId: options.indexDocId, force: options.force === true,
      url: viewerUrl(target.doc_id, hash, search.searchQuery, target) }, { replace: options.historyMode === "replace" });
    pendingDocumentOpen = { key: key, promise: promise };
    return promise.finally(function () {
      if (pendingDocumentOpen && pendingDocumentOpen.promise === promise) pendingDocumentOpen = null;
    });
  }
  async function openPresentation(targetContext) {
    if (!await context.confirmDocumentNavigation()) return null;
    await context.prepareDocumentNavigation();
    await navigation.update();
    return context.openPresentation(targetContext);
  }
  function collectionIndexTarget() {
    var target = selected.documentTarget;
    var collection = target && target.collection && context.collectionConfig(target.collection);
    return collection ? { doc_id: collection.reportHostDocId } : null;
  }
  function openCollectionIndex() {
    var target = collectionIndexTarget();
    return target ? loadDoc(target, { indexDocId: target.doc_id }) : Promise.resolve(null);
  }
  async function returnToDocument() {
    await context.returnToDocument();
    await navigation.update();
  }
  function updateNavigation() {
    if (context.activeViewState().activeViewId === "rendered-document") return navigation.update();
    return Promise.resolve();
  }
  function updateIndexHistory(query) {
    var target = selected.documentTarget;
    if (target) navigation.replaceUrl(viewerUrl(target.doc_id, displayedHash, query, target));
    updateNavigation();
  }
  async function applyCurrentRoute() {
    try {
      var target = requestedTarget();
      if (!initialized) {
        initialized = true;
        context.syncIndexRoute(currentQuery());
        return await navigation.initialize({ target: target, hash: currentHash(),
          indexDocId: !target.collection && index.docsById.has(target.doc_id) ? target.doc_id : "",
          url: viewerUrl(target.doc_id, currentHash(), currentQuery(), target) });
      }
      return await loadDoc(target, { hash: currentHash(), historyMode: "replace", force: true });
    } catch (error) { context.handlePayloadError(error); return null; }
  }
  function replaceIndex(payload) {
    context.routeSession.managementContext = managementUiEnabled();
    var options = payload.viewer_options || {};
    index.nonLoadableDocIds = normalizeDocIdSet(options.non_loadable_doc_ids, []);
    index.manageOnlyTreeRootIds = normalizeDocIdSet(options.manage_only_tree_root_ids, []);
    index.allDocs = Array.isArray(payload.docs) ? payload.docs.slice() : [];
    context.applyDocVisibility();
    context.renderSidebar();
  }
  /** Application completion reads the exact generated result without opening a history entry. */
  async function refreshDocument(target, options = {}) {
    var request = selected.requestId;
    var key = documentTargetKey(target);
    var mode = context.activeViewState().activeModeId;
    if (!selected.documentTarget || key !== documentTargetKey(selected.documentTarget)) {
      throw new Error("The document to refresh is no longer displayed.");
    }
    if (!options.sourceSaved && !await context.confirmDocumentNavigation()) {
      throw new Error("Updated document output was not displayed; Source edits were retained.");
    }
    // Retained payloads cannot satisfy an action's fresh-result read.
    var payload = await context.collectionProvider.readDocument(target);
    if (request !== selected.requestId || !selected.documentTarget
      || key !== documentTargetKey(selected.documentTarget)
      || key !== documentTargetKey(requestedTarget())
      || mode !== context.activeViewState().activeModeId) throw new Error("The document refresh target changed.");
    if (!payload || payload.doc_id !== target.doc_id) throw new Error("Document payload did not match the refresh target.");
    await context.prepareDocumentNavigation();
    await context.refreshRenderedPayload(Object.assign({}, selected.displayedRecord, payload, target), payload);
    await navigation.update();
  }
  async function loadIndex(options = {}) {
    var stop = context.statusCommands.startBusy();
    try {
      replaceIndex(await context.collectionProvider.readIndex());
      if (!options.preserveDocument) return await applyCurrentRoute();
    } finally { stop(); }
  }
  function shouldUseNativeNavigation(event, anchor) {
    return event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
      || anchor.hasAttribute("download") || Boolean(anchor.target && anchor.target !== "_self");
  }
  function bindRouteLinks() {
    ["input", "change"].forEach(function (eventName) { context.root.addEventListener(eventName, updateNavigation); });
    context.root.addEventListener("click", function (event) {
      if (event.target.closest("button, input")) window.setTimeout(updateNavigation, 0);
      if (context.handleManagementRootClick && context.handleManagementRootClick(event)) return;
      var toggle = event.target.closest("[data-toggle-doc-id]");
      if (toggle) { context.toggleSidebarBranch(toggle.dataset.toggleDocId); updateNavigation(); return; }
      var anchor = event.target.closest("a[href]");
      if (!anchor || shouldUseNativeNavigation(event, anchor)) return;
      var route = routeFromAnchor(anchor);
      if (!route) return;
      event.preventDefault();
      if (route.error) { setStatus(route.error, true); return; }
      var row = anchor.closest("[data-doc-row-id]");
      loadDoc(route.target, { hash: route.hash, indexDocId: row && row.dataset.docRowId }).catch(function (error) { setStatus(error.message, true); });
    });
  }
  async function commitDeletedDocument(target) {
    context.collectionProvider.commitDocumentChange({ target: target, deleted: true });
    if (!target.collection) await loadIndex({ preserveDocument: true });
    if (navigation.hasCaller()) { navigation.back(); return; }
    var docId = context.defaultDocId();
    if (docId) return loadDoc(docId, { historyMode: "replace", force: true });
    context.hideDocPane();
  }
  var commands = { applyCurrentRoute: applyCurrentRoute, loadDoc: loadDoc, loadIndex: loadIndex,
    resolveDocId: currentDocId, updateIndexHistory: updateIndexHistory,
    viewerUrl: viewerUrl, viewerUrlForDocument: viewerUrlForDocument,
    openPresentation: openPresentation, returnToDocument: returnToDocument,
    collectionIndexTarget: collectionIndexTarget, openCollectionIndex: openCollectionIndex,
    commitDeletedDocument: commitDeletedDocument, refreshDocument: refreshDocument };
  return { commands: commands, bindPopstate: navigation.bind, bindRouteLinks: bindRouteLinks,
    currentDocId: currentDocId, currentHash: currentHash, currentQuery: currentQuery,
    hasDisallowedModeInUrl: function () { return new URLSearchParams(window.location.search).has("mode"); },
    managementUiEnabled: managementUiEnabled, routeFromAnchor: routeFromAnchor,
    shouldUseNativeNavigation: shouldUseNativeNavigation, viewerUrl: viewerUrl,
    viewerUrlForDocument: viewerUrlForDocument };
}
