import { loadStudioConfig } from "./studio-config.js";
import { loadStudioLookupJson } from "./studio-data.js";
import { probeCatalogueHealth } from "./studio-transport.js";

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
  const metricNodes = document.querySelectorAll("[data-studio-metric]");
  if (!metricNodes.length) return;
  const [config, catalogueServerAvailable] = await Promise.all([
    loadStudioConfig().catch(() => null),
    probeCatalogueHealth()
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
    loadJson("/assets/data/docs/scopes/library/index.json").then((payload) => {
      const count = Array.isArray(payload?.docs) ? payload.docs.length : 0;
      setMetric("library-doc-count", formatNumber(count));
    }),
    loadJson("/assets/studio/data/tag_registry.json").then((payload) => {
      const tags = Array.isArray(payload?.tags) ? payload.tags.length : 0;
      const groups = Array.isArray(payload?.policy?.allowed_groups) ? payload.policy.allowed_groups.length : 0;
      setMetric("tag-count", formatNumber(tags));
      setMetric("tag-group-count", formatNumber(groups));
    }),
    loadJson("/assets/data/search/catalogue/index.json").then((payload) => {
      setMetric("catalogue-search-count", formatNumber(Number(payload?.header?.count || 0)));
    }),
    loadJson("/assets/data/search/library/index.json").then((payload) => {
      setMetric("library-search-count", formatNumber(Number(payload?.header?.count || 0)));
    }),
    loadJson("/assets/data/search/studio/index.json").then((payload) => {
      setMetric("studio-search-count", formatNumber(Number(payload?.header?.count || 0)));
    })
  ];

  await Promise.allSettled(tasks);
}

initStudioDashboard();
