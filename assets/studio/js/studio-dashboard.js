import { loadStudioConfig } from "./studio-config.js";
import { loadStudioLookupJson } from "./studio-data.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  probeCatalogueReadHealth
} from "./studio-transport.js";

function dashboardRouteDetail(root) {
  return {
    route: root && root.dataset.studioDashboardRoute ? root.dataset.studioDashboardRoute : "studio-dashboard",
    mode: "dashboard",
    recordLoaded: Boolean(root && root.querySelector("[data-studio-metric]"))
  };
}

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function setMetric(name, value) {
  document.querySelectorAll(`[data-studio-metric="${name}"]`).forEach((node) => {
    node.textContent = value;
  });
}

function formatNumber(value) {
  if (!Number.isFinite(value)) return "--";
  return value.toLocaleString("en-GB");
}

async function initStudioDashboard() {
  const root = document.querySelector("[data-studio-dashboard-route]");
  if (root) {
    initializeStudioRouteState(root, dashboardRouteDetail(root));
    setStudioRouteBusy(root, true, dashboardRouteDetail(root));
  }
  const metricNodes = document.querySelectorAll("[data-studio-metric]");
  if (!metricNodes.length) {
    if (root) {
      setStudioRouteBusy(root, false, dashboardRouteDetail(root));
      setStudioRouteReady(root, true, dashboardRouteDetail(root));
    }
    return;
  }
  const [config, catalogueServerAvailable] = await Promise.all([
    loadStudioConfig().catch(() => null),
    probeCatalogueReadHealth().catch(() => false)
  ]);
  const catalogueReadOptions = { cache: "no-store", catalogueServerAvailable };

  const tasks = [
    loadJson("/assets/data/works_index.json").then((payload) => {
      setMetric("works-count", formatNumber(Number(payload?.header?.count || 0)));
    }),
    loadJson("/assets/data/series_index.json").then((payload) => {
      setMetric("series-count", formatNumber(Number(payload?.header?.count || 0)));
    }),
    (catalogueServerAvailable && config ? loadStudioLookupJson(config, "catalogue_work_details", catalogueReadOptions) : Promise.resolve(null)).then((payload) => {
      const count = Number(payload?.header?.count || 0) || Object.keys(payload?.work_details || {}).length;
      if (payload) setMetric("work-details-count", formatNumber(count));
    }),
    (catalogueServerAvailable && config ? loadStudioLookupJson(config, "catalogue_moments", catalogueReadOptions) : Promise.resolve(null)).then((payload) => {
      const count = Number(payload?.header?.count || 0) || Object.keys(payload?.moments || {}).length;
      if (payload) setMetric("moments-count", formatNumber(count));
    }),
    loadJson("/studio/data/canonical/analytics/tag-registry.json").then((payload) => {
      const tags = Array.isArray(payload?.tags) ? payload.tags.length : 0;
      const groups = Array.isArray(payload?.policy?.allowed_groups) ? payload.policy.allowed_groups.length : 0;
      setMetric("tag-count", formatNumber(tags));
      setMetric("tag-group-count", formatNumber(groups));
    })
  ];

  await Promise.allSettled(tasks);
  if (root) {
    setStudioRouteBusy(root, false, dashboardRouteDetail(root));
    setStudioRouteReady(root, true, dashboardRouteDetail(root));
  }
}

initStudioDashboard();
