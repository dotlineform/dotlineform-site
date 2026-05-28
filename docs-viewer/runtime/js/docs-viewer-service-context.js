function cleanString(value) {
  return String(value || "").trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

export function createDocsViewerServiceContext(options) {
  var settings = options || {};
  var routeContext = settings.routeContext || {};
  var access = routeContext.access || {};
  var allowManagement = Boolean(access.allowManagement);
  var managementBaseUrl = allowManagement ? cleanBaseUrl(routeContext.managementBaseUrl) : "";
  var generatedReadBaseUrl = allowManagement ? cleanBaseUrl(routeContext.generatedBaseUrl || managementBaseUrl) : "";

  return {
    access: {
      allowManagement: allowManagement,
      publicReadOnly: !allowManagement
    },
    generatedRead: {
      authority: generatedReadBaseUrl ? "local generated-read service" : "generated static asset",
      baseUrl: generatedReadBaseUrl
    },
    config: {
      authority: "browser-safe config asset",
      docsViewerConfigUrl: cleanString(routeContext.docsViewerConfigUrl),
      uiTextUrl: cleanString(routeContext.uiTextUrl)
    },
    reports: {
      authority: "browser-safe config asset",
      reportRegistryUrl: cleanString(routeContext.reportRegistryUrl)
    },
    management: allowManagement
      ? {
        authority: "management backend capability/write endpoint",
        baseUrl: managementBaseUrl
      }
      : null
  };
}
