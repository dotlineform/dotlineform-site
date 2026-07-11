function cleanString(value) {
  return String(value || "").trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function localSurface(surface, authority) {
  var baseUrl = cleanBaseUrl(surface && surface.baseUrl);
  if (!baseUrl) return null;
  return {
    available: true,
    authority: authority,
    baseUrl: baseUrl
  };
}

export function createDocsViewerServiceAvailability(services) {
  var surfaces = services || {};
  return {
    generatedData: {
      available: true,
      local: Boolean(cleanBaseUrl(surfaces.generatedData && surfaces.generatedData.baseUrl))
    },
    source: {
      available: Boolean(cleanBaseUrl(surfaces.source && surfaces.source.baseUrl))
    },
    management: {
      available: Boolean(cleanBaseUrl(surfaces.management && surfaces.management.baseUrl))
    }
  };
}

export function createDocsViewerServiceContext(options) {
  var settings = options || {};
  var routeContext = settings.routeContext || {};
  var routeConfig = routeContext.routeConfig || {};
  var services = routeConfig.services || {};
  var generatedReadBaseUrl = cleanBaseUrl(services.generatedData && services.generatedData.baseUrl);

  return {
    generatedData: {
      available: true,
      authority: generatedReadBaseUrl ? "local generated-read service" : "generated static asset",
      baseUrl: generatedReadBaseUrl
    },
    config: {
      available: true,
      authority: "browser-safe config asset",
      docsViewerConfigUrl: cleanString(routeContext.docsViewerConfigUrl)
    },
    source: localSurface(services.source, "source service endpoint; backend capability-gated"),
    management: localSurface(services.management, "management service endpoint; backend capability-gated")
  };
}
