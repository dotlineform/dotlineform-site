import {
  buildChildrenMap,
  hasHiddenAncestor,
  compareDocs,
  isDocHidden,
  isDocViewable,
  normalizeDocIdSet
} from "./docs-viewer-tree.js";
import {
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  initDocsViewerBookmarks
} from "./docs-viewer-bookmarks.js";
import {
  appendAssetVersion,
  fetchIndexWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath,
  readAssetVersion
} from "./docs-viewer-data.js";
import {
  formatText,
  getConfigText,
  getConfigValue,
  initDocsViewerConfigController
} from "./docs-viewer-config-controller.js";
import {
  initDocsViewerDocumentController
} from "./docs-viewer-document-controller.js";
import {
  initDocsViewerSearchController
} from "./docs-viewer-search-controller.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";
import {
  initDocsViewerSidebarRenderer
} from "./docs-viewer-sidebar.js";
import {
  buildIndexPanelStorageKey,
  buildLegacySidebarStorageKey,
  nextIndexPanelState,
  persistIndexPanelState,
  projectIndexPanelState,
  readIndexPanelState
} from "./docs-viewer-index-panel.js";
import {
  applyViewerRoute,
  buildViewerUrl,
  buildViewerUrlForScope,
  handleViewerPopstate,
  loadViewerDoc,
  resolveViewerRouteDocId,
  routeFromAnchorHref,
  setViewerHistory
} from "./docs-viewer-router.js";

(function () {
  var root = document.getElementById("docsViewerRoot");
  if (!root) return;

  var nav = document.getElementById("docsViewerNav");
  var sidebarToggle = document.getElementById("docsViewerSidebarToggle");
  var status = document.getElementById("docsViewerStatus");
  var meta = document.getElementById("docsViewerMeta");
  var pathEl = document.getElementById("docsViewerPath");
  var updatedEl = document.getElementById("docsViewerUpdated");
  var summaryEl = document.getElementById("docsViewerSummary");
  var bookmarkRow = document.getElementById("docsViewerBookmarkRow");
  var bookmarkToggle = document.getElementById("docsViewerBookmarkToggle");
  var statusPills = document.getElementById("docsViewerStatusPills");
  var content = document.getElementById("docsViewerContent");
  var scopeSelect = document.getElementById("docsViewerScopeSelect");
  var recentButton = document.getElementById("docsViewerRecentButton");
  var searchInput = document.getElementById("docsViewerSearchInput");
  var resultsStatus = document.getElementById("docsViewerResultsStatus");
  var results = document.getElementById("docsViewerResults");
  var more = document.getElementById("docsViewerMore");

  var allowManagement = root.dataset.allowManagement === "true";
  var allowScopeQuery = root.dataset.allowScopeQuery === "true";
  var docsViewerConfigUrl = String(root.dataset.docsViewerConfigUrl || "").trim();
  var routeViewerBaseUrl = String(root.dataset.viewerBaseUrl || "").trim();
  var indexUrl = appendAssetVersion(root.dataset.indexUrl);
  var viewerBaseUrl = routeViewerBaseUrl || window.location.pathname;
  var viewerScope = String(root.dataset.viewerScope || "").trim();
  var includeScopeParam = root.dataset.includeScopeParam === "true";
  var defaultRouteDocId = String(root.dataset.defaultDocId || "").trim();
  var viewerPathname = new URL(viewerBaseUrl, window.location.origin).pathname;
  var searchIndexUrl = appendAssetVersion(root.dataset.searchIndexUrl);
  var uiTextUrl = String(root.dataset.uiTextUrl || "").trim();
  var reportRegistryUrl = String(root.dataset.reportRegistryUrl || "").trim();
  var managementBaseUrl = allowManagement ? String(root.dataset.managementBaseUrl || "").trim().replace(/\/+$/, "") : "";
  var generatedBaseUrl = String(root.dataset.generatedBaseUrl || "").trim().replace(/\/+$/, "") || managementBaseUrl;
  var openImportOnLoad = allowManagement && new URLSearchParams(window.location.search).get("import") === "1";
  var SEARCH_BATCH_SIZE = 50;
  var SEARCH_DEBOUNCE_MS = 140;
  var DEFAULT_RECENT_LIMIT = 10;
  var BOOKMARK_DB_NAME = "dotlineform-docs-viewer";
  var BOOKMARK_DB_VERSION = 1;
  var BOOKMARK_STORE_NAME = "favorites";
  var MANAGEMENT_MODE = "manage";
  var MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS = 60;
  var MANAGEMENT_CAPABILITY_RETRY_DELAY_MS = 500;
  var RELOAD_RETRY_ATTEMPTS = 12;
  var RELOAD_RETRY_DELAY_MS = 250;
  var UI_STATUS_EMOJI_MAX_LENGTH = 8;
  var SIDEBAR_COLLAPSE_MEDIA = "(min-width: 821px)";
  var bookmarkScope = viewerScope || viewerPathname || "docs";
  var indexPanelStorageKey = buildIndexPanelStorageKey(bookmarkScope);
  var legacySidebarStorageKey = buildLegacySidebarStorageKey(bookmarkScope);
  var assetVersion = readAssetVersion(document);
  var managementController = null;
  var managementControllerRequestPromise = null;
  var bookmarkController = null;
  var documentController = null;

  var state = {
    allDocs: [],
    allDocsById: new Map(),
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
    searchRouteActive: false,
    recentModeActive: false,
    recentLimit: DEFAULT_RECENT_LIMIT,
    docsViewerConfigLoaded: false,
    docsViewerConfigRequestPromise: null,
    scopeConfigs: [],
    scopeConfigsById: new Map(),
    defaultScopeId: "",
    viewerConfigLoaded: false,
    viewerConfigRequestPromise: null,
    uiStatuses: [],
    uiStatusByValue: new Map(),
    statusMenuOpen: false,
    bookmarks: [],
    bookmarksLoaded: false,
    bookmarkSupport: Boolean(window.indexedDB),
    editingBookmarkKey: "",
    pendingBookmarkFocusKey: "",
    managementMode: false,
    managementChecked: false,
    managementAvailable: false,
    managementBusy: false,
    managementCapabilities: null,
    managementCapabilityCheckId: 0,
    managementMessage: "",
    managementMessageIsError: false,
    managementStatusOwnsViewerStatus: false,
    generatedDataReadChecked: false,
    generatedDataReadAvailable: false,
    generatedDataReadRequestPromise: null,
    managementText: {
      archiveUnavailableNote: "Archive is unavailable for this scope until `archive` exists.",
      checkingNote: "Checking manage mode...",
      clearSearchNote: "Clear search to manage the current doc.",
      undoMoveLabel: "Undo move",
      undoMoveStatus: "Undoing move...",
      serverNotConfiguredError: "Local docs-management server is not configured.",
      unavailableNote: "Manage mode unavailable: local docs server unavailable for this scope.",
      cancelButton: "Cancel",
      confirmContinueButton: "Continue",
      viewableAncestorPrompt: "Showing this doc also requires showing these parent docs:\n\n{titles}\n\nContinue?",
      viewableAncestorTitle: "Show parent docs",
      viewableDescendantPrompt: "Choose whether to show only this doc or include its descendant docs.",
      viewableDescendantTitle: "Show descendants",
      viewableDescendantSelectedLabel: "Selected doc only",
      viewableDescendantAllLabel: "Selected doc and descendants",
      viewableInvalidChoice: "Show update cancelled: expected `all` or `selected`.",
      createDocTitle: "New doc title",
      createChildDocTitle: "New child title",
      createSiblingDocTitle: "New sibling title",
      createDocLabel: "title",
      createDocDefaultTitle: "New Doc",
      createDocButton: "Create",
      archiveConfirmTitle: "Confirm archive",
      archiveConfirmBody: "Archive {title}?",
      archiveConfirmButton: "Archive",
      deleteConfirmTitle: "Confirm delete",
      deleteConfirmButton: "Delete",
      metadataStatusLabel: "status",
      metadataStatusNoneOption: "<none>",
      metadataStatusSelectedSuffix: " (selected)",
      metadataHiddenLabel: "hidden",
      metadataParentRootOption: "Root",
      metadataParentInvalid: "Select a parent from the search field suggestions or enter Root.",
      metadataParentNoMatches: "No matching parent docs.",
      docHiddenEmoji: "🚫",
      statusMenuLabel: "Document status",
      statusPillSetLabel: "Set status: {label}",
      statusPillClearLabel: "Clear status: {label}",
      statusPillReadonlyLabel: "Status: {label}",
      statusPillSaving: "Saving status for {title}...",
      statusPillSaved: "Status saved.",
      statusPillFailed: "Status update failed.",
      settingsLoading: "Loading settings...",
      settingsEmpty: "No editable settings are available for this scope.",
      settingsSaving: "Saving settings...",
      settingsSaved: "Settings saved.",
      settingsLoadFailed: "Settings unavailable.",
      settingsSaveFailed: "Settings save failed.",
      normalizeOrderTitle: "Normalize order",
      normalizeOrderPrompt: "Choose which sibling group to renumber with sparse sort_order values.",
      normalizeOrderButton: "Normalize",
      normalizeOrderRunning: "Normalizing order...",
      normalizeOrderDone: "Order normalized.",
      normalizeOrderFailed: "Normalize order failed.",
      normalizeOrderRequired: "Choose an order target.",
      normalizeOrderRootLabel: "Root",
      normalizeOrderRootChoiceLabel: "Root sibling group",
      normalizeOrderCurrentSiblingsLabel: "Current sibling group under {parent}",
      normalizeOrderSelectedChildrenLabel: "Children of {title}",
      normalizeOrderWholeScopeLabel: "All sibling groups in this scope",
      scopeNewButton: "New scope",
      scopeDeleteMenuButton: "Delete scope",
      scopeCreateTitle: "New scope",
      scopeCreateIntro: "Create a Docs Viewer scope through the local management server.",
      scopeIdLabel: "scope id",
      scopeTitleLabel: "title",
      scopePublishingModeLabel: "publishing mode",
      scopePublicReadonlyMode: "public read-only scope",
      scopeLocalCommittedMode: "local-only committed scope",
      scopeLocalUncommittedMode: "local-only uncommitted scope",
      scopePublicReadonlyModeNote: "Creates a source root, scope config, read-only route, manifest record, and generated outputs when requested.",
      scopeLocalCommittedModeNote: "Creates a source root, scope config, manifest record, and generated outputs when requested. No public route is created.",
      scopeLocalUncommittedModeNote: "Creates local-only scope files and records the result as uncommitted local drift. No public route is created.",
      scopeSourceRootLabel: "source root",
      scopeDefaultDocIdLabel: "default doc id",
      scopePublicRoutePathLabel: "public route path",
      scopeWriteGeneratedLabel: "write generated outputs immediately",
      scopeBuildSearchLabel: "build inline search",
      scopePreviewButton: "Preview",
      scopeSaveButton: "Save",
      scopeDeleteButton: "Delete",
      scopeResultOkButton: "OK",
      scopeCreateRequiredMessage: "Enter the required scope fields.",
      scopeCreateRouteRequiredMessage: "Enter a public route path for public read-only scopes.",
      scopeCreatePreviewing: "Previewing new scope...",
      scopeCreatePreviewTitle: "Preview new scope",
      scopeCreateSaving: "Saving new scope...",
      scopeCreateFailed: "New scope failed.",
      scopeCreateResultTitle: "Scope created",
      scopeDeleteTitle: "Delete scope",
      scopeDeleteIntro: "Select the user-created scope to delete.",
      scopeDeleteTargetLabel: "scope",
      scopeDeleteRequiredMessage: "Select a scope to delete.",
      scopeDeleteNoTargets: "No user-created scopes are eligible for deletion.",
      scopeDeletePreviewing: "Previewing scope deletion...",
      scopeDeletePreviewTitle: "Preview delete scope",
      scopeDeleteDeleting: "Deleting scope...",
      scopeDeleteFailed: "Delete scope failed.",
      scopeDeleteBlocked: "Delete scope is blocked.",
      scopeDeleteBlockedTitle: "Delete blocked",
      scopeDeleteResultTitle: "Scope deleted",
      importCancelButton: "Cancel",
      copyLinkLabel: "Copy Link",
      copyLinkStatus: "Copied link for {title}.",
      copyLinkFailed: "Copy link failed."
    },
    showHidden: true,
    reloadNonce: "",
    reloadExpectedDocId: "",
    pendingBusyCount: 0,
    moveUndo: null,
    metadataEditingDocId: "",
    metadataRestoreFocusId: "",
    nonLoadableDocIds: new Set(),
    manageOnlyTreeRootIds: new Set(),
    showUpdatedDate: true,
    indexPanelState: readCurrentIndexPanelState()
  };
  var sidebarRenderer = initDocsViewerSidebarRenderer({
    canDragCurrentDoc: canDragCurrentDoc,
    meta: meta,
    nav: nav,
    pathEl: pathEl,
    renderBookmarkToggle: renderBookmarkToggle,
    renderStatusPills: renderStatusPills,
    state: state,
    statusForIndexDoc: statusForIndexDoc,
    summaryEl: summaryEl,
    updateNavDragState: updateNavDragState,
    updatedEl: updatedEl,
    viewerTargetDocId: viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentController = initDocsViewerDocumentController({
    allowManagement: allowManagement,
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    clearResultsStatus: clearResultsStatus,
    content: content,
    dataRequestOptions: dataRequestOptions,
    hasActiveQuery: hasActiveQuery,
    managementBaseUrl: function () { return managementBaseUrl; },
    meta: meta,
    more: more,
    renderBookmarkToggle: renderBookmarkToggle,
    renderBookmarkUi: renderBookmarkUi,
    renderManagementUi: renderManagementUi,
    renderMeta: renderMeta,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    renderStatusPills: renderStatusPills,
    reportRegistryUrl: function () { return reportRegistryUrl; },
    results: results,
    scopeConfigs: function () { return state.scopeConfigs; },
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    state: state,
    viewerScope: function () { return viewerScope; },
    viewerUrlForScope: viewerUrlForScope
  });
  var searchController = initDocsViewerSearchController({
    applyCurrentRoute: applyCurrentRoute,
    cancelSearchDebounce: cancelSearchDebounce,
    dataRequestOptions: dataRequestOptions,
    defaultDocId: defaultDocId,
    hideContextMenu: hideContextMenu,
    hideDocPane: hideDocPane,
    hasActiveQuery: hasActiveQuery,
    more: more,
    recentButton: recentButton,
    resultsStatus: resultsStatus,
    resolveDocId: resolveDocId,
    results: results,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchDebounceMs: SEARCH_DEBOUNCE_MS,
    searchIndexUrl: function () { return searchIndexUrl; },
    searchInput: searchInput,
    setHistory: setHistory,
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    showRecentPane: showRecentPane,
    showSearchPane: showSearchPane,
    startBusy: startBusy,
    state: state,
    viewerScope: function () { return viewerScope; },
    viewerTargetDocId: viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  var configController = initDocsViewerConfigController({
    allowScopeQuery: allowScopeQuery,
    applyRouteGlobals: applyRouteGlobals,
    dataRequestOptions: dataRequestOptions,
    defaultRecentLimit: DEFAULT_RECENT_LIMIT,
    docsViewerConfigUrl: docsViewerConfigUrl,
    getCurrentMode: getCurrentMode,
    managementController: function () { return managementController; },
    managementMode: MANAGEMENT_MODE,
    recentButton: recentButton,
    renderRecentMode: renderRecentMode,
    renderSidebar: renderSidebar,
    renderStatusPills: renderStatusPills,
    root: root,
    routeViewerBaseUrl: routeViewerBaseUrl,
    scopeSelect: scopeSelect,
    state: state,
    uiStatusEmojiMaxLength: UI_STATUS_EMOJI_MAX_LENGTH,
    uiTextUrl: uiTextUrl,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerScope: function () { return viewerScope; }
  });

  function dataRequestOptions(overrides) {
    var settings = overrides || {};
    return Object.assign({
      assetVersion: assetVersion,
      reloadNonce: state.reloadNonce,
      reloadExpectedDocId: state.reloadExpectedDocId,
      reloadRetryAttempts: RELOAD_RETRY_ATTEMPTS,
      reloadRetryDelayMs: RELOAD_RETRY_DELAY_MS,
      managementAvailable: state.managementAvailable,
      managementBaseUrl: generatedBaseUrl,
      fetch: function (url, options) {
        return window.fetch(url, options);
      },
      setTimeout: function (resolve, delayMs) {
        return window.setTimeout(resolve, delayMs);
      },
      checkGeneratedDataReadCapability: function () {
        return checkGeneratedDataReadCapability(settings.viewerScope || viewerScope);
      },
      scopeSupportsGeneratedSearchReads: function () {
        return scopeGeneratedCapability(state.managementCapabilities || {}, settings.viewerScope || viewerScope, "generated_search_reads");
      }
    }, settings);
  }

  function scopeGeneratedCapability(capabilities, scope, key) {
    var scopeCaps = capabilities && capabilities.scopes ? capabilities.scopes[scope] : null;
    return Boolean(
      capabilities &&
      capabilities.generated_data_reads &&
      scopeCaps &&
      scopeCaps.available &&
      scopeCaps[key]
    );
  }

  function readGeneratedCapabilities() {
    if (!generatedBaseUrl) return Promise.resolve(null);
    return window.fetch(generatedBaseUrl + "/capabilities", {
      headers: { Accept: "application/json" },
      cache: "no-store"
    })
      .then(function (response) {
        if (!response.ok) return null;
        return response.json();
      })
      .catch(function () {
        return null;
      });
  }

  function checkGeneratedDataReadCapability(scope) {
    var targetScope = String(scope || viewerScope || "").trim();
    if (!generatedBaseUrl) {
      state.generatedDataReadChecked = true;
      state.generatedDataReadAvailable = false;
      return Promise.resolve(false);
    }
    if (state.generatedDataReadChecked) {
      if (state.managementCapabilities && targetScope) {
        return Promise.resolve(scopeGeneratedCapability(state.managementCapabilities, targetScope, "generated_data_reads"));
      }
      return Promise.resolve(state.generatedDataReadAvailable);
    }
    if (state.generatedDataReadRequestPromise) {
      return state.generatedDataReadRequestPromise;
    }

    state.generatedDataReadRequestPromise = readGeneratedCapabilities()
      .then(function (payload) {
        if (!payload) {
          state.generatedDataReadAvailable = false;
          state.generatedDataReadChecked = true;
          return false;
        }
        state.managementCapabilities = payload.capabilities || null;
        state.generatedDataReadAvailable = scopeGeneratedCapability(state.managementCapabilities, viewerScope, "generated_data_reads");
        state.generatedDataReadChecked = true;
        return scopeGeneratedCapability(state.managementCapabilities, targetScope || viewerScope, "generated_data_reads");
      })
      .catch(function () {
        state.generatedDataReadAvailable = false;
        state.generatedDataReadChecked = true;
        return false;
      })
      .finally(function () {
        state.generatedDataReadRequestPromise = null;
      });

    return state.generatedDataReadRequestPromise;
  }

  function managementContext() {
    return {
      MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS: MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS,
      MANAGEMENT_CAPABILITY_RETRY_DELAY_MS: MANAGEMENT_CAPABILITY_RETRY_DELAY_MS,
      MANAGEMENT_MODE: MANAGEMENT_MODE,
      SEARCH_BATCH_SIZE: SEARCH_BATCH_SIZE,
      applyDocVisibility: applyDocVisibility,
      cancelSearchDebounce: cancelSearchDebounce,
      cssEscape: cssEscape,
      currentViewerConfig: function () { return state.viewerConfig || {}; },
      defaultDocId: defaultDocId,
      defaultRouteDocId: function () { return defaultRouteDocId; },
      escapeHtml: escapeHtml,
      findAllDocById: findAllDocById,
      formatText: formatText,
      getConfigText: getConfigText,
      getConfigValue: getConfigValue,
      getCurrentMode: getCurrentMode,
      loadDoc: loadDoc,
      loadIndex: loadIndex,
      managementBaseUrl: managementBaseUrl,
      nav: nav,
      renderBookmarkUi: renderBookmarkUi,
      renderRecentMode: renderRecentMode,
      renderSearchMode: renderSearchMode,
      renderSidebar: renderSidebar,
      root: root,
      searchInput: searchInput,
      setHistory: setHistory,
      setStatus: setStatus,
      state: state,
      markdownDocLink: markdownDocLink,
      viewerScope: function () { return viewerScope; }
    };
  }

  function loadManagementController() {
    if (!allowManagement) return Promise.resolve(null);
    if (managementController) return Promise.resolve(managementController);
    if (managementControllerRequestPromise) return managementControllerRequestPromise;

    managementControllerRequestPromise = import("./docs-viewer-management.js")
      .then(function (module) {
        managementController = module.initDocsViewerManagement(managementContext());
        renderSidebar();
        return managementController;
      })
      .catch(function (error) {
        console.warn("docs_viewer: management controller unavailable", error);
        return null;
      })
      .finally(function () {
        managementControllerRequestPromise = null;
      });

    return managementControllerRequestPromise;
  }

  function routeScopeFromUrl() {
    return configController.routeScopeFromUrl();
  }

  function applyRouteGlobals(values) {
    viewerScope = values.viewerScope;
    indexUrl = values.indexUrl;
    searchIndexUrl = values.searchIndexUrl;
    defaultRouteDocId = values.defaultRouteDocId;
    viewerBaseUrl = values.viewerBaseUrl;
    includeScopeParam = values.includeScopeParam;
    viewerPathname = values.viewerPathname;
    bookmarkScope = viewerScope || viewerPathname || "docs";
    indexPanelStorageKey = buildIndexPanelStorageKey(bookmarkScope);
    legacySidebarStorageKey = buildLegacySidebarStorageKey(bookmarkScope);
    state.indexPanelState = readCurrentIndexPanelState();
  }

  function loadDocsViewerConfig() {
    return configController.loadDocsViewerConfig();
  }

  function handleScopeChange() {
    configController.handleScopeChange();
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

  function getCurrentMode() {
    if (!allowManagement) return "";
    return new URLSearchParams(window.location.search).get("mode") || "";
  }

  function hasCanonicalScopeInUrl() {
    if (!includeScopeParam || !viewerScope) return true;
    return new URLSearchParams(window.location.search).get("scope") === viewerScope;
  }

  function hasDisallowedModeInUrl() {
    return !allowManagement && new URLSearchParams(window.location.search).has("mode");
  }

  function hasDisallowedScopeInUrl() {
    return !allowScopeQuery && new URLSearchParams(window.location.search).has("scope");
  }

  function hasActiveQuery(query) {
    return Boolean(normalizeSearchText(typeof query === "string" ? query : state.searchQuery));
  }

  function setRecentModeActive(active) {
    state.recentModeActive = Boolean(active);
    renderRecentButtonState();
  }

  function renderRecentButtonState() {
    if (!recentButton) return;
    recentButton.setAttribute("aria-pressed", state.recentModeActive ? "true" : "false");
  }

  function sidebarCollapseAvailable() {
    if (!window.matchMedia) return window.innerWidth > 820;
    return window.matchMedia(SIDEBAR_COLLAPSE_MEDIA).matches;
  }

  function readCurrentIndexPanelState() {
    return readIndexPanelState({
      storage: window.localStorage,
      storageKey: indexPanelStorageKey,
      legacyStorageKey: legacySidebarStorageKey
    });
  }

  function persistCurrentIndexPanelState() {
    persistIndexPanelState({
      storage: window.localStorage,
      storageKey: indexPanelStorageKey,
      state: state.indexPanelState
    });
  }

  function renderIndexPanelState() {
    var projection = projectIndexPanelState(state.indexPanelState, {
      available: sidebarCollapseAvailable()
    });
    root.dataset.indexPanelState = projection.activeState;
    root.dataset.sidebarState = projection.legacySidebarState;
    if (!sidebarToggle) return;

    sidebarToggle.hidden = projection.toggleHidden;
    sidebarToggle.setAttribute("aria-expanded", projection.toggleAriaExpanded);
    sidebarToggle.setAttribute("aria-label", projection.toggleLabel);
    sidebarToggle.title = projection.toggleLabel;
    var icon = sidebarToggle.querySelector(".docsViewer__sidebarToggleIcon");
    if (icon) {
      icon.textContent = projection.toggleIcon;
    }
  }

  function toggleIndexPanelState() {
    if (!sidebarCollapseAvailable()) return;
    state.indexPanelState = nextIndexPanelState(state.indexPanelState);
    persistCurrentIndexPanelState();
    hideContextMenu();
    renderIndexPanelState();
  }

  function loadViewerConfig() {
    return configController.loadViewerConfig();
  }

  function renderBookmarkUi() {
    if (bookmarkController) {
      bookmarkController.renderUi();
      return;
    }
    renderStatusPills();
  }

  function renderBookmarkToggle() {
    if (bookmarkController) {
      bookmarkController.renderToggle();
      return;
    }
    if (bookmarkToggle) bookmarkToggle.hidden = true;
  }

  function renderStatusPills() {
    if (!statusPills) return;
    if (managementController && typeof managementController.renderStatusPills === "function") {
      managementController.renderStatusPills();
      return;
    }
    statusPills.hidden = true;
    statusPills.innerHTML = "";
    state.statusMenuOpen = false;
  }

  function initializeBookmarks() {
    if (bookmarkController) bookmarkController.initialize();
  }

  function viewerUrl(docId, hash, query) {
    return buildViewerUrl({
      docId: docId,
      hash: hash,
      includeScopeParam: includeScopeParam,
      managementMode: state.managementMode,
      managementModeValue: MANAGEMENT_MODE,
      origin: window.location.origin,
      query: query,
      viewerBaseUrl: viewerBaseUrl,
      viewerScope: viewerScope
    });
  }

  function viewerUrlForScope(scope, docId, options) {
    return buildViewerUrlForScope({
      allowManagement: allowManagement,
      docId: docId,
      managementModeValue: MANAGEMENT_MODE,
      manage: Boolean(options && options.manage),
      origin: window.location.origin,
      routeViewerBaseUrl: routeViewerBaseUrl,
      scope: scope,
      scopeConfigsById: state.scopeConfigsById,
      viewerBaseUrl: viewerBaseUrl,
      viewerScope: viewerScope
    });
  }

  function escapeMarkdownLinkText(value) {
    return String(value || "")
      .replace(/\\/g, "\\\\")
      .replace(/\[/g, "\\[")
      .replace(/\]/g, "\\]");
  }

  function markdownDocLink(doc) {
    if (!doc || !doc.doc_id) return "";
    var title = escapeMarkdownLinkText(doc.title || doc.doc_id);
    var url = viewerUrlForScope(viewerScope, viewerTargetDocId(doc.doc_id), { manage: false });
    return "[" + title + "](" + url + ")";
  }

  function isManageOnlyTreeDoc(doc) {
    if (!doc || state.manageOnlyTreeRootIds.size === 0) return false;
    var visited = new Set();
    var current = doc;
    while (current && current.doc_id && !visited.has(current.doc_id)) {
      if (state.manageOnlyTreeRootIds.has(current.doc_id)) return true;
      visited.add(current.doc_id);
      current = current.parent_id ? state.allDocsById.get(current.parent_id) : null;
    }
    return false;
  }

  function shouldIncludeDoc(doc) {
    if (!state.managementMode && isManageOnlyTreeDoc(doc)) return false;
    if (!state.managementMode) return isDocViewable(doc) && !hasHiddenAncestor(doc, state.allDocsById);
    return isDocViewable(doc) || state.showHidden;
  }

  function applyDocVisibility() {
    state.allDocsById = new Map(
      state.allDocs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.docs = state.allDocs.filter(shouldIncludeDoc).slice().sort(compareDocs);
    state.docsById = new Map(
      state.docs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.childrenByParent = buildChildrenMap(state.docs, {
      managementMode: state.managementMode,
      showHidden: state.showHidden
    });
  }

  function findAllDocById(docId) {
    for (var i = 0; i < state.allDocs.length; i += 1) {
      if (state.allDocs[i].doc_id === docId) return state.allDocs[i];
    }
    return null;
  }

  function syncHiddenVisibilityForRequestedDoc() {
    if (!state.managementMode) return;
    var requestedDocId = getCurrentDocId();
    if (!requestedDocId) return;
    var requestedDoc = findAllDocById(requestedDocId);
    if (requestedDoc && isDocHidden(requestedDoc)) {
      state.showHidden = true;
    }
  }

  function isNonLoadableDoc(doc) {
    return Boolean(doc) && state.nonLoadableDocIds.has(doc.doc_id);
  }

  function statusForIndexDoc(doc) {
    if (!doc || isNonLoadableDoc(doc)) return null;
    if (!state.managementMode && isManageOnlyTreeDoc(doc)) return null;
    if (!isDocViewable(doc) && !state.managementMode) return null;
    var statusValue = String(doc.ui_status || "").trim();
    return statusValue ? state.uiStatusByValue.get(statusValue) || null : null;
  }

  function firstLoadableDescendantDocId(parentId) {
    var children = state.childrenByParent.get(parentId) || [];
    for (var i = 0; i < children.length; i += 1) {
      var child = children[i];
      if (!isNonLoadableDoc(child)) {
        return child.doc_id;
      }
      var nestedDocId = firstLoadableDescendantDocId(child.doc_id);
      if (nestedDocId) {
        return nestedDocId;
      }
    }
    return "";
  }

  function resolveLoadableDocId(docId) {
    var doc = state.docsById.get(docId);
    if (!doc) return "";
    if (!isNonLoadableDoc(doc)) return doc.doc_id;
    return firstLoadableDescendantDocId(doc.doc_id);
  }

  function viewerTargetDocId(docId) {
    var targetDocId = resolveLoadableDocId(docId);
    if (targetDocId) return targetDocId;

    var doc = state.docsById.get(docId);
    if (isNonLoadableDoc(doc)) {
      return defaultDocId();
    }

    return docId;
  }

  function flattenRoots() {
    var roots = state.childrenByParent.get("") || [];
    if (roots.length > 0) return roots;
    return state.docs.slice().sort(compareDocs);
  }

  function defaultDocId() {
    var roots = flattenRoots();
    for (var i = 0; i < roots.length; i += 1) {
      var docId = resolveLoadableDocId(roots[i].doc_id);
      if (docId) {
        return docId;
      }
    }
    return "";
  }

  function buildTrail(docId) {
    return sidebarRenderer.buildTrail(docId);
  }

  function expandTrail(docId) {
    sidebarRenderer.expandTrail(docId);
  }

  function renderSidebar() {
    sidebarRenderer.renderSidebar();
  }

  function renderMeta(doc) {
    sidebarRenderer.renderMeta(doc);
  }

  function setStatus(message, isError) {
    status.textContent = message;
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function clearResultsStatus() {
    if (!resultsStatus) return;
    resultsStatus.textContent = "";
    resultsStatus.hidden = true;
    resultsStatus.classList.remove("is-error");
  }

  function syncBusyState() {
    var isBusy = state.pendingBusyCount > 0;
    root.classList.toggle("is-busy", isBusy);
    root.setAttribute("aria-busy", isBusy ? "true" : "false");
  }

  function startBusy() {
    state.pendingBusyCount += 1;
    syncBusyState();
    var stopped = false;
    return function stopBusy() {
      if (stopped) return;
      stopped = true;
      state.pendingBusyCount = Math.max(0, state.pendingBusyCount - 1);
      syncBusyState();
    };
  }

  function hideContextMenu() {
    if (managementController) {
      managementController.hideContextMenu();
    }
  }

  function updateNavDragState() {
    if (managementController) {
      managementController.updateNavDragState();
    }
  }

  function canDragCurrentDoc(doc) {
    return Boolean(managementController && managementController.canDragCurrentDoc(doc));
  }

  function renderManagementUi() {
    if (managementController) {
      managementController.render();
    }
  }

  function initializeManagement() {
    if (!allowManagement) return;
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    if (!state.managementMode) return;
    loadManagementController().then(function (controller) {
      if (controller) controller.initialize();
    });
  }

  function hideDocPane() {
    documentController.hideDocPane();
  }

  function showDocPane() {
    documentController.showDocPane();
  }

  function showSearchPane() {
    documentController.showSearchPane();
  }

  function showRecentPane() {
    documentController.showRecentPane();
  }

  function renderPayload(doc, payload, hash) {
    documentController.renderPayload(doc, payload, hash);
  }

  function setHistory(docId, hash, query, mode) {
    setViewerHistory({
      docId: docId,
      hash: hash,
      history: window.history,
      includeScopeParam: includeScopeParam,
      managementMode: state.managementMode,
      managementModeValue: MANAGEMENT_MODE,
      mode: mode,
      origin: window.location.origin,
      query: query,
      viewerBaseUrl: viewerBaseUrl,
      viewerScope: viewerScope
    });
  }

  function cancelSearchDebounce() {
    if (state.searchDebounceId == null) return;
    window.clearTimeout(state.searchDebounceId);
    state.searchDebounceId = null;
  }

  function handleMissingDoc() {
    documentController.handleMissingDoc();
  }

  function renderDocLoadingState(doc) {
    documentController.renderDocLoadingState(doc);
  }

  function fetchDocPayload(doc, docId) {
    var stopBusy = startBusy();
    return fetchPreferredGeneratedJson(
      doc.content_url,
      "Failed to load " + doc.content_url,
      managementReloadPath("/docs/generated/payload", { scope: viewerScope, doc_id: docId }),
      dataRequestOptions({ useSearchCapability: false })
    ).finally(stopBusy);
  }

  function handlePayloadError(error) {
    documentController.handlePayloadError(error);
  }

  function loadDoc(docId, options) {
    return loadViewerDoc({
      docId: docId,
      expandTrailForDoc: expandTrail,
      expandTrail: !options || options.expandTrail !== false,
      fetchPayload: fetchDocPayload,
      handleMissingDoc: handleMissingDoc,
      handlePayloadError: handlePayloadError,
      hash: options && options.hash ? options.hash : "",
      historyMode: options && options.historyMode ? options.historyMode : "push",
      renderBookmarkUi: renderBookmarkUi,
      renderLoadingState: renderDocLoadingState,
      renderPayload: renderPayload,
      resolveLoadableDocId: resolveLoadableDocId,
      setHistory: setHistory,
      setRecentModeActive: setRecentModeActive,
      state: state
    });
  }

  function routeFromAnchor(anchor) {
    return routeFromAnchorHref(anchor.href, {
      allowManagement: allowManagement,
      allowScopeQuery: allowScopeQuery,
      currentHref: window.location.href,
      currentMode: getCurrentMode(),
      includeScopeParam: includeScopeParam,
      managementModeValue: MANAGEMENT_MODE,
      origin: window.location.origin,
      viewerPathname: viewerPathname,
      viewerScope: viewerScope
    });
  }

  function bindLinkInterception() {
    root.addEventListener("click", function (event) {
      if (managementController && managementController.handleRootClick(event)) {
        return;
      }
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
      if (route.navigateUrl) {
        window.location.assign(route.navigateUrl);
        return;
      }
      cancelSearchDebounce();
      state.searchQuery = "";
      state.searchVisibleCount = SEARCH_BATCH_SIZE;
      if (searchInput) {
        searchInput.value = "";
      }
      loadDoc(route.docId, {
        historyMode: "push",
        hash: route.hash
      });
    });

    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", function () {
        toggleIndexPanelState();
      });
    }

    if (scopeSelect) {
      scopeSelect.addEventListener("change", function () {
        handleScopeChange();
      });
    }

    if (bookmarkController) {
      bookmarkController.bind();
    }

    document.addEventListener("keydown", function (event) {
      if (managementController && managementController.handleDocumentKeydown(event)) {
        return;
      }
    });

    searchController.bind();
  }

  function resolveDocId() {
    return resolveViewerRouteDocId({
      requestedDocId: getCurrentDocId(),
      docsById: state.docsById,
      defaultRouteDocId: defaultRouteDocId,
      resolveLoadableDocId: resolveLoadableDocId,
      defaultDocId: defaultDocId
    });
  }

  function initializeIndex(payload) {
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    var viewerOptions = payload && payload.viewer_options && typeof payload.viewer_options === "object"
      ? payload.viewer_options
      : {};
    state.nonLoadableDocIds = normalizeDocIdSet(viewerOptions.non_loadable_doc_ids, []);
    state.manageOnlyTreeRootIds = normalizeDocIdSet(viewerOptions.manage_only_tree_root_ids, []);
    state.showUpdatedDate = viewerOptions.show_updated_date !== false;
    state.allDocs = Array.isArray(payload.docs) ? payload.docs.slice().sort(compareDocs) : [];
    syncHiddenVisibilityForRequestedDoc();
    applyDocVisibility();

    renderSidebar();
    renderBookmarkUi();

    if (state.docs.length === 0) {
      setStatus("No docs available.", true);
      return;
    }

    applyCurrentRoute({ historyMode: "replace", hash: getCurrentHash() });
  }

  function applyCurrentRoute(options) {
    return applyViewerRoute({
      applyDocVisibility: applyDocVisibility,
      currentDocId: getCurrentDocId,
      currentHash: getCurrentHash,
      currentQuery: getCurrentQuery,
      defaultDocId: defaultDocId,
      defaultRouteDocId: defaultRouteDocId,
      docHasParent: function (docId) {
        var doc = state.docsById.get(docId);
        return Boolean(doc && doc.parent_id);
      },
      expandTrail: expandTrail,
      hasActiveQuery: hasActiveQuery,
      hasCanonicalScopeInUrl: hasCanonicalScopeInUrl,
      hasDisallowedModeInUrl: hasDisallowedModeInUrl,
      hasDisallowedScopeInUrl: hasDisallowedScopeInUrl,
      hash: options && options.hash ? options.hash : "",
      historyMode: options && options.historyMode ? options.historyMode : "push",
      loadDoc: loadDoc,
      managementModeActive: function () { return getCurrentMode() === MANAGEMENT_MODE; },
      renderBookmarkUi: renderBookmarkUi,
      renderManagementUi: renderManagementUi,
      renderSearchMode: renderSearchMode,
      renderSidebar: renderSidebar,
      resolveLoadableDocId: resolveLoadableDocId,
      searchInput: searchInput,
      setHistory: setHistory,
      setRecentModeActive: setRecentModeActive,
      setStatus: setStatus,
      state: state,
      syncHiddenVisibilityForRequestedDoc: syncHiddenVisibilityForRequestedDoc
    });
  }

  function loadIndex() {
    var stopBusy = startBusy();
    return fetchIndexWithRetry(dataRequestOptions({
      indexUrl: indexUrl,
      viewerScope: viewerScope
    }))
      .then(function (payload) {
        initializeIndex(payload);
      })
      .catch(function (error) {
        state.reloadExpectedDocId = "";
        setStatus(error.message || "Failed to load docs index.", true);
        hideDocPane();
        content.textContent = "";
        throw error;
      })
      .finally(function () {
        stopBusy();
      });
  }

  function renderRecentMode() {
    searchController.renderRecentMode();
  }

  function renderSearchPendingState() {
    searchController.renderSearchPendingState();
  }

  function renderSearchMode() {
    searchController.renderSearchMode();
  }

  window.addEventListener("popstate", function () {
    handleViewerPopstate({
      allowScopeQuery: allowScopeQuery,
      applyCurrentRoute: applyCurrentRoute,
      cancelSearchDebounce: cancelSearchDebounce,
      currentHash: getCurrentHash,
      docsAvailable: function () { return state.docs.length > 0; },
      hideContextMenu: hideContextMenu,
      reloadWindow: function () { window.location.reload(); },
      routeScopeFromUrl: routeScopeFromUrl,
      setStatus: setStatus,
      viewerScope: viewerScope
    });
  });

  window.addEventListener("scroll", hideContextMenu, { passive: true });
  window.addEventListener("resize", function () {
    hideContextMenu();
    renderIndexPanelState();
  });
  window.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      hideContextMenu();
    }
  });

  bookmarkController = initDocsViewerBookmarks({
    bookmarkRow: bookmarkRow,
    bookmarkScope: function () { return bookmarkScope; },
    bookmarkToggle: bookmarkToggle,
    cancelSearchDebounce: cancelSearchDebounce,
    cssEscape: cssEscape,
    dbName: BOOKMARK_DB_NAME,
    dbVersion: BOOKMARK_DB_VERSION,
    hideContextMenu: hideContextMenu,
    loadDoc: loadDoc,
    renderStatusPills: renderStatusPills,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setStatus: setStatus,
    state: state,
    storeName: BOOKMARK_STORE_NAME
  });
  bindLinkInterception();
  var stopInitialBusy = startBusy();
  loadDocsViewerConfig()
    .then(function () {
      renderIndexPanelState();
      return loadViewerConfig();
    })
    .then(function () {
      initializeBookmarks();
      initializeManagement();
      return loadIndex();
    })
    .then(function () {
      if (openImportOnLoad && getCurrentMode() === MANAGEMENT_MODE) {
        loadManagementController().then(function (controller) {
          if (controller) controller.openImportModal();
        });
      }
    })
    .catch(function (error) {
      setStatus(error.message || "Failed to initialize Docs Viewer.", true);
      hideDocPane();
      content.textContent = "";
      if (results) results.hidden = true;
      if (more) more.hidden = true;
    })
    .finally(function () {
      stopInitialBusy();
    });

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(String(value || ""));
    }
    return String(value || "").replace(/["\\]/g, "\\$&");
  }
})();
