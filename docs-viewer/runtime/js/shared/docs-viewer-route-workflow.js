import { buildViewerUrl, CATALOGUE_SEARCH_PARAM, routeFromAnchorHref } from "./docs-viewer-router.js";
import { documentTarget, documentTargetKey } from "./docs-viewer-document-target.js";
import { createDocsViewerNavigation } from "./docs-viewer-navigation.js";
import { collectionSequenceForLink } from "./docs-viewer-collection-navigation.js";

function currentValue(value) { return typeof value === "function" ? value() : value; }

/** The common reader resolves exact targets; view owners retain their models. */
export function initDocsViewerRouteWorkflow(context) {
  var window = context.window;
  var index = context.documentIndex;
  var selected = context.selectedDocument;
  var search = context.searchRecent;
  var displayedHash = "";
  var displayedCatalogueSearch = "";
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
  function viewerUrl(docId, hash, query, targetOptions = {}, catalogueSearch = "") {
    return buildViewerUrl({ docId: docId, collection: targetOptions.collection || "", hash: hash,
      query: query, catalogueSearch: catalogueSearch, origin: window.location.origin, preservedQueryParams: preservedQueryParams(),
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
  function isCatalogueHost(target) {
    return Boolean(target && !target.collection && currentValue(context.viewerPathname) !== "/docs-review/"
      && target.doc_id === context.collectionConfig("catalogue")?.reportHostDocId);
  }
  function catalogueSearchFor(target, query) {
    return typeof query === "string" && isCatalogueHost(target) ? query.trim() : undefined;
  }
  function replaceCatalogueSearch(query) {
    var target = selected.documentTarget;
    var next = catalogueSearchFor(target, query);
    if (next === undefined || next === displayedCatalogueSearch) return;
    displayedCatalogueSearch = next;
    navigation.replaceUrl(viewerUrl(target.doc_id, displayedHash, search.searchQuery, target, next));
  }
  function capturePositions() {
    var positions = [];
    for (var node = context.activeMount(); node; node = node.parentElement) {
      positions.push({ node: node, top: node.scrollTop, left: node.scrollLeft });
    }
    return positions;
  }
  async function capture() {
    return { document: context.captureDocument(), hash: displayedHash, catalogueSearch: displayedCatalogueSearch,
      positions: capturePositions(), x: window.scrollX, y: window.scrollY,
      focus: context.root.ownerDocument.activeElement,
      focusHref: context.root.ownerDocument.activeElement && context.root.ownerDocument.activeElement.href || "" };
  }
  async function restore(record) {
    if (!record) throw new Error("This navigation entry is unavailable.");
    displayedHash = record.hash;
    displayedCatalogueSearch = record.catalogueSearch;
    await context.restoreDocument(record.document);
    // Keep the panel's current search query when restoring a document.
    var target = selected.documentTarget;
    if (target) navigation.replaceUrl(viewerUrl(target.doc_id, displayedHash, search.searchQuery, target, displayedCatalogueSearch));
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
    var sameTarget = selected.documentTarget && documentTargetKey(selected.documentTarget) === documentTargetKey(target);
    displayedCatalogueSearch = destination.catalogueSearch ?? (sameTarget ? displayedCatalogueSearch : "");
    var viewOptions = { catalogueSearch: destination.catalogueSearch, collectionSequence: destination.collectionSequence };
    if (!destination.force && await context.restoreRetainedDocument(target, displayedHash, viewOptions)) return target;
    selected.documentTarget = target;
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
      await context.renderPayload(doc, payload, displayedHash, viewOptions);
      return target;
    } catch (error) {
      context.handlePayloadError(error);
      return null;
    } finally { stop(); }
  }
  navigation = createDocsViewerNavigation({ window: window, capture: capture,
    callerAvailable: function (record) {
      var target = record.document && record.document.record && record.document.record.target;
      return Boolean(target && context.retainedDocumentAvailable(target));
    },
    prepare: context.prepareDocumentNavigation,
    retain: function (records) { context.retainDocuments(records.map(function (record) { return record.document; })); },
    confirm: context.confirmDocumentNavigation, open: open, restore: restore,
    onNavigationChange: context.onNavigationChange, reportError: function (error) { setStatus(error.message, true); } });
  if (context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    if (change.deleted) navigation.releaseUnavailableCaller();
  });
  function loadDoc(value, options = {}) {
    var target = documentTarget(typeof value === "string" ? { doc_id: value, collection: options.collection || "" } : value, { review: currentValue(context.viewerPathname) === "/docs-review/" });
    var key = documentTargetKey(target);
    if (pendingDocumentOpen) return pendingDocumentOpen.key === key ? pendingDocumentOpen.promise : Promise.resolve(null);
    var hash = options.hash || "";
    var catalogueSearch = catalogueSearchFor(target, options.catalogueSearch);
    var sameTarget = selected.documentTarget && documentTargetKey(target) === documentTargetKey(selected.documentTarget);
    if (sameTarget && !options.force) {
      return (async function () {
        if (!await context.confirmDocumentNavigation()) return null;
        await context.prepareDocumentNavigation();
        displayedHash = hash;
        displayedCatalogueSearch = catalogueSearch ?? displayedCatalogueSearch;
        navigation.replaceUrl(viewerUrl(target.doc_id, hash, search.searchQuery, target, displayedCatalogueSearch));
        if ((!hash || catalogueSearch !== undefined) && selected.displayedPayload && selected.displayedPayload.report
          && selected.displayedPayload.report.id === "docs_collection") {
          await navigation.update();
          await context.restoreRetainedDocument(target, hash, { catalogueSearch: catalogueSearch });
        } else {
          context.scrollToHash(hash);
          await navigation.update();
        }
        return target;
      })();
    }
    var promise = navigation.open({ target: target, hash: hash, catalogueSearch: catalogueSearch,
      collectionSequence: options.collectionSequence,
      force: options.force === true,
      url: viewerUrl(target.doc_id, hash, search.searchQuery, target, catalogueSearch ?? (sameTarget ? displayedCatalogueSearch : ""))
    }, { replace: options.historyMode === "replace" });
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
    return target ? loadDoc(target) : Promise.resolve(null);
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
    if (target) navigation.replaceUrl(viewerUrl(target.doc_id, displayedHash, query, target, displayedCatalogueSearch));
    updateNavigation();
  }
  async function applyCurrentRoute() {
    try {
      var target = requestedTarget();
      if (!initialized) {
        initialized = true;
        var catalogueSearch = catalogueSearchFor(target, new URLSearchParams(window.location.search).get(CATALOGUE_SEARCH_PARAM));
        context.syncIndexRoute(currentQuery());
        return await navigation.initialize({ target: target, hash: currentHash(), catalogueSearch: catalogueSearch,
          url: viewerUrl(target.doc_id, currentHash(), currentQuery(), target, catalogueSearch) });
      }
      return await loadDoc(target, { hash: currentHash(), historyMode: "replace", force: true });
    } catch (error) { context.handlePayloadError(error); return null; }
  }
  function replaceIndex(payload) {
    context.routeSession.managementContext = managementUiEnabled();
    index.docs = Array.isArray(payload.docs) ? payload.docs.slice() : [];
    context.updateDocumentIndex();
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
      loadDoc(route.target, { hash: route.hash, catalogueSearch: route.catalogueSearch,
        collectionSequence: collectionSequenceForLink(anchor) })
        .catch(function (error) { setStatus(error.message, true); });
    });
  }
  async function commitDeletedDocument(target) {
    var failures = context.collectionProvider.commitDocumentChange({ target: target, deleted: true });
    if (failures.length) throw new Error("Document deleted, but retained views could not be updated: " + failures.map(function (error) { return error.message; }).join("; "));
    if (!target.collection) await loadIndex({ preserveDocument: true });
    if (await navigation.returnToCaller()) return;
    if (target.collection) {
      if (!await openCollectionIndex()) throw new Error("The collection Index could not be displayed after Delete.");
      return;
    }
    var docId = context.defaultDocId();
    if (docId) {
      if (!await loadDoc(docId, { historyMode: "replace", force: true })) throw new Error("The surviving document could not be displayed after Delete.");
      return;
    }
    context.hideDocPane();
  }
  var commands = { applyCurrentRoute: applyCurrentRoute, loadDoc: loadDoc, loadIndex: loadIndex,
    resolveDocId: currentDocId, updateIndexHistory: updateIndexHistory, replaceCatalogueSearch: replaceCatalogueSearch,
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
