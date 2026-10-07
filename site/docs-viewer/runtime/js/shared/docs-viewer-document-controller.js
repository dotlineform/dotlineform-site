import { documentTarget, documentTargetKey } from "./docs-viewer-document-target.js";
import { mountDocsContentHtml } from "./docs-viewer-asset-url.js";

export function initDocsViewerDocumentController(context) {
  var routeSession = context.routeSession;
  var workspaceConfigState = context.workspaceConfig;
  var selectedDocument = context.selectedDocument;
  var statusCommands = context.statusCommands || {};
  var outerContent = context.content;
  var content = outerContent;
  var retained = new Map();
  var activeRecord = null;
  var transientContent = null;
  var document = outerContent.ownerDocument;
  var window = document.defaultView;

  function actionContext() { return activeRecord && activeRecord.actionContext || {}; }
  function capture() { return { record: activeRecord, owners: (activeRecord && activeRecord.viewOwners || []).map(function (owner) { return { id: owner.id, state: owner.capture() }; }) }; }
  function activate(record) {
    if (transientContent) { transientContent.remove(); transientContent = null; }
    retained.forEach(function (item) { item.root.hidden = item !== record; });
    if (content === outerContent) outerContent.replaceChildren();
    content = record.root;
    activeRecord = record;
    documentMountGeneration = record.generation;
    selectedDocument.documentTarget = record.target;
    selectedDocument.selectedDocId = record.target.doc_id;
    selectedDocument.displayedDocId = record.target.doc_id;
    selectedDocument.displayedRecord = record.doc;
    selectedDocument.displayedPayload = record.payload;
    content.hidden = false;
    showDocPane();
    context.publishCollectionReportState(record.actionContext);
    document.title = (record.doc.title || record.target.doc_id) + " | dotlineform";
    context.renderManagementUi();
  }
  function restore(snapshot) {
    var record = snapshot && snapshot.record;
    if (record) selectedDocument.documentTarget = record.target;
    if (record && record.error) renderDocumentStatus(record.error, true);
    else if (record && retained.get(documentTargetKey(record.target)) === record) {
      activate(record);
      record.restorationStates = new Map((snapshot.owners || []).map(function (saved) { return [saved.id, saved.state]; }));
      record.viewOwners.forEach(function (owner) {
        if (record.restorationStates.has(owner.id)) owner.restore(record.restorationStates.get(owner.id));
      });
    } else handleMissingDoc();
  }
  function restoreRetained(target, hash) {
    var record = retained.get(documentTargetKey(target));
    if (!record) return false;
    activate(record);
    // A list owner may resume its last visible state independently of this entry.
    var resumed = false;
    record.viewOwners.forEach(function (owner) { if (owner.resume) { owner.resume(); resumed = true; } });
    if (hash) scrollToHash(hash);
    else if (!resumed) window.scrollTo(0, 0);
    return true;
  }

  function releaseRecordViews(record) {
    var lifetime = record.lifetime;
    if (lifetime) {
      lifetime.active = false;
      lifetime.unsubscribers.forEach(function (unsubscribe) { unsubscribe(); });
      lifetime.unsubscribers = [];
    }
    record.viewOwners.forEach(function (owner) { if (owner.dispose) owner.dispose(); });
    record.viewOwners = [];
    record.restorationStates = null;
    releaseReportPresentation(record.root);
    releaseMediaDetails(record.root);
    releaseTableDetails(record.root);
    releaseDiagramDetails(record.root);
  }

  function releaseRecord(record) {
    releaseRecordViews(record);
    record.root.remove();
    var key = documentTargetKey(record.target);
    retained.delete(key);
    selectedDocument.payloadCache.delete(key);
  }

  function retainDocuments(snapshots) {
    var keep = new Set(snapshots.map(function (snapshot) { return snapshot.record; }));
    retained.forEach(function (record) { if (!keep.has(record)) releaseRecord(record); });
    selectedDocument.payloadCache.forEach(function (_, key) {
      if (!retained.has(key)) selectedDocument.payloadCache.delete(key);
    });
  }
  var toolbar = context.toolbar;
  var documentMountGeneration = 0;
  var generationSequence = 0;

  function managementContextActive() {
    return Boolean(routeSession && routeSession.managementContext);
  }

  function nextDocumentMountGeneration() {
    documentMountGeneration = ++generationSequence;
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
    var mountContent = content;
    var mountedRecord = activeRecord;
    var lifetime = mountedRecord.lifetime;
    // Preserve route capabilities while bounding report listeners to this mount.
    var collectionProvider = Object.assign({}, context.collectionProvider);
    if (context.collectionProvider.subscribeDocumentChanges) {
      collectionProvider.subscribeDocumentChanges = function (listener) {
        if (!lifetime.active) return function () {};
        var unsubscribe = context.collectionProvider.subscribeDocumentChanges(function (change) {
          if (lifetime.active) listener(change);
        });
        lifetime.unsubscribers.push(unsubscribe);
        return unsubscribe;
      };
    }
    if (typeof context.mountDocumentExtras !== "function") return;
    if (payload.report && payload.report.id === "docs_collection") {
      context.publishCollectionReportState({
        state: "loading",
        documentMountGeneration: mountGeneration,
        parentTarget: {  doc_id: doc.doc_id },
        collectionTarget: {  collection: payload.report.collection },
        collectionLabel: payload.report.collection,
        documentTarget: null
      });
    }
    Promise.resolve(context.mountDocumentExtras({
      appContext: context.appContext || {},
      checkGeneratedDataReadCapability: context.checkGeneratedDataReadCapability,
      content: mountContent,
      doc: doc,
      documentTarget: mountedRecord.target,
      documentActionContext: mountedRecord.actionContext,
      registerRetainedView: function (owner) {
        if (!lifetime.active) { if (owner.dispose) owner.dispose(); return; }
        mountedRecord.viewOwners.push(owner);
        if (mountedRecord.restorationStates && mountedRecord.restorationStates.has(owner.id)) owner.restore(mountedRecord.restorationStates.get(owner.id));
      },
      onDocumentActionState: function (state) {
        if (!lifetime.active) return;
        mountedRecord.actionContext = state;
        if (state.documentRecord) mountedRecord.doc = Object.assign({}, state.documentRecord, mountedRecord.target);
        if (activeRecord === mountedRecord) selectedDocument.displayedRecord = mountedRecord.doc;
        if (activeRecord === mountedRecord) context.publishCollectionReportState(state);
      },
      openDocument: context.openDocument,
      commitDeletedDocument: context.commitDeletedDocument,
      collectionProvider: collectionProvider,
      managementDocumentActions: context.managementDocumentActions || null,
      managementService: context.managementService || null,
      managementContext: managementContextActive(),
      mountThemedDiagrams: function () { if (lifetime.active) mountThemedDiagrams(doc, payload, mountContent); },
      mountRelatedLinks: context.mountRelatedLinks,
      payload: payload,
      mediaRoot: workspaceConfigState.activeConfig && workspaceConfigState.activeConfig.mediaRoot,
      viewerBaseUrl: workspaceConfigState.activeConfig && workspaceConfigState.activeConfig.viewerBaseUrl,
      documentMountGeneration: mountGeneration,
      reportPresentationAdapter: context.reportPresentationAdapter,
      loadMediaTarget: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (!lifetime.active || !mountContent.isConnected || !adapter) return null;
        return adapter.loadTarget(Object.assign({}, request, {
          content: mountContent, documentMountGeneration: mountGeneration
        }));
      },
      openMediaTarget: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (!lifetime.active || !mountContent.isConnected || !adapter) return false;
        return adapter.openTarget(Object.assign({}, request, {
          content: mountContent, documentMountGeneration: mountGeneration
        }));
      },
      openMediaPresentation: function (request) {
        var adapter = context.mediaDetailAdapter;
        if (!lifetime.active || !mountContent.isConnected || !adapter) return false;
        return adapter.openPresentation(Object.assign({}, request, {
          content: mountContent,
          documentMountGeneration: mountGeneration
        }));
      },
      requestContentDetail: context.requestContentDetail,
      onCollectionDocumentState: function (state) {
        if (!lifetime.active || !mountContent.isConnected) return;
        mountedRecord.actionContext = Object.assign({}, state, { documentMountGeneration: mountGeneration });
        if (activeRecord === mountedRecord) context.publishCollectionReportState(mountedRecord.actionContext);
      },
      routeContext: typeof context.routeContext === "function" ? context.routeContext() : context.routeContext,
      workspaceConfigState: workspaceConfigState,
      setStatus: setStatus,
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
      adapter.mountDocument({
        collectionProvider: context.collectionProvider,
        content: content,
        doc: doc,
        document: content ? content.ownerDocument : null,
        documentMountGeneration: mountGeneration,
        payload: payload,
        requestContentDetail: context.requestContentDetail,
        viewerConfig: workspaceConfigState.activeConfig,
        window: content && content.ownerDocument ? content.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: media detail adapter unavailable", error);
    }
  }

  function releaseTableDetails(mount = content) {
    var adapter = context.tableDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: mount,
        document: mount ? mount.ownerDocument : null,
        window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: table detail cleanup unavailable", error);
    }
  }

  function releaseMediaDetails(mount = content) {
    var adapter = context.mediaDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: mount,
        document: mount ? mount.ownerDocument : null,
        window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: media detail cleanup unavailable", error);
    }
  }

  function releaseReportPresentation(mount = content) {
    var adapter = context.reportPresentationAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: mount,
        document: mount ? mount.ownerDocument : null,
        window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: report presentation cleanup unavailable", error);
    }
  }

  function releaseDiagramDetails(mount = content) {
    var inlineAdapter = context.inlineMermaidAdapter;
    if (inlineAdapter && typeof inlineAdapter.releaseDocument === "function") {
      try {
        inlineAdapter.releaseDocument({
          content: mount,
          document: mount ? mount.ownerDocument : null,
          window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
        });
      } catch (error) {
        console.warn("docs_viewer: inline Mermaid registry cleanup unavailable", error);
      }
    }
    var themedAdapter = context.themedDiagramAdapter;
    if (themedAdapter && typeof themedAdapter.releaseDocument === "function") {
      try {
        themedAdapter.releaseDocument({
          content: mount,
          document: mount ? mount.ownerDocument : null,
          window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
        });
      } catch (error) {
        console.warn("docs_viewer: themed diagram registry cleanup unavailable", error);
      }
    }
    var adapter = context.diagramDetailAdapter;
    if (!adapter || typeof adapter.releaseDocument !== "function") return;
    try {
      adapter.releaseDocument({
        content: mount,
        document: mount ? mount.ownerDocument : null,
        window: mount && mount.ownerDocument ? mount.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: diagram detail resource cleanup unavailable", error);
    }
  }

  function mountThemedDiagrams(doc, payload, mountRoot) {
    var mountedContent = mountRoot || content;
    var adapter = context.themedDiagramAdapter;
    if (!adapter || typeof adapter.mountDocument !== "function") return;
    try {
      adapter.mountDocument({
        content: mountedContent,
        doc: doc,
        document: mountedContent ? mountedContent.ownerDocument : null,
        payload: payload,
        window: mountedContent && mountedContent.ownerDocument ? mountedContent.ownerDocument.defaultView : null
      });
    } catch (error) {
      console.warn("docs_viewer: themed diagram adapter unavailable", error);
    }
  }

  function mountInlineMermaid(doc, payload, mountGeneration) {
    var adapter = context.inlineMermaidAdapter;
    var inlineRenderingEnabled = managementContextActive();
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

    var target = Array.from(content.querySelectorAll("[id]")).find(function (node) { return node.id === hash; });
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
  }

  function showDocPane() {
    projectDocumentShell({
      toolbarHidden: false,
      contentHidden: false
    });
  }

  function renderDocumentStatus(message, isError, options) {
    var settings = options || {};
    var mountGeneration = nextDocumentMountGeneration();
    activeRecord = { target: selectedDocument.documentTarget, error: message, root: null };
    selectedDocument.displayedRecord = null;
    selectedDocument.displayedPayload = null;
    retained.forEach(function (record) { record.root.hidden = true; });
    if (transientContent) transientContent.remove();
    content = document.createElement("div");
    transientContent = content;
    outerContent.appendChild(content);
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
    activeRecord.root = content;
  }

  function renderPayload(doc, payload, hash, options = {}) {
    var scrollPositions = [];
    for (var node = content; options.preservePosition && node; node = node.parentElement) {
      scrollPositions.push({ node: node, top: node.scrollTop, left: node.scrollLeft });
    }
    var scrollX = window.scrollX;
    var scrollY = window.scrollY;
    if (transientContent) { transientContent.remove(); transientContent = null; }
    var target = documentTarget(doc, { review: context.appContext.kind === "review" });
    var key = documentTargetKey(target);
    var previous = retained.get(key);
    var committedRecord = previous && previous.committedRecord && JSON.stringify(payload) === JSON.stringify(previous.payload) ? previous.committedRecord : null;
    if (committedRecord) doc = Object.assign({}, doc, committedRecord, target);
    var mountGeneration = nextDocumentMountGeneration();
    retained.forEach(function (record) { record.root.hidden = true; });
    if (previous) {
      content = previous.root;
      releaseRecordViews(previous);
    } else {
      if (content === outerContent) outerContent.replaceChildren();
      content = document.createElement("div");
      content.className = "docsViewer__documentMount";
      outerContent.appendChild(content);
    }
    content.hidden = false;
    var record = Object.assign(previous || {}, { target: target, doc: doc, payload: payload, root: content, generation: mountGeneration, viewOwners: [], restorationStates: null,
      lifetime: { active: true, unsubscribers: [] },
      committedRecord: committedRecord,
      actionContext: { state: target.collection ? "detail" : "document", documentTarget: target, documentRecord: doc,
        collectionTarget: target.collection ? { collection: target.collection } : null,
        collectionLabel: target.collection || "",
        refreshDocument: context.openDocument,
        commitDeletedDocument: context.commitDeletedDocument,
        commitDocumentDraft: function (draftTarget, committedRecord) {
          context.collectionProvider.commitDocumentChange({ target: draftTarget, record: committedRecord });
        } } });
    activeRecord = record;
    retained.set(key, record);
    selectedDocument.documentTarget = target;
    selectedDocument.displayedRecord = doc;
    context.publishCollectionReportState(record.actionContext);
    selectedDocument.selectedDocId = doc.doc_id;
    selectedDocument.displayedDocId = doc.doc_id;
    selectedDocument.displayedPayload = payload;
    selectedDocument.payloadCache.set(documentTargetKey(target), payload);
    context.renderManagementUi();

    showDocPane();
    context.renderMeta(doc);
    releaseReportPresentation();
    releaseMediaDetails();
    releaseTableDetails();
    releaseDiagramDetails();
    mountDocsContentHtml(content, payload.content_html, {
      mediaRoot: workspaceConfigState.activeConfig && workspaceConfigState.activeConfig.mediaRoot,
      viewerBaseUrl: workspaceConfigState.activeConfig && workspaceConfigState.activeConfig.viewerBaseUrl
    });
    if (typeof context.mountRelatedLinks === "function") {
      context.mountRelatedLinks({
        content: content,
        payload: payload,
        documentTarget: target,
        isCurrentDocument: function () { return mountGeneration === documentMountGeneration; }
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
    renderDocumentStatus("Document not found.", true);
    context.renderManagementUi();
  }

  function renderDocLoadingState() {
    retained.forEach(function (record) { record.root.hidden = true; });
    activeRecord = null;
    if (content === outerContent) outerContent.replaceChildren();
    content = document.createElement("div");
    content.className = "docsViewer__documentMount";
    if (transientContent) transientContent.remove();
    transientContent = content;
    outerContent.appendChild(content);
    showDocPane();
    clearCollectionReportState("navigation-start", nextDocumentMountGeneration());
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
      outerContent.hidden = Boolean(projection.contentHidden);
    }
  }

  if (context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    var key = documentTargetKey(change.target);
    var record = retained.get(key);
    if (change.deleted) { if (record) releaseRecord(record); return; }
    if (!record) return;
    record.committedRecord = change.record;
    var policy = typeof record.doc.publication_ignored === "boolean" ? { publication_ignored: record.doc.publication_ignored } : {};
    record.doc = Object.assign({}, policy, change.record, record.target);
    record.actionContext = Object.assign({}, record.actionContext, { documentRecord: record.doc });
    if (activeRecord === record) {
      selectedDocument.displayedRecord = record.doc;
      context.publishCollectionReportState(record.actionContext);
      context.renderManagementUi();
    }
  });
  return {
    activeMount: function () { return content; },
    actionContext: actionContext,
    capture: capture,
    restore: restore,
    restoreRetained: restoreRetained,
    retainDocuments: retainDocuments,
    scrollToHash: scrollToHash,
    handleMissingDoc: handleMissingDoc,
    handlePayloadError: handlePayloadError,
    hideDocPane: hideDocPane,
    renderDocLoadingState: renderDocLoadingState,
    renderPayload: renderPayload,
    showDocPane: showDocPane
  };
}
