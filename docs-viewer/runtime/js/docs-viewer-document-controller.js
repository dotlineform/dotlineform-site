import { createDocsViewerReportService } from "./docs-viewer-report-service.js";

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

  function currentScopeConfigs() {
    return scopeConfigState && Array.isArray(scopeConfigState.scopeConfigs) ? scopeConfigState.scopeConfigs : [];
  }

  function currentReportRegistryUrl() {
    return typeof context.reportRegistryUrl === "function" ? context.reportRegistryUrl() : context.reportRegistryUrl;
  }

  function currentManagementBaseUrl() {
    return typeof context.managementBaseUrl === "function" ? context.managementBaseUrl() : context.managementBaseUrl;
  }

  function scopeConfig(scope) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    return scopeConfigState && scopeConfigState.scopeConfigsById ? scopeConfigState.scopeConfigsById.get(targetScope) : null;
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

  function fetchDocsIndexForScope(scope) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    var targetConfig = scopeConfig(targetScope);
    if (!targetConfig || !targetConfig.indexUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return context.generatedData.readScopeIndex({
      scopeConfig: targetConfig,
      viewerScope: targetScope,
      reloadNonce: "",
      reloadExpectedDocId: ""
    });
  }

  function docsScopeDataBaseUrl(scope) {
    var targetConfig = scopeConfig(scope);
    var indexUrl = targetConfig ? String(targetConfig.indexUrl || "") : "";
    return indexUrl.replace(/\/index\.json(?:[?#].*)?$/, "");
  }

  function referenceTargetSlug(target) {
    var bucketUrl = String(target && target.bucket_url || "").trim();
    if (bucketUrl) {
      try {
        var url = new URL(bucketUrl, window.location.origin);
        var filename = url.pathname.split("/").pop() || "";
        if (filename.slice(-5) === ".json") return filename.slice(0, -5);
      } catch (error) {
        // Fall through to the target id encoding below.
      }
    }
    return encodeURIComponent(String(target && target.target_id || "").trim());
  }

  function fetchDocsReferencesIndexForScope(scope) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    var baseUrl = docsScopeDataBaseUrl(targetScope);
    if (!baseUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return context.generatedData.readReferencesIndex({
      baseUrl: baseUrl,
      viewerScope: targetScope
    });
  }

  function fetchDocsReferenceTargetForScope(scope, target) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    var targetKind = String(target && target.target_kind || "").trim();
    var targetSlug = referenceTargetSlug(target);
    var staticUrl = String(target && target.bucket_url || "").trim();
    if (!staticUrl) {
      var baseUrl = docsScopeDataBaseUrl(targetScope);
      staticUrl = baseUrl + "/references/by-target/" + encodeURIComponent(targetKind) + "/" + targetSlug + ".json";
    }
    return context.generatedData.readReferenceTarget({
      staticUrl: staticUrl,
      targetKind: targetKind,
      targetSlug: targetSlug,
      viewerScope: targetScope
    });
  }

  function reportContext(doc, payload) {
    var reportManagementBaseUrl = currentManagementBaseUrl();
    return {
      allowManagement: context.allowManagement,
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      fetchDocsReferenceTarget: fetchDocsReferenceTargetForScope,
      fetchDocsReferencesIndex: fetchDocsReferencesIndexForScope,
      fetchDocsIndex: fetchDocsIndexForScope,
      managementMode: managementModeActive(),
      payload: payload,
      reportRegistryUrl: currentReportRegistryUrl(),
      reportService: reportManagementBaseUrl
        ? createDocsViewerReportService({ baseUrl: reportManagementBaseUrl })
        : null,
      setStatus: setStatus,
      scopeConfigs: currentScopeConfigs().slice(),
      viewerScope: currentViewerScope(),
      viewerUrlForScope: context.viewerUrlForScope
    };
  }

  function payloadHasReport(payload) {
    return Boolean(payload && String(payload.viewer_report || "").trim());
  }

  function maybeMountDocsViewerReport(doc, payload) {
    if (!payloadHasReport(payload)) return;
    import("./docs-viewer-reports.js")
      .then(function (module) {
        return module.mountDocsViewerReport(reportContext(doc, payload));
      })
      .catch(function (error) {
        console.warn("docs_viewer: report controller unavailable", error);
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
    maybeMountDocsViewerReport(doc, payload);
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
