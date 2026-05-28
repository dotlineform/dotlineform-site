import {
  appendAssetVersion,
  fetchJsonWithRetry
} from "./docs-viewer-data.js";
import {
  routeConfigScopeProjection
} from "./docs-viewer-route-config.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";

export function positiveInteger(value, fallback) {
  var parsed = parseInt(value, 10);
  return parsed > 0 ? parsed : fallback;
}

export function getConfigValue(config, path) {
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

export function getConfigText(config, path, fallback) {
  var value = getConfigValue(config, "ui_text." + path);
  return String(value == null ? fallback == null ? "" : fallback : value);
}

export function formatText(template, tokens) {
  var text = String(template || "");
  Object.keys(tokens || {}).forEach(function (key) {
    text = text.replace(new RegExp("\\{" + key + "\\}", "g"), tokens[key]);
  });
  return text;
}

export function initDocsViewerConfigController(context) {
  var scopeConfig = context.scopeConfig || {};
  var documentIndex = context.documentIndex || {};
  var searchRecent = context.searchRecent || {};
  var routeSession = context.routeSession || {};
  var configService = context.configService || {};
  var routeCommands = context.routeCommands || {};
  var root = context.root;
  var scopeSelect = context.scopeSelect;
  var recentButton = context.recentButton;
  if (!Array.isArray(scopeConfig.scopeConfigs)) scopeConfig.scopeConfigs = [];
  if (!scopeConfig.scopeConfigsById) scopeConfig.scopeConfigsById = new Map();
  if (!scopeConfig.managementText) scopeConfig.managementText = {};
  if (!Array.isArray(documentIndex.docs)) documentIndex.docs = [];

  function docsViewerConfigUrl() {
    return configService.docsViewerConfigUrl || context.docsViewerConfigUrl;
  }

  function uiTextUrl() {
    return configService.uiTextUrl || context.uiTextUrl;
  }

  function dataRequestOptions(options) {
    if (typeof configService.dataRequestOptions === "function") return configService.dataRequestOptions(options);
    return typeof context.dataRequestOptions === "function" ? context.dataRequestOptions(options) : {};
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
      scopeType: String(rawScope.scope_type || "").trim().toLowerCase(),
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
    }).sort(function (left, right) {
      return left.scopeId.localeCompare(right.scopeId);
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
    var viewerScope = context.viewerScope();
    if (context.allowScopeQuery && requestedScope) {
      if (!scopeConfig.scopeConfigsById.has(requestedScope)) {
        throw new Error("Unknown docs scope: " + requestedScope);
      }
      return requestedScope;
    }
    if (!context.allowScopeQuery) {
      var pathScope = scopeFromCurrentPath(scopeConfig);
      if (pathScope) return pathScope;
      if (viewerScope && scopeConfig.scopeConfigsById.has(viewerScope)) return viewerScope;
    }
    if (viewerScope && scopeConfig.scopeConfigsById.has(viewerScope)) return viewerScope;
    return scopeConfig.defaultScopeId;
  }

  function scopeOptionLabel(config) {
    var badges = getConfigValue(scopeConfig.docsViewerConfig, "docsViewerSettings.scope_type_badges");
    var badge = badges && typeof badges === "object" ? badges[config.scopeType] : null;
    var emoji = badge && typeof badge === "object" ? String(badge.emoji || "").trim() : "";
    return (emoji ? emoji + " " : "") + config.scopeId;
  }

  function renderScopeOptions() {
    if (!scopeSelect) return;
    scopeSelect.innerHTML = scopeConfig.scopeConfigs.map(function (config) {
      return '<option value="' + escapeHtml(config.scopeId) + '">' + escapeHtml(scopeOptionLabel(config)) + '</option>';
    }).join("");
    scopeSelect.value = context.viewerScope();
  }

  function applyRouteScopeConfig(scope) {
    var config = scopeConfig.scopeConfigsById.get(scope);
    if (!config) {
      throw new Error("Unknown docs scope: " + scope);
    }
    var routeProjection = routeConfigScopeProjection(config, {
      allowScopeQuery: context.allowScopeQuery,
      routeViewerBaseUrl: context.routeViewerBaseUrl,
      window: window
    });
    if (typeof routeCommands.applyRouteGlobals === "function") {
      routeCommands.applyRouteGlobals(routeProjection);
    } else if (typeof context.applyRouteGlobals === "function") {
      context.applyRouteGlobals(routeProjection);
    }
    root.dataset.viewerScope = scope;
    root.dataset.indexUrl = config.indexUrl;
    root.dataset.searchIndexUrl = config.searchIndexUrl;
    root.dataset.defaultDocId = config.defaultDocId;
    root.dataset.viewerBaseUrl = routeProjection.viewerBaseUrl;
    root.dataset.includeScopeParam = routeProjection.includeScopeParam ? "true" : "false";
    renderScopeOptions();
  }

  function loadDocsViewerConfig(options) {
    var settings = options || {};
    if (settings.force) {
      scopeConfig.docsViewerConfigLoaded = false;
      scopeConfig.docsViewerConfigRequestPromise = null;
    }
    if (scopeConfig.docsViewerConfigLoaded) return Promise.resolve(scopeConfig.docsViewerConfig);
    if (scopeConfig.docsViewerConfigRequestPromise) return scopeConfig.docsViewerConfigRequestPromise;
    if (!docsViewerConfigUrl()) {
      return Promise.reject(new Error("Docs Viewer config URL is not configured."));
    }

    scopeConfig.docsViewerConfigRequestPromise = fetchJsonWithRetry(
      docsViewerConfigUrl(),
      "Failed to load Docs Viewer config",
      "",
      dataRequestOptions(settings.reloadNonce ? { reloadNonce: settings.reloadNonce } : {})
    )
      .then(function (payload) {
        var config = normalizeBrowserConfig(payload);
        scopeConfig.docsViewerConfig = config;
        scopeConfig.scopeConfigs = config.scopes;
        scopeConfig.scopeConfigsById = config.scopesById;
        scopeConfig.defaultScopeId = config.defaultScopeId;
        scopeConfig.docsViewerConfigLoaded = true;
        applyRouteScopeConfig(routeScopeFromUrl());
        return config;
      })
      .finally(function () {
        scopeConfig.docsViewerConfigRequestPromise = null;
      });

    return scopeConfig.docsViewerConfigRequestPromise;
  }

  function handleScopeChange() {
    if (!context.allowScopeQuery || !scopeSelect) return;
    var nextScope = String(scopeSelect.value || "").trim().toLowerCase();
    var config = scopeConfig.scopeConfigsById.get(nextScope);
    if (!config) {
      scopeSelect.value = context.viewerScope();
      return;
    }

    var url = new URL(context.routeViewerBaseUrl || context.viewerBaseUrl(), window.location.origin);
    url.searchParams.set("scope", nextScope);
    if (routeSession.managementMode || context.getCurrentMode() === context.managementMode) {
      url.searchParams.set("mode", context.managementMode);
    }
    if (config.defaultDocId) {
      url.searchParams.set("doc", config.defaultDocId);
    }
    window.location.assign(url.pathname + url.search);
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
      if (!value || !label || !emoji || emoji.length > context.uiStatusEmojiMaxLength || seen.has(value)) {
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

  function applyViewerConfig(config) {
    scopeConfig.viewerConfig = config || {};
    scopeConfig.viewerConfigLoaded = true;
    scopeConfig.recentLimit = positiveInteger(getConfigValue(config, "docs_viewer.recently_added_limit"), context.defaultRecentLimit);
    searchRecent.recentLimit = scopeConfig.recentLimit;
    scopeConfig.uiStatuses = normalizeUiStatuses(config, context.viewerScope());
    scopeConfig.uiStatusByValue = new Map(scopeConfig.uiStatuses.map(function (status) {
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
    scopeConfig.managementText.statusPillSetLabel = getConfigText(config, "docs_viewer.status_pill_set_label", scopeConfig.managementText.statusPillSetLabel);
    scopeConfig.managementText.statusPillClearLabel = getConfigText(config, "docs_viewer.status_pill_clear_label", scopeConfig.managementText.statusPillClearLabel);
    scopeConfig.managementText.statusPillReadonlyLabel = getConfigText(config, "docs_viewer.status_pill_readonly_label", scopeConfig.managementText.statusPillReadonlyLabel);
    scopeConfig.managementText.statusMenuLabel = getConfigText(config, "docs_viewer.status_menu_label", scopeConfig.managementText.statusMenuLabel);
    scopeConfig.managementText.statusPillSaving = getConfigText(config, "docs_viewer.status_pill_saving", scopeConfig.managementText.statusPillSaving);
    scopeConfig.managementText.statusPillSaved = getConfigText(config, "docs_viewer.status_pill_saved", scopeConfig.managementText.statusPillSaved);
    scopeConfig.managementText.statusPillFailed = getConfigText(config, "docs_viewer.status_pill_failed", scopeConfig.managementText.statusPillFailed);
    if (context.managementController()) {
      context.managementController().applyConfig(config);
    }
    if (documentIndex.docs.length) {
      context.renderSidebar();
      context.renderStatusPills();
    }
    if (searchRecent.recentModeActive) {
      context.renderRecentMode();
    }
  }

  function loadViewerConfig(options) {
    var settings = options || {};
    if (settings.force) {
      scopeConfig.viewerConfigLoaded = false;
      scopeConfig.viewerConfigRequestPromise = null;
    }
    if (scopeConfig.viewerConfigLoaded) return Promise.resolve(null);
    if (scopeConfig.viewerConfigRequestPromise) return scopeConfig.viewerConfigRequestPromise;
    if (!docsViewerConfigUrl()) {
      applyViewerConfig({});
      return Promise.resolve(null);
    }

    scopeConfig.viewerConfigRequestPromise = Promise.all([
      loadDocsViewerConfig(settings),
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
        scopeConfig.viewerConfigRequestPromise = null;
      });
    return scopeConfig.viewerConfigRequestPromise;
  }

  function reloadDocsViewerConfig() {
    return loadViewerConfig({
      force: true,
      reloadNonce: String(Date.now())
    });
  }

  function loadDocsViewerText() {
    if (!uiTextUrl()) return Promise.resolve(null);
    return fetchJsonWithRetry(appendAssetVersion(uiTextUrl()), "Failed to load Docs Viewer UI text", "", dataRequestOptions())
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

  return {
    handleScopeChange: handleScopeChange,
    loadDocsViewerConfig: loadDocsViewerConfig,
    loadViewerConfig: loadViewerConfig,
    reloadDocsViewerConfig: reloadDocsViewerConfig,
    routeScopeFromUrl: routeScopeFromUrl
  };
}
