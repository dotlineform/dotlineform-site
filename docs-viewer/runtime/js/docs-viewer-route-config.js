import {
  appendAssetVersion
} from "./docs-viewer-data.js";

export const DOCS_VIEWER_ROUTE_CONFIG_SCHEMA = "docs_viewer_route_config_v1";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function datasetFlag(root, name) {
  return Boolean(root && root.dataset && root.dataset[name] === "true");
}

function normalizeBoolean(value) {
  return value === true || value === "true";
}

function normalizePath(value) {
  return cleanString(value);
}

function normalizeRouteType(value, allowManagement) {
  var routeType = cleanString(value).toLowerCase();
  if (routeType === "manage" || routeType === "public") return routeType;
  return allowManagement ? "manage" : "public";
}

function normalizePanelDefaults(rawPanels) {
  var panels = rawPanels && typeof rawPanels === "object" && !Array.isArray(rawPanels) ? rawPanels : {};
  var index = panels.index && typeof panels.index === "object" ? panels.index : {};
  var documentPanel = panels.document && typeof panels.document === "object" ? panels.document : {};
  var info = panels.info && typeof panels.info === "object" ? panels.info : {};
  return {
    index: {
      enabled: index.enabled !== false,
      defaultState: cleanString(index.default_state || index.defaultState) || "normal"
    },
    document: {
      enabled: documentPanel.enabled !== false,
      defaultView: cleanString(documentPanel.default_view || documentPanel.defaultView) || "document"
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
        panel: cleanString(record.panel) || "document",
        access: cleanString(record.access) || "public",
        availability: cleanString(record.availability) || "available",
        module: cleanString(record.module)
      };
    }).filter(Boolean)
  };
}

function routeConfigFromDataset(root) {
  var dataset = root && root.dataset ? root.dataset : {};
  return {
    schema_version: DOCS_VIEWER_ROUTE_CONFIG_SCHEMA,
    route_id: cleanString(dataset.routeId),
    route_type: "",
    default_scope_id: cleanString(dataset.viewerScope),
    default_doc_id: cleanString(dataset.defaultDocId),
    include_scope_param: datasetFlag(root, "includeScopeParam"),
    allow_scope_query: datasetFlag(root, "allowScopeQuery"),
    viewer_base_url: cleanString(dataset.viewerBaseUrl),
    generated_base_url: cleanString(dataset.generatedBaseUrl),
    access: {
      allow_management: datasetFlag(root, "allowManagement"),
      allow_scope_query: datasetFlag(root, "allowScopeQuery"),
      management_base_url: cleanString(dataset.managementBaseUrl),
      management_mode_value: "manage"
    },
    docs_paths: {
      index_url: cleanString(dataset.indexUrl),
      search_index_url: cleanString(dataset.searchIndexUrl)
    },
    config_urls: {
      docs_viewer: cleanString(dataset.docsViewerConfigUrl),
      ui_text: cleanString(dataset.uiTextUrl),
      report_registry: cleanString(dataset.reportRegistryUrl)
    },
    panels: {
      index: { enabled: true, default_state: "normal" },
      document: { enabled: true, default_view: "document" },
      info: { enabled: true, default_view: "metadata-info" }
    },
    hosted_views: {
      records: []
    }
  };
}

export function resolveDocsViewerRouteConfig(options) {
  var settings = options || {};
  var root = settings.root || null;
  var rawConfig = settings.routeConfig || routeConfigFromDataset(root);
  var access = rawConfig.access && typeof rawConfig.access === "object" ? rawConfig.access : {};
  var allowManagement = normalizeBoolean(access.allow_management != null ? access.allow_management : rawConfig.allow_management);
  var allowScopeQuery = normalizeBoolean(
    access.allow_scope_query != null ? access.allow_scope_query : rawConfig.allow_scope_query
  );
  var routeType = normalizeRouteType(rawConfig.route_type, allowManagement);
  var docsPaths = rawConfig.docs_paths && typeof rawConfig.docs_paths === "object" ? rawConfig.docs_paths : {};
  var configUrls = rawConfig.config_urls && typeof rawConfig.config_urls === "object" ? rawConfig.config_urls : {};
  return {
    schemaVersion: cleanString(rawConfig.schema_version) || DOCS_VIEWER_ROUTE_CONFIG_SCHEMA,
    source: settings.routeConfig ? "explicit" : "dataset",
    routeId: cleanString(rawConfig.route_id) || routeType,
    routeType: routeType,
    defaultScopeId: cleanString(rawConfig.default_scope_id || rawConfig.defaultScopeId),
    defaultDocId: cleanString(rawConfig.default_doc_id || rawConfig.defaultDocId),
    includeScopeParam: normalizeBoolean(rawConfig.include_scope_param || rawConfig.includeScopeParam),
    allowScopeQuery: allowScopeQuery,
    viewerBaseUrl: cleanString(rawConfig.viewer_base_url || rawConfig.viewerBaseUrl),
    generatedBaseUrl: cleanString(rawConfig.generated_base_url || rawConfig.generatedBaseUrl),
    docsViewerConfigUrl: cleanString(configUrls.docs_viewer || configUrls.docsViewer),
    uiTextUrl: cleanString(configUrls.ui_text || configUrls.uiText),
    reportRegistryUrl: cleanString(configUrls.report_registry || configUrls.reportRegistry),
    indexUrl: normalizePath(docsPaths.index_url || docsPaths.indexUrl),
    searchIndexUrl: normalizePath(docsPaths.search_index_url || docsPaths.searchIndexUrl),
    access: {
      allowManagement: allowManagement,
      allowScopeQuery: allowScopeQuery,
      managementBaseUrl: allowManagement ? cleanBaseUrl(access.management_base_url || access.managementBaseUrl) : "",
      managementModeValue: cleanString(access.management_mode_value || access.managementModeValue) || "manage"
    },
    panels: normalizePanelDefaults(rawConfig.panels),
    hostedViews: normalizeHostedViews(rawConfig.hosted_views || rawConfig.hostedViews)
  };
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
