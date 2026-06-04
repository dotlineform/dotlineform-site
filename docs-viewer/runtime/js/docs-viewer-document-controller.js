export function initDocsViewerDocumentController(context) {
  var routeSession = context.routeSession;
  var scopeConfigState = context.scopeConfig;
  var selectedDocument = context.selectedDocument;
  var statusCommands = context.statusCommands || {};
  var content = context.content;
  var toolbar = context.toolbar;
  var meta = context.meta;
  var results = context.results;
  var more = context.more;

  function currentViewerScope() {
    return typeof context.viewerScope === "function" ? context.viewerScope() : context.viewerScope;
  }

  function currentManagementBaseUrl() {
    return typeof context.managementBaseUrl === "function" ? context.managementBaseUrl() : context.managementBaseUrl;
  }

  function managementModeActive() {
    return Boolean(routeSession && routeSession.managementMode);
  }

  function closeStatusMenu() {
    if (typeof statusCommands.closeStatusMenu === "function") statusCommands.closeStatusMenu();
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
      allowManagement: context.allowManagement,
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      generatedData: context.generatedData,
      managementBaseUrl: currentManagementBaseUrl(),
      managementMode: managementModeActive(),
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
    projectDocumentShell({
      toolbarHidden: true,
      metaHidden: true,
      contentHidden: true
    });
    context.renderBookmarkToggle();
    context.renderStatusPills();
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
    showDocPane();
    if (settings.hideMeta) {
      projectDocumentShell({
        toolbarHidden: true,
        metaHidden: true
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
    closeStatusMenu();
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
    if (meta && Object.prototype.hasOwnProperty.call(projection || {}, "metaHidden")) {
      meta.hidden = Boolean(projection.metaHidden);
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
