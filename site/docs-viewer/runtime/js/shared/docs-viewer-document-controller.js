export function initDocsViewerDocumentController(context) {
  var routeSession = context.routeSession;
  var scopeConfigState = context.scopeConfig;
  var selectedDocument = context.selectedDocument;
  var statusCommands = context.statusCommands || {};
  var content = context.content;
  var toolbar = context.toolbar;
  var results = context.results;
  var more = context.more;
  var documentMountGeneration = 0;

  function currentViewerScope() {
    return typeof context.viewerScope === "function" ? context.viewerScope() : context.viewerScope;
  }

  function managementContextActive() {
    return Boolean(routeSession && routeSession.managementContext);
  }

  function nextDocumentMountGeneration() {
    documentMountGeneration += 1;
    return documentMountGeneration;
  }

  function currentScopeType() {
    var configsById = scopeConfigState && scopeConfigState.scopeConfigsById;
    var scopeConfig = configsById && typeof configsById.get === "function"
      ? configsById.get(currentViewerScope())
      : null;
    return scopeConfig ? String(scopeConfig.scopeType || "").trim().toLowerCase() : "";
  }

  function setStatus(message, isError) {
    if (typeof statusCommands.setStatus === "function") {
      statusCommands.setStatus(message, isError);
    } else if (typeof context.setStatus === "function") {
      context.setStatus(message, isError);
    }
  }

  function mountDocumentExtras(doc, payload) {
    if (typeof context.mountDocumentExtras !== "function") return;
    Promise.resolve(context.mountDocumentExtras({
      appContext: context.appContext || {},
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      collectionProvider: context.collectionProvider,
      managementService: context.managementService || null,
      managementContext: managementContextActive(),
      payload: payload,
      routeContext: typeof context.routeContext === "function" ? context.routeContext() : context.routeContext,
      scopeConfigState: scopeConfigState,
      setStatus: setStatus,
      viewerScope: currentViewerScope(),
      viewerUrlForScope: context.viewerUrlForScope
    })).catch(function (error) {
      console.warn("docs_viewer: document extras unavailable", error);
    });
  }

  function mountInlineMermaid(doc, payload, mountGeneration) {
    var adapter = context.inlineMermaidAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    Promise.resolve(adapter.mountDocument({
      content: content,
      doc: doc,
      document: content ? content.ownerDocument : null,
      isCurrentMount: function () {
        return mountGeneration === documentMountGeneration;
      },
      mountGeneration: mountGeneration,
      payload: payload,
      scopeType: currentScopeType(),
      viewerScope: currentViewerScope(),
      window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
    })).catch(function (error) {
      console.warn("docs_viewer: inline Mermaid adapter unavailable", error);
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
    nextDocumentMountGeneration();
    projectDocumentShell({
      toolbarHidden: true,
      contentHidden: true
    });
    context.renderBookmarkToggle();
  }

  function showDocPane() {
    if (typeof context.clearResultsStatus === "function") context.clearResultsStatus();
    context.setRecentModeActive(false);
    projectDocumentShell({
      toolbarHidden: false,
      contentHidden: false,
      resultsHidden: true,
      moreHidden: true,
      clearMore: true
    });
  }

  function renderDocumentStatus(message, isError, options) {
    var settings = options || {};
    nextDocumentMountGeneration();
    showDocPane();
    if (settings.hideMeta) {
      projectDocumentShell({
        toolbarHidden: true
      });
    }
    if (!content) return;
    content.textContent = "";
    var status = document.createElement("p");
    status.className = "docsViewer__panelStatus muted small";
    status.classList.toggle("is-error", Boolean(isError));
    status.textContent = String(message || "");
    content.appendChild(status);
  }

  function showSearchPane() {
    hideDocPane();
    projectDocumentShell({ resultsHidden: false });
  }

  function showRecentPane() {
    hideDocPane();
    context.setRecentModeActive(true);
    projectDocumentShell({ resultsHidden: false });
  }

  function renderPayload(doc, payload, hash) {
    var mountGeneration = nextDocumentMountGeneration();
    selectedDocument.selectedDocId = doc.doc_id;
    context.renderSidebar();
    context.renderBookmarkUi();
    context.renderManagementUi();

    if (context.hasActiveQuery()) {
      context.setRecentModeActive(false);
      context.renderSearchMode();
      return;
    }

    showDocPane();
    context.renderMeta(doc);
    content.innerHTML = payload.content_html || "";
    mountInlineMermaid(doc, payload, mountGeneration);
    mountDocumentExtras(doc, payload);
    document.title = doc.title + " | dotlineform";
    setStatus("", false);
    context.renderManagementUi();

    window.requestAnimationFrame(function () {
      scrollToHash(hash);
    });
  }

  function handleMissingDoc() {
    renderDocumentStatus("Document not found.", true, { hideMeta: true });
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    context.renderManagementUi();
  }

  function renderDocLoadingState(doc) {
    nextDocumentMountGeneration();
    context.renderSidebar();
    showDocPane();
    context.renderMeta(doc);
    content.textContent = "";
  }

  function handlePayloadError(error) {
    renderDocumentStatus(error.message || "Failed to load document.", true);
  }

  function projectDocumentShell(projection) {
    if (typeof context.projectDocumentShell === "function") {
      context.projectDocumentShell(projection || {});
      return;
    }
    if (toolbar && Object.prototype.hasOwnProperty.call(projection || {}, "toolbarHidden")) {
      toolbar.hidden = Boolean(projection.toolbarHidden);
    }
    if (content && Object.prototype.hasOwnProperty.call(projection || {}, "contentHidden")) {
      content.hidden = Boolean(projection.contentHidden);
    }
    if (results && Object.prototype.hasOwnProperty.call(projection || {}, "resultsHidden")) {
      results.hidden = Boolean(projection.resultsHidden);
    }
    if (more && Object.prototype.hasOwnProperty.call(projection || {}, "moreHidden")) {
      more.hidden = Boolean(projection.moreHidden);
    }
    if (more && projection && projection.clearMore) {
      more.innerHTML = "";
    }
  }

  return {
    handleMissingDoc: handleMissingDoc,
    handlePayloadError: handlePayloadError,
    hideDocPane: hideDocPane,
    renderDocLoadingState: renderDocLoadingState,
    renderPayload: renderPayload,
    showDocPane: showDocPane,
    showRecentPane: showRecentPane,
    showSearchPane: showSearchPane
  };
}
