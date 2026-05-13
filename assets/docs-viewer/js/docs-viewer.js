import {
  buildChildrenMap,
  compareDocs,
  isDocHidden,
  isDocViewable,
  normalizeDocIdSet
} from "./docs-viewer-tree.js";
import {
  collectRecentDocs,
  collectSearchMatches,
  normalizeSearchEntries,
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  bookmarkKey,
  compareBookmarks,
  deleteBookmarkRecord,
  isoNow,
  loadBookmarks,
  normalizeBookmarkRecord,
  persistBookmark
} from "./docs-viewer-favourites.js";
import {
  appendAssetVersion,
  fetchIndexWithRetry,
  fetchJsonWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath,
  readAssetVersion
} from "./docs-viewer-data.js";

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
      docHiddenEmoji: "🚫",
      statusPillSetLabel: "Set status: {label}",
      statusPillClearLabel: "Clear status: {label}",
      statusPillReadonlyLabel: "Status: {label}",
      statusPillSaving: "Saving status for {title}...",
      statusPillSaved: "Status saved.",
      statusPillFailed: "Status update failed."
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
      currentStatusValue: currentStatusValue,
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
      renderStatusPills: renderStatusPills,
      root: root,
      searchInput: searchInput,
      setHistory: setHistory,
      setStatus: setStatus,
      state: state,
      statusPillsCanWrite: statusPillsCanWrite,
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

  function searchIsEnabled() {
    return Boolean(searchInput && results && more && searchIndexUrl);
  }

  function searchControlsAvailable() {
    return Boolean(searchInput && results && more);
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

  function getScopeBookmarks() {
    return state.bookmarks
      .filter(function (record) { return record.scope === bookmarkScope; })
      .sort(compareBookmarks);
  }

  function getBookmarkForDoc(docId) {
    return findBookmarkByKey(bookmarkKey(bookmarkScope, docId));
  }

  function findBookmarkByKey(key) {
    for (var i = 0; i < state.bookmarks.length; i += 1) {
      if (state.bookmarks[i].key === key) return state.bookmarks[i];
    }
    return null;
  }

  function nextBookmarkOrder() {
    var bookmarks = getScopeBookmarks();
    if (!bookmarks.length) return 1;
    return bookmarks[bookmarks.length - 1].order + 1;
  }

  function defaultBookmarkLabel(doc) {
    if (!doc) return "";
    return String(doc.title || doc.doc_id || "").trim();
  }

  function upsertBookmarkState(record) {
    var normalized = normalizeBookmarkRecord(record);
    if (!normalized) return;
    var next = [];
    var found = false;
    state.bookmarks.forEach(function (entry) {
      if (entry.key === normalized.key) {
        next.push(normalized);
        found = true;
      } else {
        next.push(entry);
      }
    });
    if (!found) {
      next.push(normalized);
    }
    state.bookmarks = next.sort(compareBookmarks);
  }

  function removeBookmarkState(key) {
    state.bookmarks = state.bookmarks.filter(function (entry) {
      return entry.key !== key;
    });
    if (state.editingBookmarkKey === key) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
    }
  }

  function renderBookmarkUi() {
    renderBookmarkToggle();
    renderBookmarkRow();
    renderStatusPills();
  }

  function renderBookmarkToggle() {
    if (!bookmarkToggle) return;
    var doc = state.docsById.get(state.selectedDocId);
    var canShow = Boolean(doc) && state.bookmarksLoaded && state.bookmarkSupport && !state.searchRouteActive;
    bookmarkToggle.hidden = !canShow;
    if (!canShow) return;

    var record = getBookmarkForDoc(doc.doc_id);
    var active = Boolean(record);
    bookmarkToggle.classList.toggle("is-active", active);
    bookmarkToggle.textContent = active ? "★" : "☆";
    bookmarkToggle.setAttribute("aria-pressed", active ? "true" : "false");
    bookmarkToggle.setAttribute("aria-label", active ? "Remove bookmark" : "Add bookmark");
    bookmarkToggle.title = active ? "Remove bookmark" : "Add bookmark";
  }

  function currentStatusValue(doc) {
    return String(doc && doc.ui_status || "").trim();
  }

  function statusPillsCanWrite(doc) {
    return Boolean(
      doc &&
      allowManagement &&
      state.managementMode &&
      state.managementAvailable &&
      !state.managementBusy &&
      !state.searchRouteActive
    );
  }

  function statusPillsCanRender(doc) {
    return Boolean(
      doc &&
      allowManagement &&
      state.managementMode &&
      state.managementAvailable &&
      state.uiStatuses.length > 0 &&
      !state.searchRouteActive
    );
  }

  function renderStatusPills() {
    if (!statusPills) return;
    var doc = state.docsById.get(state.selectedDocId);
    var canShow = statusPillsCanRender(doc);
    statusPills.hidden = !canShow;
    if (!canShow) {
      statusPills.innerHTML = "";
      return;
    }

    var activeStatus = currentStatusValue(doc);
    var canWrite = statusPillsCanWrite(doc);
    statusPills.innerHTML = state.uiStatuses.map(function (statusConfig) {
      var selected = statusConfig.ui_status === activeStatus;
      var labelTemplate = canWrite
        ? (selected ? state.managementText.statusPillClearLabel : state.managementText.statusPillSetLabel)
        : state.managementText.statusPillReadonlyLabel;
      var label = formatText(labelTemplate, { label: statusConfig.label, title: doc.title });
      var className = "docsViewer__statusPill" + (selected ? " is-active" : "");
      return (
        '<button type="button" class="' + className + '" data-ui-status="' + escapeHtml(statusConfig.ui_status) + '" aria-pressed="' + (selected ? "true" : "false") + '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(label) + '"' + (canWrite ? "" : " disabled") + '>' +
          '<span class="docsViewer__statusPillEmoji" aria-hidden="true">' + escapeHtml(statusConfig.emoji) + '</span>' +
          '<span class="visually-hidden">' + escapeHtml(statusConfig.label) + '</span>' +
        '</button>'
      );
    }).join("");
  }

  function renderBookmarkRow() {
    if (!bookmarkRow) return;
    if (!state.bookmarksLoaded || !state.bookmarkSupport) {
      bookmarkRow.hidden = true;
      bookmarkRow.innerHTML = "";
      return;
    }

    var bookmarks = getScopeBookmarks();
    if (!bookmarks.length) {
      bookmarkRow.hidden = true;
      bookmarkRow.innerHTML = "";
      return;
    }

    bookmarkRow.hidden = false;
    bookmarkRow.innerHTML = bookmarks.map(function (record) {
      var isActive = record.doc_id === state.selectedDocId;
      var isEditing = record.key === state.editingBookmarkKey;
      var pillClass = "docsViewer__bookmarkPill" + (isActive ? " is-active" : "");
      if (isEditing) {
        return (
          '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
            '<input class="docsViewer__bookmarkInput" type="text" value="' + escapeHtml(record.label || record.default_title || record.doc_id) + '" data-bookmark-input="' + escapeHtml(record.key) + '" aria-label="Rename bookmark">' +
            '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
          '</div>'
        );
      }
      return (
        '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
          '<button type="button" class="docsViewer__bookmarkOpen" data-bookmark-open="' + escapeHtml(record.doc_id) + '" title="Open bookmark. Right-click to rename." aria-current="' + (isActive ? "page" : "false") + '">' +
            '<span class="docsViewer__bookmarkLabel">' + escapeHtml(record.label || record.default_title || record.doc_id) + '</span>' +
          '</button>' +
          '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
        '</div>'
      );
    }).join("");

    if (state.pendingBookmarkFocusKey) {
      var focusTarget = bookmarkRow.querySelector('[data-bookmark-input="' + cssEscape(state.pendingBookmarkFocusKey) + '"]');
      if (focusTarget) {
        window.requestAnimationFrame(function () {
          focusTarget.focus();
          focusTarget.select();
        });
      }
      state.pendingBookmarkFocusKey = "";
    }
  }

  function bookmarkStorageOptions() {
    return {
      indexedDB: window.indexedDB,
      dbName: BOOKMARK_DB_NAME,
      dbVersion: BOOKMARK_DB_VERSION,
      storeName: BOOKMARK_STORE_NAME
    };
  }

  function handleBookmarkStorageError(error) {
    if (error && error.bookmarkStorageUnavailable) {
      state.bookmarkSupport = false;
      renderBookmarkUi();
    }
    return error;
  }

  function initializeBookmarks() {
    if (!state.bookmarkSupport) {
      state.bookmarksLoaded = true;
      renderBookmarkUi();
      return;
    }

    loadBookmarks(bookmarkStorageOptions())
      .then(function (records) {
        state.bookmarks = records;
        state.bookmarksLoaded = true;
        renderBookmarkUi();
      })
      .catch(function (error) {
        handleBookmarkStorageError(error);
        state.bookmarks = [];
        state.bookmarksLoaded = true;
        renderBookmarkUi();
      });
  }

  function addBookmarkForDoc(doc) {
    if (!doc || !state.bookmarkSupport) return;
    var now = isoNow();
    var record = normalizeBookmarkRecord({
      scope: bookmarkScope,
      doc_id: doc.doc_id,
      label: defaultBookmarkLabel(doc),
      default_title: defaultBookmarkLabel(doc),
      created_at_utc: now,
      updated_at_utc: now,
      order: nextBookmarkOrder()
    });
    upsertBookmarkState(record);
    renderBookmarkUi();
    persistBookmark(record, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      removeBookmarkState(record.key);
      renderBookmarkUi();
      setStatus(error.message || "Failed to save bookmark.", true);
    });
  }

  function removeBookmarkByKey(key) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) return;
    removeBookmarkState(key);
    renderBookmarkUi();
    deleteBookmarkRecord(key, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      upsertBookmarkState(record);
      renderBookmarkUi();
      setStatus(error.message || "Failed to remove bookmark.", true);
    });
  }

  function toggleCurrentBookmark() {
    var doc = state.docsById.get(state.selectedDocId);
    if (!doc || !state.bookmarksLoaded || !state.bookmarkSupport) return;
    var existing = getBookmarkForDoc(doc.doc_id);
    if (existing) {
      removeBookmarkByKey(existing.key);
      return;
    }
    addBookmarkForDoc(doc);
  }

  function startBookmarkRename(key) {
    if (!key) return;
    state.editingBookmarkKey = key;
    state.pendingBookmarkFocusKey = key;
    renderBookmarkRow();
  }

  function finishBookmarkRename(key, nextValue, cancel) {
    var record = key ? findBookmarkByKey(key) : null;
    if (!record) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderBookmarkRow();
      return;
    }

    if (cancel) {
      state.editingBookmarkKey = "";
      state.pendingBookmarkFocusKey = "";
      renderBookmarkRow();
      return;
    }

    var nextLabel = String(nextValue || "").trim() || record.default_title || record.doc_id;
    state.editingBookmarkKey = "";
    state.pendingBookmarkFocusKey = "";
    if (nextLabel === record.label) {
      renderBookmarkRow();
      return;
    }

    var updated = normalizeBookmarkRecord({
      key: record.key,
      scope: record.scope,
      doc_id: record.doc_id,
      label: nextLabel,
      default_title: record.default_title,
      created_at_utc: record.created_at_utc,
      updated_at_utc: isoNow(),
      order: record.order
    });

    upsertBookmarkState(updated);
    renderBookmarkUi();
    persistBookmark(updated, bookmarkStorageOptions()).catch(function (error) {
      handleBookmarkStorageError(error);
      upsertBookmarkState(record);
      renderBookmarkUi();
      setStatus(error.message || "Failed to rename bookmark.", true);
    });
  }

  function commitBookmarkInput(input, cancel) {
    if (!input || input.dataset.bookmarkCommitted === "true") return;
    input.dataset.bookmarkCommitted = "true";
    finishBookmarkRename(input.dataset.bookmarkInput, input.value, cancel);
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

  function docChildren(docId) {
    return state.childrenByParent.get(docId) || [];
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
    var trail = [];
    var current = state.docsById.get(docId);
    while (current) {
      trail.unshift(current);
      current = current.parent_id ? state.docsById.get(current.parent_id) : null;
    }
    return trail;
  }

  function displayRecentMetaForDoc(doc) {
    if (!doc) return "";
    var parts = [];
    var addedDate = String(doc.added_date || doc.last_updated || "").trim();
    if (addedDate) parts.push(addedDate);
    if (doc.parent_id) {
      var parent = state.docsById.get(doc.parent_id);
      var parentTitle = parent ? String(parent.title || "").trim() : "";
      if (parentTitle) parts.push(parentTitle);
    }
    return parts.join(" • ");
  }

  function expandTrail(docId) {
    buildTrail(docId).forEach(function (doc) {
      if ((state.childrenByParent.get(doc.doc_id) || []).length > 0) {
        state.expandedDocIds.add(doc.doc_id);
      }
    });
  }

  function renderSidebar() {
    nav.textContent = "";
    if (state.docs.length === 0) {
      return;
    }

    nav.appendChild(renderNavList(""));
    updateNavDragState();
  }

  function renderNavList(parentId) {
    var list = document.createElement("ul");
    list.className = parentId ? "docsViewer__navList docsViewer__navList--child" : "docsViewer__navList";

    var docs = state.childrenByParent.get(parentId) || [];
    docs.forEach(function (doc) {
      var item = document.createElement("li");
      item.className = "docsViewer__navItem";
      var row = document.createElement("div");
      row.className = "docsViewer__navRow";
      if (isDocHidden(doc)) {
        row.className += " is-draft";
      }
      row.dataset.docRowId = doc.doc_id;
      var children = docChildren(doc.doc_id);
      var hasChildren = children.length > 0;

      if (hasChildren) {
        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "docsViewer__toggle";
        toggle.dataset.toggleDocId = doc.doc_id;
        toggle.setAttribute("aria-expanded", state.expandedDocIds.has(doc.doc_id) ? "true" : "false");
        toggle.setAttribute("aria-label", state.expandedDocIds.has(doc.doc_id) ? "Collapse section" : "Expand section");
        toggle.textContent = state.expandedDocIds.has(doc.doc_id) ? "▼" : "►";
        row.appendChild(toggle);
      } else {
        var spacer = document.createElement("span");
        spacer.className = "docsViewer__toggleSpacer";
        spacer.setAttribute("aria-hidden", "true");
        spacer.textContent = "";
        row.appendChild(spacer);
      }

      var link = document.createElement("a");
      link.className = "docsViewer__navLink";
      if (doc.doc_id === state.selectedDocId) {
        link.className += " is-active";
        link.setAttribute("aria-current", "page");
      }
      if (isDocHidden(doc)) {
        link.setAttribute("data-draft-doc", "true");
        link.title = state.managementText.metadataHiddenLabel;
      }
      link.href = viewerUrl(viewerTargetDocId(doc.doc_id));
      link.dataset.docId = doc.doc_id;
      if (canDragCurrentDoc(doc)) {
        link.draggable = true;
        link.dataset.dragDocId = doc.doc_id;
      }
      link.textContent = "";
      var uiStatus = statusForIndexDoc(doc);
      if (uiStatus) {
        var statusIcon = document.createElement("span");
        statusIcon.className = "docsViewer__navStatus";
        statusIcon.setAttribute("aria-hidden", "true");
        statusIcon.textContent = uiStatus.emoji;
        link.appendChild(statusIcon);
      }
      if (isDocHidden(doc)) {
        var draftIcon = document.createElement("span");
        draftIcon.className = "docsViewer__draftPrefix";
        draftIcon.setAttribute("aria-hidden", "true");
        draftIcon.textContent = state.managementText.docHiddenEmoji;
        link.appendChild(draftIcon);
      }
      link.appendChild(document.createTextNode(doc.title));
      row.appendChild(link);
      item.appendChild(row);

      if (hasChildren && state.expandedDocIds.has(doc.doc_id)) {
        item.appendChild(renderNavList(doc.doc_id));
      }

      list.appendChild(item);
    });

    return list;
  }

  function renderMeta(doc) {
    var trail = buildTrail(doc.doc_id).slice(0, -1);
    pathEl.textContent = "";
    pathEl.hidden = trail.length === 0;

    trail.forEach(function (entry, index) {
      if (index > 0) {
        var separator = document.createElement("span");
        separator.className = "docsViewer__pathSep";
        separator.textContent = "/";
        pathEl.appendChild(separator);
      }

      var link = document.createElement("a");
      link.href = viewerUrl(viewerTargetDocId(entry.doc_id));
      link.dataset.docId = entry.doc_id;
      link.textContent = entry.title;
      pathEl.appendChild(link);
    });

    var hiddenLabel = state.managementText.metadataHiddenLabel;
    if (!state.showUpdatedDate) {
      updatedEl.textContent = isDocHidden(doc) ? hiddenLabel : "";
      updatedEl.hidden = isDocViewable(doc);
    } else if (doc.last_updated) {
      updatedEl.textContent = (isDocHidden(doc) ? hiddenLabel + " • " : "") + "Updated " + doc.last_updated;
      updatedEl.hidden = false;
    } else {
      updatedEl.textContent = isDocHidden(doc) ? hiddenLabel : "";
      updatedEl.hidden = isDocViewable(doc);
    }
    if (summaryEl) {
      var summary = String(doc.summary || "").trim();
      summaryEl.textContent = summary;
      summaryEl.hidden = !summary;
    }
    meta.hidden = false;
    renderBookmarkToggle();
    renderStatusPills();
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
    if (includeScopeParam && scope && scope !== viewerScope) return null;
    if (allowManagement && String(url.searchParams.get("mode") || "") !== getCurrentMode()) return null;

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
      cancelSearchDebounce();
      state.searchQuery = "";
      state.searchVisibleCount = SEARCH_BATCH_SIZE;
      if (searchInput) {
        searchInput.value = "";
      }
      loadDoc(route.docId, { historyMode: "push", hash: route.hash });
    });

    if (bookmarkToggle) {
      bookmarkToggle.addEventListener("click", function () {
        hideContextMenu();
        toggleCurrentBookmark();
      });
    }

    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", function () {
        toggleSidebarCollapsed();
      });
    }

    if (recentButton) {
      recentButton.addEventListener("click", function () {
        hideContextMenu();
        cancelSearchDebounce();
        var activeDocId = state.selectedDocId || resolveDocId().docId || defaultDocId();
        state.searchQuery = "";
        state.searchRouteActive = false;
        state.searchVisibleCount = SEARCH_BATCH_SIZE;
        if (searchInput) {
          searchInput.value = "";
        }
        if (activeDocId) {
          setHistory(activeDocId, "", "", "push");
        }
        renderRecentMode();
      });
    }

    if (scopeSelect) {
      scopeSelect.addEventListener("change", function () {
        handleScopeChange();
      });
    }

    if (bookmarkRow) {
      bookmarkRow.addEventListener("click", function (event) {
        var removeButton = event.target.closest("[data-bookmark-remove]");
        if (removeButton) {
          event.preventDefault();
          removeBookmarkByKey(removeButton.dataset.bookmarkRemove);
          return;
        }

        var openButton = event.target.closest("[data-bookmark-open]");
        if (openButton) {
          event.preventDefault();
          var targetDocId = openButton.dataset.bookmarkOpen;
          if (!targetDocId) return;
          cancelSearchDebounce();
          state.searchQuery = "";
          state.searchVisibleCount = SEARCH_BATCH_SIZE;
          if (searchInput) {
            searchInput.value = "";
          }
          loadDoc(targetDocId, { historyMode: "push", hash: "" });
        }
      });

      bookmarkRow.addEventListener("contextmenu", function (event) {
        var openButton = event.target.closest("[data-bookmark-open]");
        if (!openButton) return;
        event.preventDefault();
        startBookmarkRename(bookmarkKey(bookmarkScope, openButton.dataset.bookmarkOpen));
      });

      bookmarkRow.addEventListener("keydown", function (event) {
        var openButton = event.target.closest("[data-bookmark-open]");
        if (openButton && event.key === "F2") {
          event.preventDefault();
          startBookmarkRename(bookmarkKey(bookmarkScope, openButton.dataset.bookmarkOpen));
          return;
        }

        var input = event.target.closest("[data-bookmark-input]");
        if (!input) return;
        if (event.key === "Enter") {
          event.preventDefault();
          commitBookmarkInput(input, false);
        } else if (event.key === "Escape") {
          event.preventDefault();
          commitBookmarkInput(input, true);
        }
      });

      bookmarkRow.addEventListener("focusout", function (event) {
        var input = event.target.closest("[data-bookmark-input]");
        if (!input) return;
        commitBookmarkInput(input, false);
      });
    }

    if (statusPills) {
      statusPills.addEventListener("click", function (event) {
        var button = event.target.closest("[data-ui-status]");
        if (!button) return;
        event.preventDefault();
        if (managementController) {
          managementController.handleStatusPillClick(button.dataset.uiStatus);
        }
      });
    }

    document.addEventListener("keydown", function (event) {
      if (managementController && managementController.handleDocumentKeydown(event)) {
        return;
      }
    });

    if (searchControlsAvailable()) {
      more.addEventListener("click", function (event) {
        var button = event.target.closest("button[data-role='more']");
        if (!button) return;
        state.searchVisibleCount += SEARCH_BATCH_SIZE;
        renderSearchMode();
      });

      searchInput.addEventListener("input", function () {
        var nextQuery = String(searchInput.value || "").trim();
        var nextModeActive = Boolean(normalizeSearchText(nextQuery));
        var previousModeActive = state.searchRouteActive;
        var activeDocId = state.selectedDocId || resolveDocId().docId || "";

        cancelSearchDebounce();
        setRecentModeActive(false);
        state.searchQuery = nextQuery;
        state.searchVisibleCount = SEARCH_BATCH_SIZE;

        if (!activeDocId) {
          return;
        }

        if (!nextModeActive) {
          state.searchRouteActive = false;
          setHistory(activeDocId, "", "", previousModeActive ? "replace" : "none");
          applyCurrentRoute({ historyMode: "none", hash: "" });
          return;
        }

        state.searchRouteActive = true;
        setHistory(activeDocId, "", nextQuery, previousModeActive ? "replace" : "push");
        renderSearchPendingState();
        state.searchDebounceId = window.setTimeout(function () {
          state.searchDebounceId = null;
          applyCurrentRoute({ historyMode: "none", hash: "" });
        }, SEARCH_DEBOUNCE_MS);
      });
    }
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

  function loadSearchEntries() {
    if (!searchIsEnabled()) {
      return Promise.reject(new Error("Search unavailable."));
    }
    if (state.searchLoaded) {
      return Promise.resolve(state.searchEntries);
    }
    if (state.searchRequestPromise) {
      return state.searchRequestPromise;
    }

    state.searchRequestPromise = fetchPreferredGeneratedJson(
      searchIndexUrl,
      "Failed to load search data",
      managementReloadPath("/docs/generated/search", { scope: viewerScope }),
      dataRequestOptions({ useSearchCapability: true })
    )
      .then(function (payload) {
        state.searchEntries = normalizeSearchEntries(payload && Array.isArray(payload.entries) ? payload.entries : []);
        state.searchLoaded = true;
        return state.searchEntries;
      })
      .catch(function (error) {
        state.searchLoaded = false;
        throw error;
      })
      .finally(function () {
        state.searchRequestPromise = null;
      });

    return state.searchRequestPromise;
  }

  function renderResultEntry(docId, title, metaText) {
    return (
      '<li class="docsViewer__resultItem">' +
        '<a class="docsViewer__resultTitle" href="' + escapeHtml(viewerUrl(viewerTargetDocId(docId), "", "")) + '">' + escapeHtml(title) + '</a>' +
        (metaText ? '<p class="docsViewer__resultMeta">' + escapeHtml(metaText) + '</p>' : '') +
      '</li>'
    );
  }

  function renderSearchEntry(entry) {
    var metaText = entry.displayMeta || [entry.lastUpdated, entry.parentTitle].filter(Boolean).join(" • ");
    return renderResultEntry(entry.id, entry.title, metaText);
  }

  function renderRecentEntry(doc) {
    return renderResultEntry(doc.doc_id, doc.title, displayRecentMetaForDoc(doc));
  }

  function renderRecentMode() {
    if (!searchIsEnabled()) return;
    showRecentPane();
    document.title = "Recently Added | dotlineform";
    var recentDocs = collectRecentDocs(state.docs.filter(isDocViewable), state.recentLimit);
    if (!recentDocs.length) {
      setStatus("No recently added docs.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    setStatus(recentDocs.length === 1 ? "1 recently added doc" : recentDocs.length + " recently added docs", false);
    results.innerHTML = recentDocs.map(renderRecentEntry).join("");
    more.innerHTML = "";
    more.hidden = true;
  }

  function renderSearchPendingState() {
    if (!searchIsEnabled() || !hasActiveQuery()) return;
    setRecentModeActive(false);
    showSearchPane();
    setStatus(state.searchLoaded ? "Searching..." : "Loading search index...", false);
    results.innerHTML = "";
    more.innerHTML = "";
    more.hidden = true;
    document.title = "Search | dotlineform";
  }

  function renderSearchMode() {
    if (!searchIsEnabled()) {
      setStatus("Search unavailable.", true);
      hideDocPane();
      results.hidden = true;
      more.hidden = true;
      return;
    }

    var query = normalizeSearchText(state.searchQuery);
    if (!query) {
      return;
    }

    showSearchPane();
    setRecentModeActive(false);
    document.title = "Search | dotlineform";

    if (!state.searchLoaded) {
      renderSearchPendingState();
      loadSearchEntries()
        .then(function () {
          if (hasActiveQuery()) {
            renderSearchMode();
          }
        })
        .catch(function (error) {
          if (!hasActiveQuery()) return;
          setStatus(error.message || "Failed to load search data.", true);
          results.innerHTML = "";
          more.innerHTML = "";
          more.hidden = true;
        });
      return;
    }

    var matches = collectSearchMatches(state.searchEntries, query);
    if (!matches.length) {
      setStatus("No results.", false);
      results.innerHTML = "";
      more.innerHTML = "";
      more.hidden = true;
      return;
    }

    var visible = matches.slice(0, state.searchVisibleCount);
    setStatus(matches.length === 1
      ? "1 result"
      : matches.length > visible.length
        ? "Showing " + visible.length + " of " + matches.length + " results"
        : matches.length + " results",
    false);
    results.innerHTML = visible.map(function (match) {
      return renderSearchEntry(match.entry);
    }).join("");
    if (matches.length > visible.length) {
      more.hidden = false;
      more.innerHTML = '<button type="button" class="docsViewer__moreBtn" data-role="more">more</button>';
    } else {
      more.hidden = true;
      more.innerHTML = "";
    }
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

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(String(value || ""));
    }
    return String(value || "").replace(/["\\]/g, "\\$&");
  }
})();
