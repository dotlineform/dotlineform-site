import {
  hostedViewAccessAllowed
} from "./docs-viewer-access.js";
import {
  normalizeHostedViewCapabilities
} from "./docs-viewer-hosted-view-capabilities.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function noop() {}

function normalizeAvailability(value) {
  var availability = cleanString(value).toLowerCase();
  if (availability === "disabled" || availability === "unavailable") return availability;
  return "available";
}

function normalizeHostedView(record) {
  var view = record && typeof record === "object" ? record : {};
  var id = cleanString(view.id);
  if (!id) return null;
  return {
    id: id,
    label: cleanString(view.label) || id,
    panel: cleanString(view.panel) || "document",
    access: cleanString(view.access) || "public",
    availability: normalizeAvailability(view.availability),
    module: cleanString(view.module),
    renderer: cleanString(view.renderer),
    placeholderText: cleanString(view.placeholderText || view.placeholder_text),
    capabilities: normalizeHostedViewCapabilities(view.capabilities),
    load: typeof view.load === "function" ? view.load : function () { return Promise.resolve(null); },
    mount: typeof view.mount === "function" ? view.mount : noop,
    update: typeof view.update === "function" ? view.update : noop,
    unmount: typeof view.unmount === "function" ? view.unmount : noop,
    dispose: typeof view.dispose === "function" ? view.dispose : noop
  };
}

function hostedViewIdSet(records) {
  var ids = new Set();
  (records || []).forEach(function (record) {
    var id = cleanString(record && record.id);
    if (id) ids.add(id);
  });
  return ids;
}

function routeHostedViewRecord(record) {
  var view = record && typeof record === "object" ? record : {};
  var id = cleanString(view.id);
  if (!id) return null;
  return Object.assign({}, view, {
    id: id,
    module: ""
  });
}

export function createDocsViewerHostedViewRegistry(options) {
  var settings = options || {};
  var accessProjection = settings.accessProjection || {};
  var views = new Map();

  function statusFor(view) {
    if (!view) {
      return { available: false, reason: "missing" };
    }
    if (view.availability !== "available") {
      return { available: false, reason: view.availability };
    }
    if (!hostedViewAccessAllowed(accessProjection, view.access)) {
      return { available: false, reason: "access" };
    }
    return { available: true, reason: "" };
  }

  function register(record) {
    var view = normalizeHostedView(record);
    if (!view) return null;
    views.set(view.id, view);
    return view;
  }

  function resolve(id) {
    var view = views.get(cleanString(id)) || null;
    var status = statusFor(view);
    return {
      id: cleanString(id),
      view: status.available ? view : null,
      registered: Boolean(view),
      available: status.available,
      reason: status.reason
    };
  }

  function list() {
    return Array.from(views.values()).map(function (view) {
      var status = statusFor(view);
      return Object.assign({}, view, {
        available: status.available,
        unavailableReason: status.reason
      });
    });
  }

  function listByPanel(panel) {
    var targetPanel = cleanString(panel);
    return list().filter(function (view) {
      return view.panel === targetPanel;
    });
  }

  return {
    get: function (id) { return views.get(cleanString(id)) || null; },
    list: list,
    listByPanel: listByPanel,
    register: register,
    resolve: resolve
  };
}

export function listDocsViewerHostedViewsForPanel(registry, panel) {
  if (!registry) return [];
  if (typeof registry.listByPanel === "function") return registry.listByPanel(panel);
  if (typeof registry.list === "function") {
    var targetPanel = cleanString(panel);
    return registry.list().filter(function (view) {
      return view.panel === targetPanel;
    });
  }
  return [];
}

export function createDocsViewerBuiltInHostedViews() {
  return [
    {
      id: "index-tree",
      label: "Index tree",
      panel: "index",
      access: "public",
      availability: "available",
      renderer: "index-tree",
      capabilities: {
        layoutStates: ["normal", "collapsed"],
        toolbar: false
      }
    },
    {
      id: "rendered-document",
      label: "Document",
      panel: "main",
      access: "public",
      availability: "available"
    },
    {
      id: "search-results",
      feature: "search",
      label: "Search results",
      panel: "main",
      access: "public",
      availability: "available"
    },
    {
      id: "recent-results",
      feature: "recently-added",
      label: "Recently added",
      panel: "main",
      access: "public",
      availability: "available"
    },
    {
      id: "metadata-info",
      label: "Metadata info",
      panel: "info",
      access: "public",
      availability: "available",
      load: function () {
        return import("./docs-viewer-metadata-info-view.js")
          .then(function (module) {
            return module.createDocsViewerMetadataInfoView();
          });
      }
    }
  ];
}

export function createDocsViewerDefaultHostedViews() {
  return createDocsViewerBuiltInHostedViews();
}

export function createDocsViewerRouteHostedViews(records, options) {
  var settings = options || {};
  var reservedIds = hostedViewIdSet(settings.reservedRecords || createDocsViewerDefaultHostedViews());
  return (records || []).map(routeHostedViewRecord).filter(function (record) {
    return record && !reservedIds.has(record.id);
  });
}

export function registerDocsViewerHostedViews(registry, records) {
  var target = registry || createDocsViewerHostedViewRegistry();
  (records || []).forEach(function (record) {
    target.register(record);
  });
  return target;
}
