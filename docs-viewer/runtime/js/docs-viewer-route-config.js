import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  normalizeHostedViewCapabilities
} from "./docs-viewer-hosted-view-capabilities.js";

export const DOCS_VIEWER_ROUTE_CONFIG_SCHEMA = "docs_viewer_route_config_v1";
export const DOCS_VIEWER_ROUTE_CONFIG_REGISTRY_SCHEMA = "docs_viewer_route_config_registry_v1";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function firstPresent() {
  for (var i = 0; i < arguments.length; i += 1) {
    if (arguments[i] !== undefined && arguments[i] !== null) return arguments[i];
  }
  return undefined;
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

function normalizeRouteType(value, allowManagement) {
  var routeType = cleanString(value).toLowerCase();
  if (routeType === "manage" || routeType === "public") return routeType;
  return allowManagement ? "manage" : "public";
}

function normalizePanelDefaults(rawPanels) {
  var panels = rawPanels && typeof rawPanels === "object" && !Array.isArray(rawPanels) ? rawPanels : {};
  var index = panels.index && typeof panels.index === "object" ? panels.index : {};
  var mainPanel = panels.main && typeof panels.main === "object" ? panels.main : {};
  var info = panels.info && typeof panels.info === "object" ? panels.info : {};
  return {
    index: {
      enabled: index.enabled !== false,
      defaultState: cleanString(index.default_state || index.defaultState) || "normal"
    },
    main: {
      enabled: mainPanel.enabled !== false,
      defaultView: cleanString(mainPanel.default_view || mainPanel.defaultView) || "rendered-document"
    },
    info: {
      enabled: info.enabled !== false,
      defaultView: cleanString(info.default_view || info.defaultView) || "metadata-info"
    }
  };
}

function normalizeHostedViews(rawHostedViews) {
  var hostedViews = rawHostedViews && typeof rawHostedViews === "object" && !Array.isArray(rawHostedViews)
    ? rawHostedViews
    : {};
  var records = Array.isArray(hostedViews.records) ? hostedViews.records : [];
  return {
    records: records.map(function (record) {
      if (!record || typeof record !== "object") return null;
      var id = cleanString(record.id);
      if (!id) return null;
      return {
        id: id,
        label: cleanString(record.label) || id,
        panel: cleanString(record.panel) || "main",
        access: cleanString(record.access) || "public",
        availability: cleanString(record.availability) || "available",
        module: cleanString(record.module),
        renderer: cleanString(record.renderer),
        placeholderText: cleanString(record.placeholder_text || record.placeholderText),
        capabilities: normalizeHostedViewCapabilities(record.capabilities)
      };
    }).filter(Boolean)
  };
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
  if (payload.routes && typeof payload.routes === "object") {
    return Object.keys(payload.routes).map(function (key) {
      var record = payload.routes[key];
      if (record && typeof record === "object" && !Array.isArray(record) && !record.route_id) {
        return Object.assign({ route_id: key }, record);
      }
      return record;
    });
  }
  throw new Error("Docs Viewer route config registry requires routes.");
}

function pathMatchesRoute(windowRef, routeRecord) {
  if (!windowRef || !windowRef.location || !routeRecord) return false;
  var routePath = cleanString(routeRecord.route_path || routeRecord.routePath || routeRecord.viewer_base_url || routeRecord.viewerBaseUrl);
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
      return cleanString(record.route_id || record.routeId) === requestedRouteId;
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

export function resolveDocsViewerRouteConfig(options) {
  var settings = options || {};
  var resolvedSource = routeConfigSource(settings);
  var rawConfig = resolvedSource.config || {};
  var access = rawConfig.access && typeof rawConfig.access === "object" ? rawConfig.access : {};
  var allowManagement = normalizeBoolean(firstPresent(
    access.allow_management,
    access.allowManagement,
    rawConfig.allow_management,
    rawConfig.allowManagement
  ));
  var allowScopeQuery = normalizeBoolean(
    firstPresent(access.allow_scope_query, access.allowScopeQuery, rawConfig.allow_scope_query, rawConfig.allowScopeQuery)
  );
  var routeType = normalizeRouteType(firstPresent(rawConfig.route_type, rawConfig.routeType), allowManagement);
  var docsPaths = rawConfig.docs_paths && typeof rawConfig.docs_paths === "object" ? rawConfig.docs_paths : {};
  var configUrls = rawConfig.config_urls && typeof rawConfig.config_urls === "object" ? rawConfig.config_urls : {};
  return {
    schemaVersion: cleanString(firstPresent(rawConfig.schema_version, rawConfig.schemaVersion)) || DOCS_VIEWER_ROUTE_CONFIG_SCHEMA,
    source: resolvedSource.source,
    routeId: cleanString(firstPresent(rawConfig.route_id, rawConfig.routeId)) || routeType,
    routeType: routeType,
    defaultScopeId: cleanString(firstPresent(rawConfig.default_scope_id, rawConfig.defaultScopeId)),
    defaultDocId: cleanString(firstPresent(rawConfig.default_doc_id, rawConfig.defaultDocId)),
    includeScopeParam: normalizeBoolean(firstPresent(rawConfig.include_scope_param, rawConfig.includeScopeParam)),
    allowScopeQuery: allowScopeQuery,
    viewerBaseUrl: cleanString(firstPresent(rawConfig.viewer_base_url, rawConfig.viewerBaseUrl)),
    generatedBaseUrl: cleanString(firstPresent(rawConfig.generated_base_url, rawConfig.generatedBaseUrl)),
    docsViewerConfigUrl: cleanString(firstPresent(configUrls.docs_viewer, configUrls.docsViewer)),
    uiTextUrl: cleanString(firstPresent(configUrls.ui_text, configUrls.uiText)),
    reportRegistryUrl: cleanString(configUrls.report_registry),
    indexUrl: normalizePath(firstPresent(docsPaths.index_url, docsPaths.indexUrl)),
    searchIndexUrl: normalizePath(firstPresent(docsPaths.search_index_url, docsPaths.searchIndexUrl)),
    access: {
      allowManagement: allowManagement,
      allowScopeQuery: allowScopeQuery,
      managementBaseUrl: allowManagement
        ? cleanBaseUrl(firstPresent(access.management_base_url, access.managementBaseUrl))
        : "",
      managementModeValue: cleanString(access.management_mode_value || access.managementModeValue) || "manage"
    },
    panels: normalizePanelDefaults(rawConfig.panels),
    hostedViews: normalizeHostedViews(rawConfig.hosted_views || rawConfig.hostedViews)
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
  return {
    defaultRouteDocId: cleanString(config.defaultDocId),
    includeScopeParam: includeScopeParam,
    indexUrl: appendAssetVersion(config.indexUrl || "", settings.assetVersion),
    searchIndexUrl: appendAssetVersion(config.searchIndexUrl || "", settings.assetVersion),
    viewerBaseUrl: viewerBaseUrl,
    viewerPathname: windowRef && windowRef.location
      ? new URL(viewerBaseUrl || fallbackPath, windowRef.location.origin).pathname
      : viewerBaseUrl,
    viewerScope: cleanString(config.scopeId)
  };
}
