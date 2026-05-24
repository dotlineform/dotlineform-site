import {
  appendAssetVersion,
  fetchJsonWithRetry
} from "./docs-viewer-data.js";
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
  var state = context.state;
  var root = context.root;
  var scopeSelect = context.scopeSelect;
  var recentButton = context.recentButton;

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
    var viewerScope = context.viewerScope();
    if (context.allowScopeQuery && requestedScope) {
      if (!state.scopeConfigsById.has(requestedScope)) {
        throw new Error("Unknown docs scope: " + requestedScope);
      }
      return requestedScope;
    }
    if (!context.allowScopeQuery) {
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
    scopeSelect.value = context.viewerScope();
  }

  function applyRouteScopeConfig(scope) {
    var config = state.scopeConfigsById.get(scope);
    if (!config) {
      throw new Error("Unknown docs scope: " + scope);
    }
    var viewerBaseUrl = context.allowScopeQuery ? (context.routeViewerBaseUrl || window.location.pathname) : config.viewerBaseUrl;
    var includeScopeParam = context.allowScopeQuery ? true : config.includeScopeParam;
    context.applyRouteGlobals({
      defaultRouteDocId: config.defaultDocId,
      includeScopeParam: includeScopeParam,
      indexUrl: appendAssetVersion(config.indexUrl),
      searchIndexUrl: appendAssetVersion(config.searchIndexUrl),
      viewerBaseUrl: viewerBaseUrl,
      viewerPathname: new URL(viewerBaseUrl, window.location.origin).pathname,
      viewerScope: scope
    });
    root.dataset.viewerScope = scope;
    root.dataset.indexUrl = config.indexUrl;
    root.dataset.searchIndexUrl = config.searchIndexUrl;
    root.dataset.defaultDocId = config.defaultDocId;
    root.dataset.viewerBaseUrl = viewerBaseUrl;
    root.dataset.includeScopeParam = includeScopeParam ? "true" : "false";
    renderScopeOptions();
  }

  function loadDocsViewerConfig() {
    if (state.docsViewerConfigLoaded) return Promise.resolve(state.docsViewerConfig);
    if (state.docsViewerConfigRequestPromise) return state.docsViewerConfigRequestPromise;
    if (!context.docsViewerConfigUrl) {
      return Promise.reject(new Error("Docs Viewer config URL is not configured."));
    }

    state.docsViewerConfigRequestPromise = fetchJsonWithRetry(
      context.docsViewerConfigUrl,
      "Failed to load Docs Viewer config",
      "",
      context.dataRequestOptions()
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
    if (!context.allowScopeQuery || !scopeSelect) return;
    var nextScope = String(scopeSelect.value || "").trim().toLowerCase();
    var config = state.scopeConfigsById.get(nextScope);
    if (!config) {
      scopeSelect.value = context.viewerScope();
      return;
    }

    var url = new URL(context.routeViewerBaseUrl || context.viewerBaseUrl(), window.location.origin);
    url.searchParams.set("scope", nextScope);
    if (state.managementMode || context.getCurrentMode() === context.managementMode) {
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
    state.viewerConfig = config || {};
    state.viewerConfigLoaded = true;
    state.recentLimit = positiveInteger(getConfigValue(config, "docs_viewer.recently_added_limit"), context.defaultRecentLimit);
    state.uiStatuses = normalizeUiStatuses(config, context.viewerScope());
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
    if (context.managementController()) {
      context.managementController().applyConfig(config);
    }
    if (state.docs.length) {
      context.renderSidebar();
      context.renderStatusPills();
    }
    if (state.recentModeActive) {
      context.renderRecentMode();
    }
  }

  function loadViewerConfig() {
    if (state.viewerConfigLoaded) return Promise.resolve(null);
    if (state.viewerConfigRequestPromise) return state.viewerConfigRequestPromise;
    if (!context.docsViewerConfigUrl) {
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
    if (!context.uiTextUrl) return Promise.resolve(null);
    return fetchJsonWithRetry(appendAssetVersion(context.uiTextUrl), "Failed to load Docs Viewer UI text", "", context.dataRequestOptions())
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
    routeScopeFromUrl: routeScopeFromUrl
  };
}
