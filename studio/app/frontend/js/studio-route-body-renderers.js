const ROUTE_BODY_RENDERERS = {
  studio_home: async (config, importModule) => {
    const module = await importModule("./studio-home-shell.js");
    return module.renderStudioHomeShell(config);
  },
  bulk_add_work: async (config, importModule) => {
    const module = await importModule("./bulk-add-work-shell.js");
    return module.renderBulkAddWorkShell(config);
  },
  catalogue_field_registry: async (_config, importModule) => {
    const module = await importModule("./catalogue-field-registry-shell.js");
    return module.renderCatalogueFieldRegistryShell();
  },
  catalogue_series_editor: async (config, importModule) => {
    const module = await importModule("./catalogue-series-shell.js");
    return module.renderCatalogueSeriesShell(config);
  },
  catalogue_status: async (_config, importModule) => {
    const module = await importModule("./catalogue-status-shell.js");
    return module.renderCatalogueStatusShell();
  },
  catalogue_work_editor: async (config, importModule) => {
    const module = await importModule("./catalogue-work-shell.js");
    return module.renderCatalogueWorkShell(config);
  },
  project_state: async (_config, importModule) => {
    const module = await importModule("./project-state-shell.js");
    return module.renderProjectStateShell();
  },
  studio_works: async (_config, importModule) => {
    const module = await importModule("./studio-works-shell.js");
    return module.renderStudioWorksShell();
  }
};

export function hasStudioRouteBodyRenderer(routeId) {
  return Boolean(ROUTE_BODY_RENDERERS[normalizeRouteId(routeId)]);
}

export async function renderStudioRouteBody(routeId, config, options = {}) {
  const normalizedRouteId = normalizeRouteId(routeId);
  const renderer = ROUTE_BODY_RENDERERS[normalizedRouteId];
  if (!renderer) {
    throw new Error(`Studio route body is not registered: ${normalizedRouteId}`);
  }
  const importModule = typeof options.importModule === "function" ? options.importModule : importDefault;
  return renderer(config, importModule);
}

function importDefault(path) {
  return import(new URL(path, import.meta.url).href);
}

function normalizeRouteId(value) {
  return String(value || "").trim().replace(/-/g, "_").toLowerCase();
}
