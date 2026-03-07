import {
  buildStudioRagTooltip,
  computeStudioRag,
  computeStudioTagMetrics,
  loadStudioConfig
} from "./studio-config.js";
import {
  buildStudioRegistryLookup,
  getSeriesAssignmentTagIds,
  getStudioAssignmentsSeries,
  loadStudioAssignmentsJson,
  loadStudioRegistryJson
} from "./studio-data.js";

initTagStudioIndexRag();

async function initTagStudioIndexRag() {
  const list = document.getElementById("tagStudioList");
  if (!list) return;

  const rows = Array.from(list.querySelectorAll(".worksList__item[data-series-id]"));
  if (!rows.length) return;

  try {
    const config = await loadStudioConfig();
    const [assignmentsData, registryData] = await Promise.all([
      loadStudioAssignmentsJson(config),
      loadStudioRegistryJson(config),
    ]);

    const registry = buildStudioRegistryLookup(registryData);
    const assignmentsSeries = getStudioAssignmentsSeries(assignmentsData);

    for (const row of rows) {
      const seriesId = String(row.getAttribute("data-series-id") || "").trim();
      if (!seriesId) continue;

      const indicator = row.querySelector("[data-rag-indicator]");
      if (!indicator) continue;

      const assignedTags = getSeriesAssignmentTagIds(assignmentsSeries, seriesId);
      const metrics = computeStudioTagMetrics(assignedTags, registry, config);
      const rag = computeStudioRag(metrics, config);
      const tooltip = buildStudioRagTooltip(metrics);
      const label = `status ${rag.toUpperCase()}: ${tooltip}`;

      indicator.classList.remove("rag--red", "rag--amber", "rag--green");
      indicator.classList.add(`rag--${rag}`);
      indicator.setAttribute("title", tooltip);
      indicator.setAttribute("aria-label", label);
    }
  } catch (err) {
    for (const row of rows) {
      const indicator = row.querySelector("[data-rag-indicator]");
      if (!indicator) continue;
      indicator.classList.remove("rag--amber", "rag--green");
      indicator.classList.add("rag--red");
      indicator.setAttribute("title", "Tag status unavailable: failed to load tag data.");
      indicator.setAttribute("aria-label", "status RED: failed to load tag data");
    }
  }
}
