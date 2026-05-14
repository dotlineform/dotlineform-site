import {
  buildChildrenMap,
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
  fetchJsonWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath,
  readAssetVersion
} from "./docs-viewer-data.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";
import {
  initDocsViewerSearchController
} from "./docs-viewer-search-controller.js";
import {
  initDocsViewerSidebarRenderer
} from "./docs-viewer-sidebar.js";

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
  var SIDEBAR_STORAGE_PREFIX = "dotlineform-docs-viewer-sidebar:";
  var bookmarkScope = viewerScope || viewerPathname || "docs";
  var sidebarStorageKey = SIDEBAR_STORAGE_PREFIX + bookmarkScope;
  var assetVersion = readAssetVersion(document);
  var managementController = null;
  var managementControllerRequestPromise = null;
  var bookmarkController = null;

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
      viewableAncestorPrompt: "Showing this doc also requires showing these parent docs:\n\n{titles}\n\nContinue?",
      viewableDescendantPrompt: "Show descendant docs too?\n\nType \"all\" to include descendants, \"selected\" for this doc only, or cancel to stop.",
      viewableInvalidChoice: "Show update cancelled: expected `all` or `selected`.",
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
      copyLinkLabel: "Copy Link",
      copyLinkStatus: "Copied link for {title}.",
      copyLinkFailed: "Copy link failed."
    },
    showHidden: true,
    reloadNonce: "",
    reloadExpectedDocId: "",
    dragDocId: "",
    dropTargetDocId: "",
    dropPosition: "",
    moveUndo: null,
    contextMenuDocId: "",
    metadataEditingDocId: "",
    metadataRestoreFocusId: "",
    nonLoadableDocIds: new Set(),
    manageOnlyTreeRootIds: new Set(),
    showUpdatedDate: true,
    sidebarCollapsed: readSidebarCollapsedState()
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
    state: state,
    viewerScope: function () { return viewerScope; },
    viewerTargetDocId: viewerTargetDocId,
    viewerUrl: viewerUrl
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

  function normalizeBrowserScopeConfig(rawScope) {
    if (!rawScope || typeof rawScope !== "object") return null;
    var scopeId = String(rawScope.scope_id || "").trim().toLowerCase();
    if (!scopeId) return null;
    var rawViewerBaseUrl = String(rawScope.viewer_base_url || "").trim() || "/docs/";
    var viewerBase = rawViewerBaseUrl.charAt(0) === "/" ? rawViewerBaseUrl : "/" + rawViewerBaseUrl;
    if (viewerBase.charAt(viewerBase.length - 1) !== "/") {
      viewerBase += "/";
    }
    return {
      scopeId: scopeId,
      viewerBaseUrl: viewerBase,
      includeScopeParam: rawScope.include_scope_param === true,
      defaultDocId: String(rawScope.default_doc_id || "").trim(),
      indexUrl: String(rawScope.index_url || "").trim(),
      searchIndexUrl: String(rawScope.search_index_url || "").trim()
    };
  }

  function normalizeBrowserConfig(payload) {
    if (!payload || typeof payload !== "object") {
      throw new Error("Docs Viewer config must be a JSON object.");
    }
    if (payload.schema_version !== "docs_viewer_config_v1") {
      throw new Error("Docs Viewer config has an unsupported schema.");
    }
    if (!Array.isArray(payload.scopes)) {
      throw new Error("Docs Viewer config requires a scopes array.");
    }
    var seen = new Set();
    var scopes = payload.scopes.map(normalizeBrowserScopeConfig).filter(Boolean).filter(function (config) {
      if (seen.has(config.scopeId)) return false;
      seen.add(config.scopeId);
      return true;
    });
    if (!scopes.length) {
      throw new Error("Docs Viewer config does not define any scopes.");
    }
    scopes.forEach(function (config) {
      if (!config.defaultDocId || !config.indexUrl) {
        throw new Error("Docs Viewer scope " + config.scopeId + " is missing default_doc_id or index_url.");
      }
    });
    return {
      defaultScopeId: String(payload.default_scope_id || scopes[0].scopeId || "").trim().toLowerCase(),
      scopes: scopes,
      scopesById: new Map(scopes.map(function (config) {
        return [config.scopeId, config];
      })),
      docsViewerSettings: payload.docs_viewer && typeof payload.docs_viewer === "object" && !Array.isArray(payload.docs_viewer)
        ? payload.docs_viewer
        : {}
    };
  }

  function pathMatchesViewerBase(pathname, viewerBaseUrl) {
    return pathname.replace(/\/+$/, "/") === new URL(viewerBaseUrl, window.location.origin).pathname.replace(/\/+$/, "/");
  }

  function scopeFromCurrentPath(config) {
    var pathname = window.location.pathname.replace(/\/+$/, "/") || "/";
    var scopes = config.scopes || config.scopeConfigs || [];
    for (var i = 0; i < scopes.length; i += 1) {
      if (pathMatchesViewerBase(pathname, scopes[i].viewerBaseUrl)) {
        return scopes[i].scopeId;
      }
    }
    return "";
  }

  function routeScopeFromUrl() {
    var requestedScope = String(new URLSearchParams(window.location.search).get("scope") || "").trim().toLowerCase();
    if (allowScopeQuery && requestedScope) {
      if (!state.scopeConfigsById.has(requestedScope)) {
        throw new Error("Unknown docs scope: " + requestedScope);
      }
      return requestedScope;
    }
    if (!allowScopeQuery) {
      var pathScope = scopeFromCurrentPath(state);
      if (pathScope) return pathScope;
      if (viewerScope && state.scopeConfigsById.has(viewerScope)) return viewerScope;
    }
    if (viewerScope && state.scopeConfigsById.has(viewerScope)) return viewerScope;
    return state.defaultScopeId;
  }

  function renderScopeOptions() {
    if (!scopeSelect) return;
    scopeSelect.innerHTML = state.scopeConfigs.map(function (config) {
      return '<option value="' + escapeHtml(config.scopeId) + '">' + escapeHtml(config.scopeId) + '</option>';
    }).join("");
    scopeSelect.value = viewerScope;
  }

  function applyRouteScopeConfig(scope) {
    var config = state.scopeConfigsById.get(scope);
    if (!config) {
      throw new Error("Unknown docs scope: " + scope);
    }
    viewerScope = scope;
    indexUrl = appendAssetVersion(config.indexUrl);
    searchIndexUrl = appendAssetVersion(config.searchIndexUrl);
    defaultRouteDocId = config.defaultDocId;
    viewerBaseUrl = allowScopeQuery ? (routeViewerBaseUrl || window.location.pathname) : config.viewerBaseUrl;
    includeScopeParam = allowScopeQuery ? true : config.includeScopeParam;
    viewerPathname = new URL(viewerBaseUrl, window.location.origin).pathname;
    bookmarkScope = viewerScope || viewerPathname || "docs";
    sidebarStorageKey = SIDEBAR_STORAGE_PREFIX + bookmarkScope;
    state.sidebarCollapsed = readSidebarCollapsedState();
    root.dataset.viewerScope = viewerScope;
    root.dataset.indexUrl = config.indexUrl;
    root.dataset.searchIndexUrl = config.searchIndexUrl;
    root.dataset.defaultDocId = defaultRouteDocId;
    root.dataset.viewerBaseUrl = viewerBaseUrl;
    root.dataset.includeScopeParam = includeScopeParam ? "true" : "false";
    renderScopeOptions();
  }

  function loadDocsViewerConfig() {
    if (state.docsViewerConfigLoaded) return Promise.resolve(state.docsViewerConfig);
    if (state.docsViewerConfigRequestPromise) return state.docsViewerConfigRequestPromise;
    if (!docsViewerConfigUrl) {
      return Promise.reject(new Error("Docs Viewer config URL is not configured."));
    }

    state.docsViewerConfigRequestPromise = fetchJsonWithRetry(
      docsViewerConfigUrl,
      "Failed to load Docs Viewer config",
      "",
      dataRequestOptions()
    )
      .then(function (payload) {
        var config = normalizeBrowserConfig(payload);
        state.docsViewerConfig = config;
        state.scopeConfigs = config.scopes;
        state.scopeConfigsById = config.scopesById;
        state.defaultScopeId = config.defaultScopeId;
        state.docsViewerConfigLoaded = true;
        applyRouteScopeConfig(routeScopeFromUrl());
        return config;
      })
      .finally(function () {
        state.docsViewerConfigRequestPromise = null;
      });

    return state.docsViewerConfigRequestPromise;
  }

  function handleScopeChange() {
    if (!allowScopeQuery || !scopeSelect) return;
    var nextScope = String(scopeSelect.value || "").trim().toLowerCase();
    var config = state.scopeConfigsById.get(nextScope);
    if (!config) {
      scopeSelect.value = viewerScope;
      return;
    }

    var url = new URL(routeViewerBaseUrl || viewerBaseUrl, window.location.origin);
    url.searchParams.set("scope", nextScope);
    if (state.managementMode || getCurrentMode() === MANAGEMENT_MODE) {
      url.searchParams.set("mode", MANAGEMENT_MODE);
    }
    if (config.defaultDocId) {
      url.searchParams.set("doc", config.defaultDocId);
    }
    window.location.assign(url.pathname + url.search);
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

  function readSidebarCollapsedState() {
    try {
      return window.localStorage.getItem(sidebarStorageKey) === "collapsed";
    } catch (error) {
      return false;
    }
  }

  function persistSidebarCollapsedState() {
    try {
      window.localStorage.setItem(sidebarStorageKey, state.sidebarCollapsed ? "collapsed" : "expanded");
    } catch (error) {
      return;
    }
  }

  function renderSidebarCollapsedState() {
    var active = state.sidebarCollapsed && sidebarCollapseAvailable();
    root.dataset.sidebarState = active ? "collapsed" : "expanded";
    if (!sidebarToggle) return;

    sidebarToggle.hidden = !sidebarCollapseAvailable();
    sidebarToggle.setAttribute("aria-expanded", active ? "false" : "true");
    sidebarToggle.setAttribute("aria-label", active ? "Expand docs index" : "Collapse docs index");
    sidebarToggle.title = active ? "Expand docs index" : "Collapse docs index";
    var icon = sidebarToggle.querySelector(".docsViewer__sidebarToggleIcon");
    if (icon) {
      icon.textContent = active ? "›" : "‹";
    }
  }

  function toggleSidebarCollapsed() {
    if (!sidebarCollapseAvailable()) return;
    state.sidebarCollapsed = !state.sidebarCollapsed;
    persistSidebarCollapsedState();
    hideContextMenu();
    renderSidebarCollapsedState();
  }

  function positiveInteger(value, fallback) {
    var parsed = parseInt(value, 10);
    return parsed > 0 ? parsed : fallback;
  }

  function getConfigValue(config, path) {
    var current = config;
    String(path || "").split(".").filter(Boolean).forEach(function (key) {
      if (current && Object.prototype.hasOwnProperty.call(current, key)) {
        current = current[key];
      } else {
        current = undefined;
      }
    });
    return current;
  }

  function getConfigText(config, path, fallback) {
    var value = getConfigValue(config, "ui_text." + path);
    return String(value || fallback || "");
  }

  function normalizeUiStatuses(config, scope) {
    var statusesByScope = getConfigValue(config, "docs_viewer.ui_statuses_by_scope");
    var rawStatuses = statusesByScope && typeof statusesByScope === "object" ? statusesByScope[scope] : null;
    if (!Array.isArray(rawStatuses)) return [];

    var seen = new Set();
    return rawStatuses.reduce(function (statuses, rawStatus) {
      if (!rawStatus || typeof rawStatus !== "object") return statuses;
      var value = typeof rawStatus.ui_status === "string" ? rawStatus.ui_status.trim() : "";
      var label = typeof rawStatus.label === "string" ? rawStatus.label.trim() : "";
      var emoji = typeof rawStatus.emoji === "string" ? rawStatus.emoji.trim() : "";
      if (!value || !label || !emoji || emoji.length > UI_STATUS_EMOJI_MAX_LENGTH || seen.has(value)) {
        return statuses;
      }
      seen.add(value);
      statuses.push({
        ui_status: value,
        label: label,
        emoji: emoji
      });
      return statuses;
    }, []);
  }

  function formatText(template, tokens) {
    var text = String(template || "");
    Object.keys(tokens || {}).forEach(function (key) {
      text = text.replace(new RegExp("\\{" + key + "\\}", "g"), tokens[key]);
    });
    return text;
  }

  function applyViewerConfig(config) {
    state.viewerConfig = config || {};
    state.viewerConfigLoaded = true;
    state.recentLimit = positiveInteger(getConfigValue(config, "docs_viewer.recently_added_limit"), DEFAULT_RECENT_LIMIT);
    state.uiStatuses = normalizeUiStatuses(config, viewerScope);
    state.uiStatusByValue = new Map(state.uiStatuses.map(function (status) {
      return [status.ui_status, status];
    }));
    var hiddenColor = String(getConfigValue(config, "docs_viewer.hidden_nav_color") || getConfigValue(config, "docs_viewer.draft_nav_color") || "").trim();
    if (hiddenColor) {
      root.style.setProperty("--docs-viewer-draft-color", hiddenColor);
    }
    if (recentButton) {
      var label = getConfigText(config, "docs_viewer.recently_added_button", "recently added");
      recentButton.textContent = label;
      recentButton.setAttribute("aria-label", label);
      recentButton.title = label;
    }
    state.managementText.statusPillSetLabel = getConfigText(config, "docs_viewer.status_pill_set_label", state.managementText.statusPillSetLabel);
    state.managementText.statusPillClearLabel = getConfigText(config, "docs_viewer.status_pill_clear_label", state.managementText.statusPillClearLabel);
    state.managementText.statusPillReadonlyLabel = getConfigText(config, "docs_viewer.status_pill_readonly_label", state.managementText.statusPillReadonlyLabel);
    state.managementText.statusMenuLabel = getConfigText(config, "docs_viewer.status_menu_label", state.managementText.statusMenuLabel);
    state.managementText.statusPillSaving = getConfigText(config, "docs_viewer.status_pill_saving", state.managementText.statusPillSaving);
    state.managementText.statusPillSaved = getConfigText(config, "docs_viewer.status_pill_saved", state.managementText.statusPillSaved);
    state.managementText.statusPillFailed = getConfigText(config, "docs_viewer.status_pill_failed", state.managementText.statusPillFailed);
    if (managementController) {
      managementController.applyConfig(config);
    }
    if (state.docs.length) {
      renderSidebar();
      renderStatusPills();
    }
    if (state.recentModeActive) {
      renderRecentMode();
    }
  }

  function loadViewerConfig() {
    if (state.viewerConfigLoaded) return Promise.resolve(null);
    if (state.viewerConfigRequestPromise) return state.viewerConfigRequestPromise;
    if (!docsViewerConfigUrl) {
      applyViewerConfig({});
      return Promise.resolve(null);
    }

    state.viewerConfigRequestPromise = Promise.all([
      loadDocsViewerConfig(),
      loadDocsViewerText()
    ])
      .then(function (results) {
        var browserConfig = results[0] || {};
        var config = {
          docs_viewer: browserConfig.docsViewerSettings || {}
        };
        config = mergeDocsViewerText(config, results[1]);
        applyViewerConfig(config);
        return config;
      })
      .catch(function () {
        applyViewerConfig({});
        return null;
      })
      .finally(function () {
        state.viewerConfigRequestPromise = null;
      });
    return state.viewerConfigRequestPromise;
  }

  function loadDocsViewerText() {
    if (!uiTextUrl) return Promise.resolve(null);
    return fetchJsonWithRetry(appendAssetVersion(uiTextUrl), "Failed to load Docs Viewer UI text", "", dataRequestOptions())
      .catch(function (error) {
        console.warn("docs_viewer: scoped UI text unavailable; using fallback copy", error);
        return null;
      });
  }

  function mergeDocsViewerText(config, text) {
    if (!text || typeof text !== "object" || Array.isArray(text)) return config || {};
    var target = config && typeof config === "object" ? config : {};
    if (!target.ui_text || typeof target.ui_text !== "object" || Array.isArray(target.ui_text)) {
      target.ui_text = {};
    }
    target.ui_text.docs_viewer = text;
    return target;
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
    var url = new URL(viewerBaseUrl, window.location.origin);
    if (includeScopeParam && viewerScope) {
      url.searchParams.set("scope", viewerScope);
    }
    if (state.managementMode) {
      url.searchParams.set("mode", MANAGEMENT_MODE);
    }
    url.searchParams.set("doc", docId);
    if (typeof query === "string" && query.trim()) {
      url.searchParams.set("q", query.trim());
    }
    url.hash = hash || "";
    return url.pathname + url.search + url.hash;
  }

  function viewerUrlForScope(scope, docId, options) {
    var targetScope = String(scope || viewerScope || "").trim().toLowerCase();
    var targetConfig = state.scopeConfigsById.get(targetScope);
    var useManage = Boolean(options && options.manage && allowManagement);
    var url = new URL(useManage ? (routeViewerBaseUrl || viewerBaseUrl || "/docs/") : ((targetConfig && targetConfig.viewerBaseUrl) || viewerBaseUrl), window.location.origin);
    if (useManage) {
      url.searchParams.set("scope", targetScope);
      url.searchParams.set("mode", MANAGEMENT_MODE);
    } else if (targetConfig && targetConfig.includeScopeParam && targetScope) {
      url.searchParams.set("scope", targetScope);
    }
    url.searchParams.set("doc", docId);
    return url.pathname + url.search;
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

  function fetchDocsIndexForScope(scope) {
    var targetScope = String(scope || viewerScope || "").trim().toLowerCase();
    var targetConfig = state.scopeConfigsById.get(targetScope);
    if (!targetConfig || !targetConfig.indexUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return fetchIndexWithRetry(dataRequestOptions({
      indexUrl: appendAssetVersion(targetConfig.indexUrl),
      viewerScope: targetScope,
      reloadNonce: "",
      reloadExpectedDocId: ""
    }));
  }

  function reportContext(doc, payload) {
    return {
      allowManagement: allowManagement,
      checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
      content: content,
      doc: doc,
      fetchDocsIndex: fetchDocsIndexForScope,
      managementBaseUrl: managementBaseUrl,
      managementMode: state.managementMode,
      payload: payload,
      reportRegistryUrl: reportRegistryUrl,
      setStatus: setStatus,
      viewerScope: viewerScope,
      viewerUrlForScope: viewerUrlForScope
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
    if (!state.managementMode) return isDocViewable(doc);
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
    if (!doc || isNonLoadableDoc(doc) || isManageOnlyTreeDoc(doc)) return null;
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
    meta.hidden = true;
    content.hidden = true;
    renderBookmarkToggle();
    renderStatusPills();
  }

  function showDocPane() {
    setRecentModeActive(false);
    content.hidden = false;
    results.hidden = true;
    more.hidden = true;
    more.innerHTML = "";
  }

  function showSearchPane() {
    hideDocPane();
    results.hidden = false;
  }

  function showRecentPane() {
    hideDocPane();
    setRecentModeActive(true);
    results.hidden = false;
  }

  function renderPayload(doc, payload, hash) {
    state.statusMenuOpen = false;
    state.selectedDocId = doc.doc_id;
    renderSidebar();
    renderBookmarkUi();
    renderManagementUi();

    if (hasActiveQuery()) {
      setRecentModeActive(false);
      renderSearchMode();
      return;
    }

    showDocPane();
    renderMeta(doc);
    content.innerHTML = payload.content_html || "";
    maybeMountDocsViewerReport(doc, payload);
    document.title = doc.title + " | dotlineform";
    setStatus("", false);

    window.requestAnimationFrame(function () {
      scrollToHash(hash);
    });
  }

  function setHistory(docId, hash, query, mode) {
    if (mode === "none") return;

    var nextUrl = viewerUrl(docId, hash, query);
    var nextState = { docId: docId, hash: hash || "", q: query || "" };
    if (mode === "replace") {
      window.history.replaceState(nextState, "", nextUrl);
      return;
    }

    window.history.pushState(nextState, "", nextUrl);
  }

  function cancelSearchDebounce() {
    if (state.searchDebounceId == null) return;
    window.clearTimeout(state.searchDebounceId);
    state.searchDebounceId = null;
  }

  function loadDoc(docId, options) {
    setRecentModeActive(false);
    var mode = options && options.historyMode ? options.historyMode : "push";
    var hash = options && options.hash ? options.hash : "";
    var shouldExpandTrail = !options || options.expandTrail !== false;
    var targetDocId = resolveLoadableDocId(docId);
    if (targetDocId && targetDocId !== docId) {
      loadDoc(targetDocId, {
        historyMode: mode === "none" ? "replace" : mode,
        hash: hash,
        expandTrail: shouldExpandTrail
      });
      return;
    }
    var doc = state.docsById.get(docId);
    if (!doc) {
      setStatus("Document not found.", true);
      hideDocPane();
      content.textContent = "";
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      renderManagementUi();
      return;
    }

    state.selectedDocId = docId;
    if (shouldExpandTrail) {
      expandTrail(docId);
    }
    renderBookmarkUi();

    setHistory(docId, hash, "", mode);

    if (state.payloadCache.has(docId)) {
      renderPayload(doc, state.payloadCache.get(docId), hash);
      return;
    }

    renderSidebar();
    showDocPane();
    renderMeta(doc);
    setStatus("Loading " + doc.title + "...", false);
    content.textContent = "";

    var requestId = state.requestId + 1;
    state.requestId = requestId;

    fetchPreferredGeneratedJson(
      doc.content_url,
      "Failed to load " + doc.content_url,
      managementReloadPath("/docs/generated/payload", { scope: viewerScope, doc_id: docId }),
      dataRequestOptions({ useSearchCapability: false })
    )
      .then(function (payload) {
        if (state.requestId !== requestId) return;
        state.payloadCache.set(docId, payload);
        state.reloadNonce = "";
        state.reloadExpectedDocId = "";
        renderPayload(doc, payload, hash);
      })
      .catch(function (error) {
        if (state.requestId !== requestId) return;
        setStatus(error.message || "Failed to load document.", true);
        content.textContent = "";
      });
  }

  function routeFromAnchor(anchor) {
    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return null;
    if (url.pathname !== viewerPathname) return null;
    var scope = String(url.searchParams.get("scope") || "").trim();
    var linkMode = String(url.searchParams.get("mode") || "");
    var currentMode = getCurrentMode();
    if (allowManagement && linkMode && linkMode !== currentMode) return null;
    if (includeScopeParam && scope && scope !== viewerScope) {
      if (!allowScopeQuery || !allowManagement || currentMode !== MANAGEMENT_MODE || linkMode) return null;
      url.searchParams.set("mode", MANAGEMENT_MODE);
      return {
        navigateUrl: url.pathname + url.search + url.hash
      };
    }

    var docId = url.searchParams.get("doc");
    if (!docId) return null;

    return {
      docId: docId,
      hash: url.hash ? url.hash.slice(1) : ""
    };
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
      loadDoc(route.docId, { historyMode: "push", hash: route.hash });
    });

    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", function () {
        toggleSidebarCollapsed();
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
    var requestedDocId = getCurrentDocId();
    var resolvedDocId = requestedDocId;
    if (!state.docsById.has(resolvedDocId) && defaultRouteDocId && state.docsById.has(defaultRouteDocId)) {
      resolvedDocId = defaultRouteDocId;
    }
    if (state.docsById.has(resolvedDocId)) {
      resolvedDocId = resolveLoadableDocId(resolvedDocId) || "";
    }
    if (!resolvedDocId && defaultRouteDocId && state.docsById.has(defaultRouteDocId)) {
      resolvedDocId = resolveLoadableDocId(defaultRouteDocId);
    }
    if (!resolvedDocId) {
      resolvedDocId = defaultDocId();
    }
    return {
      requestedDocId: requestedDocId,
      docId: resolvedDocId,
      corrected: resolvedDocId !== requestedDocId
    };
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
    setRecentModeActive(false);
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    syncHiddenVisibilityForRequestedDoc();
    applyDocVisibility();
    var route = resolveDocId();
    var docId = route.docId;
    if (!docId) {
      setStatus("No docs available.", true);
      return;
    }

    var query = getCurrentQuery();
    state.searchQuery = query;
    state.searchRouteActive = hasActiveQuery(query);
    state.selectedDocId = docId;
    if (searchInput) {
      searchInput.value = query;
    }

    expandTrail(docId);
    renderSidebar();
    renderBookmarkUi();
    renderManagementUi();

    if (route.corrected || !hasCanonicalScopeInUrl() || hasDisallowedModeInUrl() || hasDisallowedScopeInUrl()) {
      setHistory(docId, "", query, "replace");
    }

    if (state.searchRouteActive) {
      renderSearchMode();
      return;
    }

    loadDoc(docId, {
      historyMode: options && options.historyMode ? options.historyMode : "push",
      hash: options && options.hash ? options.hash : getCurrentHash(),
      expandTrail: Boolean(state.docsById.get(docId).parent_id)
    });
  }

  function loadIndex() {
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
    if (state.docs.length === 0) return;
    if (allowScopeQuery) {
      try {
        if (routeScopeFromUrl() !== viewerScope) {
          window.location.reload();
          return;
        }
      } catch (error) {
        setStatus(error.message || "Unknown docs scope.", true);
        return;
      }
    }
    hideContextMenu();
    cancelSearchDebounce();
    applyCurrentRoute({ historyMode: "none", hash: getCurrentHash() });
  });

  window.addEventListener("scroll", hideContextMenu, { passive: true });
  window.addEventListener("resize", function () {
    hideContextMenu();
    renderSidebarCollapsedState();
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
  loadDocsViewerConfig()
    .then(function () {
      renderSidebarCollapsedState();
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
    });

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(String(value || ""));
    }
    return String(value || "").replace(/["\\]/g, "\\$&");
  }
})();
