const GROUPS = ["subject", "domain", "form", "theme"];

initTagStudioIndexRag();

async function initTagStudioIndexRag() {
  const list = document.getElementById("tagStudioList");
  if (!list) return;

  const rows = Array.from(list.querySelectorAll(".worksList__item[data-series-id]"));
  if (!rows.length) return;

  try {
    const [assignmentsData, registryData] = await Promise.all([
      fetchJson("/assets/data/tag_assignments.json"),
      fetchJson("/assets/data/tag_registry.json"),
    ]);

    const registry = buildRegistryLookup(registryData);
    const assignmentsSeries = getAssignmentsSeries(assignmentsData);

    for (const row of rows) {
      const seriesId = String(row.getAttribute("data-series-id") || "").trim();
      if (!seriesId) continue;

      const indicator = row.querySelector("[data-rag-indicator]");
      if (!indicator) continue;

      const assignedTags = getSeriesTags(assignmentsSeries, seriesId);
      const metrics = computeMetrics(assignedTags, registry);
      const rag = computeRag(metrics);
      const tooltip = buildTooltip(metrics);
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

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
  return response.json();
}

function buildRegistryLookup(registryData) {
  const tags = Array.isArray(registryData && registryData.tags) ? registryData.tags : [];
  const map = new Map();

  for (const rawTag of tags) {
    if (!rawTag || typeof rawTag !== "object") continue;
    const tagId = normalize(rawTag.tag_id);
    const group = normalize(rawTag.group);
    const status = normalize(rawTag.status || "active");
    if (!tagId || !group) continue;
    map.set(tagId, { group, status });
  }

  return map;
}

function getAssignmentsSeries(assignmentsData) {
  if (assignmentsData && typeof assignmentsData.series === "object" && assignmentsData.series !== null) {
    return assignmentsData.series;
  }
  return {};
}

function getSeriesTags(assignmentsSeries, seriesId) {
  if (assignmentsSeries[seriesId] && Array.isArray(assignmentsSeries[seriesId].tags)) {
    return normalizeSeriesTagIds(assignmentsSeries[seriesId].tags);
  }

  const normalizedSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(assignmentsSeries)) {
    if (normalize(key) !== normalizedSeriesId) continue;
    return Array.isArray(value && value.tags) ? normalizeSeriesTagIds(value.tags) : [];
  }
  return [];
}

function normalizeSeriesTagIds(rawTags) {
  if (!Array.isArray(rawTags)) return [];
  const out = [];
  const seen = new Set();
  for (const raw of rawTags) {
    const tagId = normalizeAssignmentTagId(raw);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push(tagId);
  }
  return out;
}

function normalizeAssignmentTagId(rawTag) {
  if (typeof rawTag === "string") {
    return normalize(rawTag);
  }
  if (rawTag && typeof rawTag === "object") {
    return normalize(rawTag.tag_id);
  }
  return "";
}

function computeMetrics(assignedTags, registry) {
  const counts = {
    subject: 0,
    domain: 0,
    form: 0,
    theme: 0,
  };
  let nUnknown = 0;
  let nDeprecated = 0;
  let nTotal = 0;

  const uniqueTags = Array.from(
    new Set((Array.isArray(assignedTags) ? assignedTags : []).map((tag) => normalize(tag)).filter(Boolean))
  );

  for (const tagId of uniqueTags) {
    nTotal += 1;
    const reg = registry.get(tagId);
    if (!reg) {
      nUnknown += 1;
      continue;
    }

    if (reg.group in counts) counts[reg.group] += 1;
    if (reg.status !== "active") nDeprecated += 1;
  }

  const presentGroups = GROUPS.filter((group) => counts[group] > 0);
  const missingGroups = GROUPS.filter((group) => counts[group] === 0);
  const groupsPresent = presentGroups.length;
  const completenessBase = groupsPresent / 4;
  const tagBonus = (Math.min(nTotal, 6) / 6) * 0.25;
  const completeness = Math.min(1, completenessBase + tagBonus);

  return {
    nTotal,
    nUnknown,
    nDeprecated,
    counts,
    groupsPresent,
    presentGroups,
    missingGroups,
    completeness,
  };
}

function computeRag(metrics) {
  if (metrics.nTotal === 0 || metrics.nUnknown > 0) {
    return "red";
  }

  const missingForm = metrics.counts.form === 0;
  const missingTheme = metrics.counts.theme === 0;
  if (
    metrics.groupsPresent === 1 ||
    metrics.nTotal < 3 ||
    metrics.nDeprecated > 0 ||
    (missingForm && missingTheme)
  ) {
    return "amber";
  }

  return "green";
}

function buildTooltip(metrics) {
  const groupsLabel = metrics.presentGroups.length ? metrics.presentGroups.join(", ") : "none";
  const missingLabel = metrics.missingGroups.length ? metrics.missingGroups.join(", ") : "none";
  return (
    `tags: ${metrics.nTotal}; groups: ${groupsLabel}; missing: ${missingLabel}; ` +
    `unknown: ${metrics.nUnknown}; deprecated: ${metrics.nDeprecated}; ` +
    `completeness: ${metrics.completeness.toFixed(2)}`
  );
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
