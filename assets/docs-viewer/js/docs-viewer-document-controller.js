import {
  appendAssetVersion,
  fetchIndexWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath
} from "./docs-viewer-data.js";

export function initDocsViewerDocumentController(context) {
  var state = context.state;
  var content = context.content;
  var meta = context.meta;
  var results = context.results;
  var more = context.more;

  function currentViewerScope() {
    return typeof context.viewerScope === "function" ? context.viewerScope() : context.viewerScope;
  }

  function currentScopeConfigs() {
    return typeof context.scopeConfigs === "function" ? context.scopeConfigs() : state.scopeConfigs;
  }

  function currentReportRegistryUrl() {
    return typeof context.reportRegistryUrl === "function" ? context.reportRegistryUrl() : context.reportRegistryUrl;
  }

  function currentManagementBaseUrl() {
    return typeof context.managementBaseUrl === "function" ? context.managementBaseUrl() : context.managementBaseUrl;
  }

  function scopeConfig(scope) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    return state.scopeConfigsById.get(targetScope);
  }

  function fetchDocsIndexForScope(scope) {
    var targetScope = String(scope || currentViewerScope() || "").trim().toLowerCase();
    var targetConfig = scopeConfig(targetScope);
    if (!targetConfig || !targetConfig.indexUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return fetchIndexWithRetry(context.dataRequestOptions({
      indexUrl: appendAssetVersion(targetConfig.indexUrl),
      viewerScope: targetScope,
      reloadNonce: "",
      reloadExpectedDocId: ""
    }));
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
    return fetchPreferredGeneratedJson(
      appendAssetVersion(baseUrl + "/references/index.json"),
      "Failed to load docs references",
      managementReloadPath("/docs/generated/references", { scope: targetScope }),
      context.dataRequestOptions({
        viewerScope: targetScope,
        reloadNonce: "",
        reloadExpectedDocId: ""
      })
    );
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
    return fetchPreferredGeneratedJson(
      appendAssetVersion(staticUrl),
      "Failed to load docs reference target",
      managementReloadPath("/docs/generated/reference-target", {
        scope: targetScope,
        target_kind: targetKind,
        target_slug: targetSlug
      }),
      context.dataRequestOptions({
        viewerScope: targetScope,
        reloadNonce: "",
        reloadExpectedDocId: ""
      })
    );
  }

  function reportContext(doc, payload) {
    return {
      allowManagement: context.allowManagement,
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      fetchDocsReferenceTarget: fetchDocsReferenceTargetForScope,
      fetchDocsReferencesIndex: fetchDocsReferencesIndexForScope,
      fetchDocsIndex: fetchDocsIndexForScope,
      managementBaseUrl: currentManagementBaseUrl(),
      managementMode: state.managementMode,
      payload: payload,
      reportRegistryUrl: currentReportRegistryUrl(),
      setStatus: context.setStatus,
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
    if (meta) meta.hidden = true;
    if (content) content.hidden = true;
    context.renderBookmarkToggle();
    context.renderStatusPills();
  }

  function showDocPane() {
    context.setRecentModeActive(false);
    if (content) content.hidden = false;
    if (results) results.hidden = true;
    if (more) {
      more.hidden = true;
      more.innerHTML = "";
    }
  }

  function showSearchPane() {
    hideDocPane();
    if (results) results.hidden = false;
  }

  function showRecentPane() {
    hideDocPane();
    context.setRecentModeActive(true);
    if (results) results.hidden = false;
  }

  function renderPayload(doc, payload, hash) {
    state.statusMenuOpen = false;
    state.selectedDocId = doc.doc_id;
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
    context.setStatus("", false);

    window.requestAnimationFrame(function () {
      scrollToHash(hash);
    });
  }

  function handleMissingDoc() {
    context.setStatus("Document not found.", true);
    hideDocPane();
    content.textContent = "";
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    context.renderManagementUi();
  }

  function renderDocLoadingState(doc) {
    context.renderSidebar();
    showDocPane();
    context.renderMeta(doc);
    context.setStatus("Loading " + doc.title + "...", false);
    content.textContent = "";
  }

  function handlePayloadError(error) {
    context.setStatus(error.message || "Failed to load document.", true);
    content.textContent = "";
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
