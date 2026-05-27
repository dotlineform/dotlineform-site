import {
  buildChildrenMap,
  hasHiddenAncestor,
  compareDocs,
  isDocHidden,
  isDocViewable
} from "./docs-viewer-tree.js";
import {
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  initDocsViewerBookmarks
} from "./docs-viewer-bookmarks.js";
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
  initDocsViewerRouteWorkflow
} from "./docs-viewer-route-workflow.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";
import {
  initDocsViewerSidebarRenderer
} from "./docs-viewer-sidebar.js";
import {
  updateDocsViewerRouteContext
} from "./docs-viewer-app-context.js";
import {
  createDocsViewerPanelLayout
} from "./docs-viewer-panel-layout.js";
import {
  createDocsViewerInfoPanelHost
} from "./docs-viewer-info-panel-host.js";
import {
  createDocsViewerHostedViewContext,
  resolveDocsViewerSelectedDoc
} from "./docs-viewer-view-context.js";
import {
  createDocsViewerCompatibilityHostedViews,
  createDocsViewerHostedViewRegistry,
  registerDocsViewerHostedViews
} from "./docs-viewer-hosted-views.js";
export function startDocsViewerRuntime(options) {
  var settings = options || {};
  var root = settings.root;
  var document = settings.document;
  var window = settings.window;
  var assetVersion = settings.assetVersion || "";
  var routeContext = settings.routeContext;
  var appShellReady = settings.appShellReady || Promise.resolve(null);
  var appShellRefs = settings.appShellRefs || {};
  if (!root || !document || !window || !routeContext) return null;

  var indexPanelRefs = appShellRefs.indexPanel;
  var nav = indexPanelRefs.nav;
  var sidebarToggle = indexPanelRefs.sidebarToggle;
  var sidebarExpand = indexPanelRefs.sidebarExpand;
  var documentShellRefs = appShellRefs.documentShell;
  var infoPanelRefs = appShellRefs.infoPanel;
  var status = appShellRefs.status;
  var meta = documentShellRefs.meta;
  var pathEl = documentShellRefs.pathEl;
  var updatedEl = documentShellRefs.updatedEl;
  var summaryEl = documentShellRefs.summaryEl;
  var bookmarkRow = appShellRefs.bookmarkRow;
  var infoToggle = documentShellRefs.infoToggle;
  var bookmarkToggle = documentShellRefs.bookmarkToggle;
  var statusPills = documentShellRefs.statusPills;
  var content = documentShellRefs.content;
  var scopeSelect = appShellRefs.headerControls.scopeSelect;
  var recentButton = appShellRefs.headerControls.recentButton;
  var searchInput = appShellRefs.headerControls.searchInput;
  var resultsStatus = documentShellRefs.resultsStatus;
  var results = documentShellRefs.results;
  var more = documentShellRefs.more;

  var allowManagement = routeContext.access.allowManagement;
  var allowScopeQuery = routeContext.access.allowScopeQuery;
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var indexUrl = routeContext.indexUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;
  var viewerScope = routeContext.viewerScope;
  var includeScopeParam = routeContext.includeScopeParam;
  var defaultRouteDocId = routeContext.defaultRouteDocId;
  var viewerPathname = routeContext.viewerPathname;
  var searchIndexUrl = routeContext.searchIndexUrl;
  var uiTextUrl = routeContext.uiTextUrl;
  var reportRegistryUrl = routeContext.reportRegistryUrl;
  var managementBaseUrl = routeContext.managementBaseUrl;
  var generatedBaseUrl = routeContext.generatedBaseUrl;
  var openImportOnLoad = routeContext.openImportOnLoad;
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
  var bookmarkScope = routeContext.bookmarkScope;
  var hostedViewRegistry = registerDocsViewerHostedViews(
    createDocsViewerHostedViewRegistry({ accessProjection: routeContext.access }),
    createDocsViewerCompatibilityHostedViews().concat(routeContext.routeConfig.hostedViews.records)
  );
  var panelLayout = createDocsViewerPanelLayout({
    root: root,
    storage: window.localStorage,
    storageScope: bookmarkScope,
    panels: routeContext.routeConfig.panels,
    routeId: routeContext.routeConfig.routeId,
    indexPanelRefs: indexPanelRefs,
    documentShellRefs: documentShellRefs,
    infoPanelRefs: infoPanelRefs,
    indexPanelAvailable: sidebarCollapseAvailable
  });
  var infoPanelHost = createDocsViewerInfoPanelHost({
    refs: infoPanelRefs,
    registry: hostedViewRegistry,
    project: function (projection) {
      panelLayout.projectInfoPanel(projection || {});
      state.viewState = panelLayout.projectViewState();
      renderInfoToggleState();
    }
  });
  var managementController = null;
  var managementControllerRequestPromise = null;
  var bookmarkController = null;
  var documentController = null;
  var routeWorkflow = null;

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
      archiveUnavailableNote: "Archive is unavailable until the archive scope exists.",
      archiveUnavailableTitle: "Archive unavailable",
      archiveScopeMissingPrompt: "archive scope doesn't exist.",
      checkingNote: "Checking manage mode...",
      clearSearchNote: "Clear search to manage the current doc.",
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
      scopeLocalCommittedMode: "committed manage-mode scope",
      scopeLocalUncommittedMode: "local-only uncommitted scope",
      scopePublicReadonlyModeNote: "Creates a source root, scope config, read-only route, manifest record, and generated outputs when requested.",
      scopeLocalCommittedModeNote: "Creates tracked source, config, manifest, and non-public generated outputs under docs-viewer/generated/ when requested. No public route is created.",
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
    metadataEditingDocId: "",
    metadataRestoreFocusId: "",
    nonLoadableDocIds: new Set(),
    manageOnlyTreeRootIds: new Set(),
    showUpdatedDate: true,
    indexPanelState: panelLayout.indexPanelState()
  };
  state.hostedViews = hostedViewRegistry;
  state.viewState = panelLayout.projectViewState();
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
    projectDocumentShell: projectDocumentShell,
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
  routeWorkflow = initDocsViewerRouteWorkflow({
    allowManagement: function () { return allowManagement; },
    allowScopeQuery: function () { return allowScopeQuery; },
    applyDocVisibility: applyDocVisibility,
    cancelSearchDebounce: cancelSearchDebounce,
    clearManagementMessageForDocChange: clearManagementMessageForDocChange,
    content: content,
    dataRequestOptions: dataRequestOptions,
    defaultDocId: defaultDocId,
    defaultRouteDocId: function () { return defaultRouteDocId; },
    expandTrail: expandTrail,
    handleManagementRootClick: function (event) {
      return Boolean(managementController && managementController.handleRootClick(event));
    },
    handleMissingDoc: handleMissingDoc,
    handlePayloadError: handlePayloadError,
    hasActiveQuery: hasActiveQuery,
    hideContextMenu: hideContextMenu,
    hideDocPane: hideDocPane,
    includeScopeParam: function () { return includeScopeParam; },
    indexUrl: function () { return indexUrl; },
    managementModeValue: MANAGEMENT_MODE,
    more: more,
    renderBookmarkUi: renderBookmarkUi,
    renderDocLoadingState: renderDocLoadingState,
    renderManagementUi: renderManagementUi,
    renderPayload: renderPayload,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    resolveLoadableDocId: resolveLoadableDocId,
    results: results,
    root: root,
    routeScopeFromUrl: routeScopeFromUrl,
    routeViewerBaseUrl: function () { return routeViewerBaseUrl; },
    scopeConfigsById: function () { return state.scopeConfigsById; },
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    startBusy: startBusy,
    state: state,
    syncHiddenVisibilityForRequestedDoc: syncHiddenVisibilityForRequestedDoc,
    updateInfoPanel: updateInfoPanel,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerPathname: function () { return viewerPathname; },
    viewerScope: function () { return viewerScope; },
    window: window
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
      docsViewerConfigUrl: docsViewerConfigUrl,
      escapeHtml: escapeHtml,
      findAllDocById: findAllDocById,
      formatText: formatText,
      getConfigText: getConfigText,
      getConfigValue: getConfigValue,
      getCurrentMode: getCurrentMode,
      loadDoc: loadDoc,
      loadIndex: loadIndex,
      managementBaseUrl: managementBaseUrl,
      managementShellRefs: appShellRefs.managementShell || {},
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
      uiTextUrl: uiTextUrl,
      markdownDocLink: markdownDocLink,
      reloadDocsViewerConfig: function () { return configController.reloadDocsViewerConfig(); },
      viewerScope: function () { return viewerScope; }
    };
  }

  function loadManagementController() {
    if (!allowManagement) return Promise.resolve(null);
    if (managementController) return Promise.resolve(managementController);
    if (managementControllerRequestPromise) return managementControllerRequestPromise;

    managementControllerRequestPromise = appShellReady
      .then(function () {
        return import("./docs-viewer-management.js");
      })
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
    routeContext = updateDocsViewerRouteContext(routeContext, values, { window: window });
    viewerScope = routeContext.viewerScope;
    indexUrl = routeContext.indexUrl;
    searchIndexUrl = routeContext.searchIndexUrl;
    defaultRouteDocId = routeContext.defaultRouteDocId;
    viewerBaseUrl = routeContext.viewerBaseUrl;
    includeScopeParam = routeContext.includeScopeParam;
    viewerPathname = routeContext.viewerPathname;
    bookmarkScope = routeContext.bookmarkScope;
    state.indexPanelState = panelLayout.setStorageScope(bookmarkScope);
  }

  function loadDocsViewerConfig() {
    return configController.loadDocsViewerConfig();
  }

  function handleScopeChange() {
    configController.handleScopeChange();
  }

  function getCurrentDocId() {
    return routeWorkflow.currentDocId();
  }

  function getCurrentHash() {
    return routeWorkflow.currentHash();
  }

  function getCurrentMode() {
    return routeWorkflow.currentMode();
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

  function renderIndexPanelState() {
    panelLayout.renderIndexPanelState();
  }

  function toggleIndexPanelState() {
    hideContextMenu();
    state.indexPanelState = panelLayout.toggleIndexPanelState();
  }

  function expandIndexPanelState() {
    hideContextMenu();
    state.indexPanelState = panelLayout.expandIndexPanelState();
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
      renderInfoToggleState();
      return;
    }
    if (bookmarkToggle) bookmarkToggle.hidden = true;
    renderInfoToggleState();
  }

  function currentSelectedDoc() {
    return resolveDocsViewerSelectedDoc({
      allDocsById: state.allDocsById,
      docsById: state.docsById,
      selectedDocId: state.selectedDocId
    });
  }

  function infoPanelContext() {
    return createDocsViewerHostedViewContext({
      allDocsById: state.allDocsById,
      buildTrail: buildTrail,
      docsById: state.docsById,
      payloadCache: state.payloadCache,
      routeAccess: routeContext.access,
      selectedDocId: state.selectedDocId,
      uiStatusByValue: state.uiStatusByValue,
      viewerScope: viewerScope,
      viewerTargetDocId: viewerTargetDocId,
      viewerUrl: viewerUrl
    });
  }

  function metadataInfoAvailable() {
    var resolved = hostedViewRegistry.resolve("metadata-info");
    return Boolean(resolved.available && resolved.view);
  }

  function renderInfoToggleState() {
    if (!infoToggle) return;
    var canShow = Boolean(currentSelectedDoc() && metadataInfoAvailable());
    var open = infoPanelHost.isOpen();
    var label = open ? "Hide document info" : "Show document info";
    projectDocumentShell({
      infoToggleHidden: !canShow,
      infoToggleLabel: label,
      infoTogglePressed: open
    });
  }

  function updateInfoPanel() {
    renderInfoToggleState();
    if (infoPanelHost.isOpen()) {
      infoPanelHost.update(infoPanelContext());
    }
  }

  function openMetadataInfoPanel() {
    if (!currentSelectedDoc()) return;
    infoPanelHost.open("metadata-info", infoPanelContext()).then(function () {
      renderInfoToggleState();
    });
  }

  function closeInfoPanel() {
    infoPanelHost.close().then(function () {
      renderInfoToggleState();
    });
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
    return routeWorkflow.viewerUrl(docId, hash, query);
  }

  function viewerUrlForScope(scope, docId, options) {
    return routeWorkflow.viewerUrlForScope(scope, docId, options);
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
    projectDocumentShell({
      resultsStatusText: "",
      resultsStatusHidden: true,
      resultsStatusError: false
    });
  }

  function projectDocumentShell(projection) {
    panelLayout.projectDocumentShell(projection || {});
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

  function clearManagementMessageForDocChange(docId) {
    var targetDocId = String(docId || "").trim();
    if (!targetDocId || targetDocId === state.selectedDocId || !state.managementMessage) return;
    state.managementMessage = "";
    state.managementMessageIsError = false;
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
    updateInfoPanel();
  }

  function showDocPane() {
    documentController.showDocPane();
  }

  function showSearchPane() {
    documentController.showSearchPane();
    updateInfoPanel();
  }

  function showRecentPane() {
    documentController.showRecentPane();
    updateInfoPanel();
  }

  function renderPayload(doc, payload, hash) {
    documentController.renderPayload(doc, payload, hash);
    updateInfoPanel();
  }

  function setHistory(docId, hash, query, mode) {
    routeWorkflow.setHistory(docId, hash, query, mode);
  }

  function cancelSearchDebounce() {
    if (state.searchDebounceId == null) return;
    window.clearTimeout(state.searchDebounceId);
    state.searchDebounceId = null;
  }

  function handleMissingDoc() {
    documentController.handleMissingDoc();
    updateInfoPanel();
  }

  function renderDocLoadingState(doc) {
    documentController.renderDocLoadingState(doc);
    updateInfoPanel();
  }

  function handlePayloadError(error) {
    documentController.handlePayloadError(error);
    updateInfoPanel();
  }

  function loadDoc(docId, options) {
    return routeWorkflow.loadDoc(docId, options);
  }

  function bindLinkInterception() {
    routeWorkflow.bindRouteLinks();

    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", function () {
        toggleIndexPanelState();
      });
    }

    if (sidebarExpand) {
      sidebarExpand.addEventListener("click", function () {
        expandIndexPanelState();
      });
    }

    if (infoToggle) {
      infoToggle.addEventListener("click", function () {
        if (infoPanelHost.isOpen()) {
          closeInfoPanel();
        } else {
          openMetadataInfoPanel();
        }
      });
    }

    if (infoPanelRefs.closeButton) {
      infoPanelRefs.closeButton.addEventListener("click", function () {
        closeInfoPanel();
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
      if (event.key === "Escape" && infoPanelHost.isOpen()) {
        closeInfoPanel();
      }
    });

    searchController.bind();
  }

  function resolveDocId() {
    return routeWorkflow.resolveDocId();
  }

  function applyCurrentRoute(options) {
    return routeWorkflow.applyCurrentRoute(options);
  }

  function loadIndex() {
    return routeWorkflow.loadIndex();
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

  routeWorkflow.bindPopstate();

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
  var initialLoadPromise = loadDocsViewerConfig()
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

  return {
    root: root,
    routeContext: function () { return routeContext; },
    appShellRefs: appShellRefs,
    state: state,
    initialLoadPromise: initialLoadPromise,
    loadManagementController: loadManagementController,
    applyCurrentRoute: applyCurrentRoute,
    loadIndex: loadIndex,
    loadDoc: loadDoc
  };
}
