export function initDocsViewerDocumentController(context) {
  var routeSession = context.routeSession;
  var workspaceConfigState = context.workspaceConfig;
  var selectedDocument = context.selectedDocument;
  var statusCommands = context.statusCommands || {};
  var content = context.content;
  var toolbar = context.toolbar;
  var results = context.results;
  var more = context.more;
  var documentMountGeneration = 0;

  function managementContextActive() {
    return Boolean(routeSession && routeSession.managementContext);
  }

  function nextDocumentMountGeneration() {
    if (context.linksDetailAdapter) context.linksDetailAdapter.releaseDocument({ content: content });
    documentMountGeneration += 1;
    return documentMountGeneration;
  }

  function clearCollectionReportState(reason, mountGeneration) {
    if (typeof context.publishCollectionReportState !== "function") return;
    context.publishCollectionReportState({
      state: "inactive",
      reason: String(reason || "document-navigation"),
      documentMountGeneration: mountGeneration,
      parentTarget: null,
      documentTarget: null
    });
  }

  function setStatus(message, isError) {
    if (typeof statusCommands.setStatus === "function") {
      statusCommands.setStatus(message, isError);
    } else if (typeof context.setStatus === "function") {
      context.setStatus(message, isError);
    }
  }

  function mountDocumentExtras(doc, payload, mountGeneration) {
    if (typeof context.mountDocumentExtras !== "function") return;
    if (payload.report && payload.report.id === "docs_collection") {
      context.publishCollectionReportState({
        state: "loading",
        documentMountGeneration: mountGeneration,
        parentTarget: { ...(context.viewerStage() ? { stage: context.viewerStage() } : {}), doc_id: doc.doc_id },
        collectionTarget: { ...(context.viewerStage() ? { stage: context.viewerStage() } : {}), collection: payload.report.collection },
        collectionLabel: payload.report.collection,
        documentTarget: null
      });
    }
    Promise.resolve(context.mountDocumentExtras({
      appContext: context.appContext || {},
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      collectionProvider: context.collectionProvider,
      managementDocumentActions: context.managementDocumentActions || null,
      managementService: context.managementService || null,
      managementContext: managementContextActive(),
      mountThemedDiagrams: function () { mountThemedDiagrams(doc, payload); },
      payload: payload,
      documentMountGeneration: mountGeneration,
      reportPresentationAdapter: context.reportPresentationAdapter,
      loadMediaTarget: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (mountGeneration !== documentMountGeneration || !adapter) return null;
        return adapter.loadTarget(Object.assign({}, request, {
          content: content, documentMountGeneration: mountGeneration
        }));
      },
      openMediaTarget: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (mountGeneration !== documentMountGeneration || !adapter) return false;
        return adapter.openTarget(Object.assign({}, request, {
          content: content, documentMountGeneration: mountGeneration
        }));
      },
      openMediaPresentation: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (mountGeneration !== documentMountGeneration || !adapter) return false;
        return adapter.openPresentation(Object.assign({}, request, {
          content: content,
          documentMountGeneration: mountGeneration
        }));
      },
      requestContentDetail: context.requestContentDetail,
      onCollectionDocumentState: function (state) {
        if (mountGeneration !== documentMountGeneration) return;
        if (state.parentTarget && state.parentTarget.doc_id !== doc.doc_id) return;
        if (state.collectionTarget && (state.collectionTarget.collection !== payload.report.collection
          || String(state.collectionTarget.stage || "") !== String(context.viewerStage() || ""))) return;
        context.publishCollectionReportState(Object.assign({}, state, {
          documentMountGeneration: mountGeneration
        }));
        var adapter = context.linksDetailAdapter;
        if (!adapter) return;
        var target = state.state === "detail" ? state.documentTarget : null;
        if (target && (target.collection !== payload.report.collection
          || String(target.stage || "") !== String(context.viewerStage() || ""))) return;
        adapter.setDocument({ content: content, target: target, title: state.documentRecord && state.documentRecord.title });
      },
      routeContext: typeof context.routeContext === "function" ? context.routeContext() : context.routeContext,
      workspaceConfigState: workspaceConfigState,
      setStatus: setStatus,
      viewerStage: context.viewerStage(),
      viewerUrlForDocument: context.viewerUrlForDocument
    })).catch(function (error) {
      console.warn("docs_viewer: document extras unavailable", error);
    });
  }

  function mountDiagramDetails(doc, payload, mountGeneration) {
    var adapter = context.diagramDetailAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    try {
      adapter.mountDocument({
        content: content,
        doc: doc,
        document: content ? content.ownerDocument : null,
        documentMountGeneration: mountGeneration,
        payload: payload,
        requestContentDetail: context.requestContentDetail,
        viewerStage: context.viewerStage(),
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: diagram detail adapter unavailable", error);
    }
  }

  function mountTableDetails(doc, payload, mountGeneration) {
    var adapter = context.tableDetailAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    try {
      adapter.mountDocument({
        content: content,
        doc: doc,
        document: content ? content.ownerDocument : null,
        documentMountGeneration: mountGeneration,
        payload: payload,
        requestContentDetail: context.requestContentDetail,
        viewerStage: context.viewerStage(),
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: table detail adapter unavailable", error);
    }
  }

  function mountMediaDetails(doc, payload, mountGeneration) {
    var adapter = context.mediaDetailAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    try {
      var route = typeof context.routeContext === "function" ? context.routeContext() : context.routeContext;
      adapter.mountDocument({
        collectionProvider: context.collectionProvider,
        content: content,
        doc: doc,
        document: content ? content.ownerDocument : null,
        documentMountGeneration: mountGeneration,
        payload: payload,
        requestContentDetail: context.requestContentDetail,
        viewerStage: route && route.viewerStage,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: media detail adapter unavailable", error);
    }
  }

  function releaseTableDetails() {
    var adapter = context.tableDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: content,
        document: content ? content.ownerDocument : null,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: table detail cleanup unavailable", error);
    }
  }

  function releaseMediaDetails() {
    var adapter = context.mediaDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: content,
        document: content ? content.ownerDocument : null,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: media detail cleanup unavailable", error);
    }
  }

  function releaseReportPresentation() {
    var adapter = context.reportPresentationAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: content,
        document: content ? content.ownerDocument : null,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: report presentation cleanup unavailable", error);
    }
  }

  function releaseDiagramDetails() {
    var inlineAdapter = context.inlineMermaidAdapter;
    if (inlineAdapter && typeof inlineAdapter.releaseDocument === "function") {
      try {
        inlineAdapter.releaseDocument({
          content: content,
          document: content ? content.ownerDocument : null,
          window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
        });
      } catch (error) {
        console.warn("docs_viewer: inline Mermaid registry cleanup unavailable", error);
      }
    }
    var themedAdapter = context.themedDiagramAdapter;
    if (themedAdapter && typeof themedAdapter.releaseDocument === "function") {
      try {
        themedAdapter.releaseDocument({
          content: content,
          document: content ? content.ownerDocument : null,
          window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
        });
      } catch (error) {
        console.warn("docs_viewer: themed diagram registry cleanup unavailable", error);
      }
    }
    var adapter = context.diagramDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: content,
        document: content ? content.ownerDocument : null,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: diagram detail resource cleanup unavailable", error);
    }
  }

  function mountThemedDiagrams(doc, payload) {
    var adapter = context.themedDiagramAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    try {
      adapter.mountDocument({
        content: content,
        doc: doc,
        document: content ? content.ownerDocument : null,
        payload: payload,
        viewerStage: context.viewerStage(),
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: themed diagram adapter unavailable", error);
    }
  }

  function mountInlineMermaid(doc, payload, mountGeneration) {
    var adapter = context.inlineMermaidAdapter;
    var inlineRenderingEnabled = managementContextActive() && context.viewerStage() === "working";
    if (!inlineRenderingEnabled || !adapter || typeof adapter.mountDocument !== "function") return;
    Promise.resolve(adapter.mountDocument({
      content: content,
      diagramDetailAdapter: context.diagramDetailAdapter,
      doc: doc,
      document: content ? content.ownerDocument : null,
      isCurrentMount: function () {
        return mountGeneration === documentMountGeneration;
      },
      mountGeneration: mountGeneration,
      payload: payload,
      viewerStage: context.viewerStage(),
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
    var mountGeneration = nextDocumentMountGeneration();
    clearCollectionReportState("document-pane-hidden", mountGeneration);
    releaseReportPresentation();
    releaseMediaDetails();
    releaseTableDetails();
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
    var mountGeneration = nextDocumentMountGeneration();
    clearCollectionReportState("document-status", mountGeneration);
    showDocPane();
    if (settings.hideMeta) {
      projectDocumentShell({
        toolbarHidden: true
      });
    }
    if (!content) return;
    releaseReportPresentation();
    releaseMediaDetails();
    releaseTableDetails();
    releaseDiagramDetails();
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

  function renderPayload(doc, payload, hash, options = {}) {
    var scrollPositions = [];
    for (var node = content; options.preservePosition && node; node = node.parentElement) {
      scrollPositions.push({ node: node, top: node.scrollTop, left: node.scrollLeft });
    }
    var scrollX = window.scrollX;
    var scrollY = window.scrollY;
    var mountGeneration = nextDocumentMountGeneration();
    clearCollectionReportState("document-mount", mountGeneration);
    selectedDocument.selectedDocId = doc.doc_id;
    selectedDocument.displayedDocId = doc.doc_id;
    selectedDocument.displayedPayload = payload;
    if (!options.preservePosition) context.renderSidebar();
    context.renderBookmarkUi();
    context.renderManagementUi();

    if (context.hasActiveQuery()) {
      context.setRecentModeActive(false);
      context.renderSearchMode();
      return;
    }

    showDocPane();
    context.renderMeta(doc);
    releaseReportPresentation();
    releaseMediaDetails();
    releaseTableDetails();
    releaseDiagramDetails();
    content.innerHTML = payload.content_html || "";
    if (context.linksDetailAdapter) {
      context.linksDetailAdapter.mountDocument({
        content: content,
        target: payload.report ? null : {
          stage: context.viewerStage(), collection: "", doc_id: payload.doc_id
        },
        title: payload.title,
        collectionProvider: context.collectionProvider,
        projectControlState: context.projectLinksControlState,
        requestContentDetail: context.requestContentDetail,
        showWarning: setStatus
      });
    }
    mountTableDetails(doc, payload, mountGeneration);
    mountMediaDetails(doc, payload, mountGeneration);
    mountThemedDiagrams(doc, payload);
    mountDiagramDetails(doc, payload, mountGeneration);
    mountInlineMermaid(doc, payload, mountGeneration);
    mountDocumentExtras(doc, payload, mountGeneration);
    document.title = payload.title + " | dotlineform";
    setStatus("", false);
    context.renderManagementUi();

    if (options.preservePosition) {
      scrollPositions.forEach(function (position) {
        position.node.scrollTop = position.top;
        position.node.scrollLeft = position.left;
      });
      window.scrollTo(scrollX, scrollY);
    } else {
      window.requestAnimationFrame(function () { scrollToHash(hash); });
    }
  }

  function handleMissingDoc() {
    renderDocumentStatus("Document not found.", true, { hideMeta: true });
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    context.renderManagementUi();
  }

  function renderDocLoadingState(doc) {
    var mountGeneration = nextDocumentMountGeneration();
    clearCollectionReportState("navigation-start", mountGeneration);
    context.renderSidebar();
    showDocPane();
    context.renderMeta(doc);
    releaseReportPresentation();
    releaseMediaDetails();
    releaseTableDetails();
    releaseDiagramDetails();
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
    openLinks: function (detail) {
      if (detail.eventType !== "click" || !context.linksDetailAdapter) return false;
      return context.linksDetailAdapter.openTarget({ content: content, invocationControl: detail.target });
    },
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
