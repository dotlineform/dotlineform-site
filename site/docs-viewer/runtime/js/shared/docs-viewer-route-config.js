import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  docsViewerRouteFeatureEnabled,
  normalizeDocsViewerRouteFeatures
} from "./docs-viewer-route-features.js";

export const DOCS_VIEWER_ROUTE_CONFIG_SCHEMA = "docs_viewer_route_config_v4";
export const DOCS_VIEWER_ROUTE_CONFIG_REGISTRY_SCHEMA = "docs_viewer_route_config_registry_v1";
export const DOCS_VIEWER_MANAGEMENT_ROUTE_PATH = "/docs/";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function normalizeBoolean(value) {
  return value === true || value === "true";
}

function normalizePath(value) {
  return cleanString(value);
}

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

function normalizeRoutePath(value) {
  var path = cleanString(value);
  if (!path) return "";
  try {
    path = new URL(path, "http://docs-viewer.local").pathname;
  } catch (error) {
    return "";
  }
  path = path.replace(/\/+$/, "/") || "/";
  return path;
}

export function isDocsManagementRoutePath(value) {
  return normalizeRoutePath(value) === DOCS_VIEWER_MANAGEMENT_ROUTE_PATH;
}

function routeConfigPath(rawConfig) {
  return cleanString(rawConfig.route_path || rawConfig.viewer_base_url);
}

function normalizePanelDefaults(rawPanels) {
  var panels = rawPanels && typeof rawPanels === "object" && !Array.isArray(rawPanels) ? rawPanels : {};
  var index = panels.index && typeof panels.index === "object" ? panels.index : {};
  var mainPanel = panels.main && typeof panels.main === "object" ? panels.main : {};
  var info = panels.info && typeof panels.info === "object" ? panels.info : {};
  return {
    index: {
      enabled: index.enabled !== false,
      defaultState: cleanString(index.default_state) || "normal"
    },
    main: {
      enabled: mainPanel.enabled !== false,
      defaultView: cleanString(mainPanel.default_view) || "rendered-document"
    },
    info: {
      enabled: info.enabled !== false,
      defaultView: cleanString(info.default_view) || "metadata-info"
    }
  };
}

function normalizeRouteUi(rawUi) {
  var ui = rawUi && typeof rawUi === "object" && !Array.isArray(rawUi) ? rawUi : {};
  var routeShell = ui.route_shell && typeof ui.route_shell === "object" && !Array.isArray(ui.route_shell)
    ? ui.route_shell
    : {};
  var viewerSearch = ui.viewer_search && typeof ui.viewer_search === "object" && !Array.isArray(ui.viewer_search)
    ? ui.viewer_search
    : {};
  return {
    routeShell: {
      configured: Boolean(ui.route_shell),
      pageTitle: cleanString(routeShell.page_title),
      bodyClass: cleanString(routeShell.body_class)
    },
    viewerSearch: {
      configured: Boolean(ui.viewer_search),
      placeholder: cleanString(viewerSearch.placeholder) || "search docs",
      ariaLabel: cleanString(viewerSearch.aria_label) || "Search docs"
    }
  };
}

function normalizeViewPolicy(rawPolicy) {
  var policy = rawPolicy && typeof rawPolicy === "object" && !Array.isArray(rawPolicy) ? rawPolicy : {};
  function ids(value) {
    if (!Array.isArray(value)) return [];
    var seen = new Set();
    return value.map(cleanString).filter(function (id) {
      if (!id || seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }
  return {
    hiddenViews: ids(policy.hidden_views),
    hiddenModes: ids(policy.hidden_modes),
    hiddenControls: ids(policy.hidden_controls)
  };
}

function normalizePreservedQueryParams(value) {
  if (!Array.isArray(value)) return [];
  var seen = new Set();
  return value.map(cleanString).filter(function (name) {
    if (!/^[a-z][a-z0-9_-]*$/i.test(name) || seen.has(name)) return false;
    seen.add(name);
    return true;
  });
}

function routeConfigSource(settings) {
  if (settings.routeConfig) {
    return {
      source: cleanString(settings.routeConfigSource) || "explicit",
      config: settings.routeConfig
    };
  }
  throw new Error("Docs Viewer route config requires an explicit config record or route-config registry.");
}

function routeConfigUrlFromDataset(root) {
  return root && root.dataset ? cleanString(root.dataset.routeConfigUrl) : "";
}

function routeIdFromDataset(root) {
  return root && root.dataset ? cleanString(root.dataset.routeId) : "";
}

function normalizeRegistryRoutes(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Docs Viewer route config registry must be a JSON object.");
  }
  if (payload.schema_version && payload.schema_version !== DOCS_VIEWER_ROUTE_CONFIG_REGISTRY_SCHEMA) {
    throw new Error("Docs Viewer route config registry has an unsupported schema.");
  }
  if (Array.isArray(payload.routes)) return payload.routes;
  throw new Error("Docs Viewer route config registry requires routes array.");
}

function pathMatchesRoute(windowRef, routeRecord) {
  if (!windowRef || !windowRef.location || !routeRecord) return false;
  var routePath = cleanString(routeRecord.route_path || routeRecord.viewer_base_url);
  if (!routePath) return false;
  try {
    var currentPath = windowRef.location.pathname.replace(/\/+$/, "/") || "/";
    var candidatePath = new URL(routePath, windowRef.location.origin).pathname.replace(/\/+$/, "/") || "/";
    return currentPath === candidatePath;
  } catch (error) {
    return false;
  }
}

function routeConfigFromRegistryPayload(payload, options) {
  var settings = options || {};
  var root = settings.root || null;
  var windowRef = settings.window || (typeof window !== "undefined" ? window : null);
  var requestedRouteId = cleanString(settings.routeId) || routeIdFromDataset(root);
  var routes = normalizeRegistryRoutes(payload).filter(function (record) {
    return record && typeof record === "object" && !Array.isArray(record);
  });
  var selected = null;
  if (requestedRouteId) {
    selected = routes.find(function (record) {
      return cleanString(record.route_id) === requestedRouteId;
    }) || null;
  }
  if (!selected) {
    selected = routes.find(function (record) {
      return pathMatchesRoute(windowRef, record);
    }) || null;
  }
  if (!selected) {
    throw new Error("Docs Viewer route config registry does not define route " + (requestedRouteId || "for current path") + ".");
  }
  return selected;
}

function fetchRouteConfigRegistry(url, options) {
  var settings = options || {};
  var fetchImpl = settings.fetch || defaultFetch;
  var fetchUrl = appendAssetVersion(url, settings.assetVersion);
  return fetchImpl(fetchUrl, {
    headers: { Accept: "application/json" },
    cache: "default"
  }).then(function (response) {
    if (!response.ok) {
      var error = new Error("Failed to load Docs Viewer route config (" + response.status + ")");
      error.status = response.status;
      throw error;
    }
    return response.json();
  });
}

function requireRouteConfigField(value, fieldName) {
  var cleaned = cleanString(value);
  if (!cleaned) {
    throw new Error("Docs Viewer route config requires " + fieldName + ".");
  }
  return cleaned;
}

function normalizeAppKind(value) {
  var kind = cleanString(value).toLowerCase();
  if (kind !== "public" && kind !== "manage" && kind !== "review") {
    throw new Error("Docs Viewer route config requires app_kind to be public, manage, or review.");
  }
  return kind;
}

function normalizeServiceSurface(rawSurface) {
  var surface = rawSurface && typeof rawSurface === "object" && !Array.isArray(rawSurface)
    ? rawSurface
    : {};
  return {
    baseUrl: cleanBaseUrl(surface.base_url)
  };
}

function normalizeServiceSurfaces(rawServices) {
  var services = rawServices && typeof rawServices === "object" && !Array.isArray(rawServices)
    ? rawServices
    : {};
  return {
    generatedData: normalizeServiceSurface(services.generated_data),
    source: normalizeServiceSurface(services.source),
    management: normalizeServiceSurface(services.management)
  };
}

function normalizeRecentBasis(value, enabled) {
  var basis = cleanString(value).toLowerCase();
  if (enabled && basis !== "added" && basis !== "edited") {
    throw new Error("Docs Viewer routes with Recent enabled must declare recent_basis as added or edited.");
  }
  if (!enabled && basis) {
    throw new Error("Docs Viewer routes cannot declare recent_basis without the Recent feature.");
  }
  return basis;
}

export function resolveDocsViewerRouteConfig(options) {
  var settings = options || {};
  var resolvedSource = routeConfigSource(settings);
  var rawConfig = resolvedSource.config || {};
  if (Object.prototype.hasOwnProperty.call(rawConfig, "hosted_views")) {
    throw new Error("Docs Viewer route config cannot define hosted_views; views are code-owned.");
  }
  if (rawConfig.ui && Object.prototype.hasOwnProperty.call(rawConfig.ui, "main_view_toolbar")) {
    throw new Error("Docs Viewer route config cannot define main_view_toolbar; hide known controls through view_policy.");
  }
  var access = rawConfig.access && typeof rawConfig.access === "object" ? rawConfig.access : {};
  var appKind = normalizeAppKind(rawConfig.app_kind);
  var requestedAppKind = cleanString(settings.appKind).toLowerCase();
  if (requestedAppKind && requestedAppKind !== appKind) {
    throw new Error("Docs Viewer entrypoint app kind does not match route config app_kind.");
  }
  var allowScopeQuery = normalizeBoolean(access.allow_scope_query);
  var docsManagementRoute = isDocsManagementRoutePath(routeConfigPath(rawConfig));
  var managementUi = appKind === "manage" && normalizeBoolean(access.management_ui);
  var services = normalizeServiceSurfaces(rawConfig.services);
  var features = normalizeDocsViewerRouteFeatures(rawConfig.features);
  var docsPaths = rawConfig.docs_paths && typeof rawConfig.docs_paths === "object" ? rawConfig.docs_paths : {};
  var configUrls = rawConfig.config_urls && typeof rawConfig.config_urls === "object" ? rawConfig.config_urls : {};
  var schemaVersion = cleanString(rawConfig.schema_version) || DOCS_VIEWER_ROUTE_CONFIG_SCHEMA;
  if (schemaVersion !== DOCS_VIEWER_ROUTE_CONFIG_SCHEMA) {
    throw new Error("Docs Viewer route config has an unsupported schema.");
  }
  var searchEnabled = docsViewerRouteFeatureEnabled(features, "search");
  var recentEnabled = docsViewerRouteFeatureEnabled(features, "recent");
  var recentBasis = normalizeRecentBasis(rawConfig.recent_basis, recentEnabled);
  var reportsEnabled = docsViewerRouteFeatureEnabled(features, "reports");
  return {
    schemaVersion: schemaVersion,
    source: resolvedSource.source,
    appKind: appKind,
    routeId: requireRouteConfigField(rawConfig.route_id, "route_id"),
    isDocsManagementRoute: docsManagementRoute,
    defaultScopeId: requireRouteConfigField(rawConfig.default_scope_id, "default_scope_id"),
    includeScopeParam: normalizeBoolean(rawConfig.include_scope_param),
    preserveQueryParams: normalizePreservedQueryParams(rawConfig.preserve_query_params),
    viewerBaseUrl: requireRouteConfigField(rawConfig.viewer_base_url, "viewer_base_url"),
    docsViewerConfigUrl: requireRouteConfigField(configUrls.docs_viewer, "config_urls.docs_viewer"),
    reportRegistryUrl: reportsEnabled
      ? requireRouteConfigField(configUrls.report_registry, "config_urls.report_registry")
      : cleanString(configUrls.report_registry),
    indexTreeUrl: normalizePath(requireRouteConfigField(docsPaths.index_tree_url, "docs_paths.index_tree_url")),
    recentUrl: normalizePath(recentEnabled
      ? requireRouteConfigField(docsPaths.recent_url, "docs_paths.recent_url")
      : docsPaths.recent_url),
    recentBasis: recentBasis,
    searchIndexUrl: normalizePath(searchEnabled
      ? requireRouteConfigField(docsPaths.search_index_url, "docs_paths.search_index_url")
      : docsPaths.search_index_url),
    access: {
      allowScopeQuery: allowScopeQuery,
      managementUi: managementUi
    },
    services: services,
    features: features,
    panels: normalizePanelDefaults(rawConfig.panels),
    ui: normalizeRouteUi(rawConfig.ui),
    viewPolicy: normalizeViewPolicy(rawConfig.view_policy)
  };
}

export function resolveDocsViewerRouteConfigAsync(options) {
  var settings = options || {};
  var root = settings.root || null;
  var routeConfigUrl = cleanString(settings.routeConfigUrl) || routeConfigUrlFromDataset(root);
  if (settings.routeConfig || !routeConfigUrl) {
    try {
      return Promise.resolve(resolveDocsViewerRouteConfig(settings));
    } catch (error) {
      return Promise.reject(error);
    }
  }
  return fetchRouteConfigRegistry(routeConfigUrl, settings)
    .then(function (payload) {
      var rawRouteConfig = routeConfigFromRegistryPayload(payload, settings);
      return resolveDocsViewerRouteConfig(Object.assign({}, settings, {
        routeConfig: rawRouteConfig,
        routeConfigSource: "registry"
      }));
    });
}

export function routeConfigScopeProjection(scopeConfig, options) {
  var settings = options || {};
  var config = scopeConfig && typeof scopeConfig === "object" ? scopeConfig : {};
  var allowScopeQuery = settings.allowScopeQuery === true;
  var routeViewerBaseUrl = cleanString(settings.routeViewerBaseUrl);
  var windowRef = settings.window || (typeof window !== "undefined" ? window : null);
  var fallbackPath = windowRef && windowRef.location ? windowRef.location.pathname : "";
  var viewerBaseUrl = allowScopeQuery ? (routeViewerBaseUrl || fallbackPath) : cleanString(config.viewerBaseUrl);
  var includeScopeParam = allowScopeQuery ? true : Boolean(config.includeScopeParam);
  var subScopes = Array.isArray(config.subScopes) ? config.subScopes : [];
  return {
    defaultRouteDocId: cleanString(config.defaultDocId),
    includeScopeParam: includeScopeParam,
    indexTreeUrl: appendAssetVersion(config.indexTreeUrl || "", settings.assetVersion),
    recentUrl: appendAssetVersion(config.recentUrl || "", settings.assetVersion),
    searchIndexUrl: appendAssetVersion(config.searchIndexUrl || "", settings.assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerPathname: windowRef && windowRef.location
      ? new URL(viewerBaseUrl || fallbackPath, windowRef.location.origin).pathname
      : viewerBaseUrl,
    viewerScope: cleanString(config.scopeId),
    subScopes: subScopes,
    subScopesById: config.subScopesById instanceof Map
      ? config.subScopesById
      : new Map(subScopes.map(function (subScopeConfig) {
        return [cleanString(subScopeConfig.subScope), subScopeConfig];
      }))
  };
}
