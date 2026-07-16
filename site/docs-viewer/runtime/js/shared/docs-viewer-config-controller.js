import {
  routeConfigScopeProjection
} from "./docs-viewer-route-config.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";
import {
  createDocsViewerScopeSelectMenu
} from "./docs-viewer-scope-select-menu.js";

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
  var scopeSelectMenu = createDocsViewerScopeSelectMenu({
    document: document,
    scopeSelect: scopeSelect,
    window: window
  });
  if (!Array.isArray(scopeConfig.scopeConfigs)) scopeConfig.scopeConfigs = [];
  if (!scopeConfig.scopeConfigsById) scopeConfig.scopeConfigsById = new Map();
  if (!Array.isArray(documentIndex.docs)) documentIndex.docs = [];

  function normalizeSubScopeConfig(rawSubScope) {
    if (!rawSubScope || typeof rawSubScope !== "object") return null;
    var subScope = String(rawSubScope.sub_scope || "").trim().toLowerCase();
    if (!subScope) return null;
    var manifestUrl = String(rawSubScope.manifest_url || "").trim();
    var byIdUrlBase = String(rawSubScope.by_id_url_base || "").trim().replace(/\/+$/, "");
    if (!manifestUrl || !byIdUrlBase) return null;
    return {
      subScope: subScope,
      title: String(rawSubScope.title || "").trim(),
      manifestUrl: manifestUrl,
      byIdUrlBase: byIdUrlBase
    };
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
    var subScopes = Array.isArray(rawScope.sub_scopes)
      ? rawScope.sub_scopes.map(normalizeSubScopeConfig).filter(Boolean)
      : [];
    return {
      scopeId: scopeId,
      scopeType: String(rawScope.scope_type || "").trim().toLowerCase(),
      meta: String(rawScope.meta || "").trim(),
      viewerBaseUrl: viewerBase,
      includeScopeParam: rawScope.include_scope_param === true,
      defaultDocId: String(rawScope.default_doc_id || "").trim(),
      indexTreeUrl: String(rawScope.index_tree_url || "").trim(),
      recentUrl: String(rawScope.recent_url || "").trim(),
      searchIndexUrl: String(rawScope.search_index_url || "").trim(),
      subScopes: subScopes,
      subScopesById: new Map(subScopes.map(function (config) {
        return [config.subScope, config];
      }))
    };
  }

  function normalizeConfigEnvelope(payload) {
    if (!payload || typeof payload !== "object") {
      throw new Error("Docs Viewer config must be a JSON object.");
    }
    if (payload.schema_version !== "docs_viewer_config_v1") {
      throw new Error("Docs Viewer config has an unsupported schema.");
    }
    return {
      rawScopes: payload.scopes,
      defaultScopeId: String(payload.default_scope_id || "").trim().toLowerCase(),
      docsViewerSettings: payload.docs_viewer && typeof payload.docs_viewer === "object" && !Array.isArray(payload.docs_viewer)
        ? payload.docs_viewer
        : {}
    };
  }

  function normalizeConfiguredScopes(envelope) {
    var configEnvelope = envelope || {};
    if (!Array.isArray(configEnvelope.rawScopes)) {
      throw new Error("Docs Viewer config requires a scopes array.");
    }
    var seen = new Set();
    var scopes = configEnvelope.rawScopes.map(normalizeBrowserScopeConfig).filter(Boolean).filter(function (config) {
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
      if (!config.indexTreeUrl) {
        throw new Error("Docs Viewer scope " + config.scopeId + " is missing index_tree_url.");
      }
      if (context.featurePolicy && context.featurePolicy.recent && !config.recentUrl) {
        throw new Error("Docs Viewer scope " + config.scopeId + " is missing recent_url.");
      }
      if (context.featurePolicy && context.featurePolicy.search && !config.searchIndexUrl) {
        throw new Error("Docs Viewer scope " + config.scopeId + " is missing search_index_url.");
      }
    });
    return {
      defaultScopeId: configEnvelope.defaultScopeId || scopes[0].scopeId,
      scopes: scopes,
      scopesById: new Map(scopes.map(function (config) {
        return [config.scopeId, config];
      }))
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

  function scopeTypeBadge(config) {
    var badges = getConfigValue(scopeConfig.docsViewerConfig, "docsViewerSettings.scope_type_badges");
    return badges && typeof badges === "object" && badges[config.scopeType] && typeof badges[config.scopeType] === "object"
      ? badges[config.scopeType]
      : null;
  }

  function scopeOptionRecord(config) {
    var badge = scopeTypeBadge(config);
    var emoji = badge ? String(badge.emoji || "").trim() : "";
    var meta = config.meta || (badge ? String(badge.label || "").trim() : "");
    return {
      value: config.scopeId,
      label: config.scopeId,
      emoji: emoji,
      meta: meta
    };
  }

  function renderScopeOptions() {
    if (!scopeSelect) return;
    var records = scopeConfig.scopeConfigs.map(scopeOptionRecord);
    scopeSelect.innerHTML = records.map(function (record) {
      return '<option value="' + escapeHtml(record.value) + '">' + escapeHtml((record.emoji ? record.emoji + " " : "") + record.label) + '</option>';
    }).join("");
    scopeSelect.value = context.viewerScope();
    scopeSelectMenu.render(records);
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
    root.dataset.indexTreeUrl = config.indexTreeUrl;
    root.dataset.recentUrl = config.recentUrl;
    root.dataset.searchIndexUrl = config.searchIndexUrl;
    root.dataset.defaultDocId = config.defaultDocId;
    root.dataset.viewerBaseUrl = routeProjection.viewerBaseUrl;
    root.dataset.includeScopeParam = routeProjection.includeScopeParam ? "true" : "false";
    renderScopeOptions();
  }

  function loadConfigEnvelope(options) {
    var settings = options || {};
    if (settings.force) {
      scopeConfig.docsViewerConfigLoaded = false;
      scopeConfig.docsViewerConfigRequestPromise = null;
    }
    if (scopeConfig.docsViewerConfigLoaded) return Promise.resolve(scopeConfig.docsViewerConfig);
    if (scopeConfig.docsViewerConfigRequestPromise) return scopeConfig.docsViewerConfigRequestPromise;
    if (typeof configService.fetchDocsViewerConfig !== "function") {
      return Promise.reject(new Error("Docs Viewer config service is not configured."));
    }

    scopeConfig.docsViewerConfigRequestPromise = configService.fetchDocsViewerConfig(settings)
      .then(function (payload) {
        var config = normalizeConfigEnvelope(payload);
        scopeConfig.docsViewerConfig = config;
        scopeConfig.docsViewerConfigLoaded = true;
        return config;
      })
      .finally(function () {
        scopeConfig.docsViewerConfigRequestPromise = null;
      });

    return scopeConfig.docsViewerConfigRequestPromise;
  }

  function loadConfiguredScopes(options) {
    var settings = options || {};
    if (settings.force) {
      scopeConfig.configuredScopesLoaded = false;
      scopeConfig.configuredScopesRequestPromise = null;
    }
    if (scopeConfig.configuredScopesLoaded) return Promise.resolve(scopeConfig.scopeConfigs);
    if (scopeConfig.configuredScopesRequestPromise) return scopeConfig.configuredScopesRequestPromise;

    scopeConfig.configuredScopesRequestPromise = loadConfigEnvelope(settings)
      .then(function (envelope) {
        var config = normalizeConfiguredScopes(envelope);
        scopeConfig.scopeConfigs = config.scopes;
        scopeConfig.scopeConfigsById = config.scopesById;
        scopeConfig.defaultScopeId = config.defaultScopeId;
        scopeConfig.configuredScopesLoaded = true;
        applyRouteScopeConfig(routeScopeFromUrl());
        return config.scopes;
      })
      .finally(function () {
        scopeConfig.configuredScopesRequestPromise = null;
      });
    return scopeConfig.configuredScopesRequestPromise;
  }

  function handleScopeChange() {
    if (!context.allowScopeQuery || !scopeSelect) return;
    var nextScope = String(scopeSelect.value || "").trim().toLowerCase();
    var config = scopeConfig.scopeConfigsById.get(nextScope);
    if (!config) {
      scopeSelect.value = context.viewerScope();
      scopeSelectMenu.project();
      return;
    }

    var url = new URL(context.routeViewerBaseUrl || context.viewerBaseUrl(), window.location.origin);
    url.searchParams.set("scope", nextScope);
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
    scopeConfig.recentLimit = positiveInteger(getConfigValue(config, "docs_viewer.recent_limit"), context.defaultRecentLimit);
    searchRecent.recentLimit = scopeConfig.recentLimit;
    scopeConfig.uiStatuses = normalizeUiStatuses(config, context.viewerScope());
    scopeConfig.uiStatusByValue = new Map(scopeConfig.uiStatuses.map(function (status) {
      return [status.ui_status, status];
    }));
    var nonViewableColor = String(getConfigValue(config, "docs_viewer.non_viewable_nav_color") || "").trim();
    if (nonViewableColor) {
      root.style.setProperty("--docs-viewer-draft-color", nonViewableColor);
    }
    if (typeof context.setRecentControlLabel === "function") context.setRecentControlLabel("Recent");
    if (context.managementController()) {
      context.managementController().applyConfig(config);
    }
    if (documentIndex.docs.length) {
      context.renderSidebar();
    }
    if (searchRecent.recentModeActive) {
      context.renderRecentMode();
    }
  }

  function loadViewerSettings(options) {
    var settings = options || {};
    if (settings.force) {
      scopeConfig.viewerConfigLoaded = false;
      scopeConfig.viewerConfigRequestPromise = null;
    }
    if (scopeConfig.viewerConfigLoaded) return Promise.resolve(null);
    if (scopeConfig.viewerConfigRequestPromise) return scopeConfig.viewerConfigRequestPromise;
    if (typeof configService.fetchDocsViewerConfig !== "function") {
      applyViewerConfig({});
      return Promise.resolve(null);
    }

    scopeConfig.viewerConfigRequestPromise = loadConfigEnvelope(settings)
      .then(function (configEnvelope) {
        configEnvelope = configEnvelope || {};
        var config = {
          docs_viewer: configEnvelope.docsViewerSettings || {}
        };
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

  function reloadViewerConfiguration() {
    var reloadOptions = {
      force: true,
      reloadNonce: String(Date.now())
    };
    scopeConfig.viewerConfigLoaded = false;
    scopeConfig.viewerConfigRequestPromise = null;
    var reloadDiscovery = context.featurePolicy && context.featurePolicy.configuredScopeDiscovery
      ? loadConfiguredScopes(reloadOptions)
      : loadConfigEnvelope(reloadOptions);
    return reloadDiscovery.then(function () {
      return loadViewerSettings();
    });
  }

  return {
    handleScopeChange: handleScopeChange,
    loadConfiguredScopes: loadConfiguredScopes,
    loadViewerSettings: loadViewerSettings,
    reloadViewerConfiguration: reloadViewerConfiguration,
    routeScopeFromUrl: routeScopeFromUrl
  };
}
