const GROUPS = ["subject", "domain", "form", "theme"];

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagsPage);
} else {
  initSeriesTagsPage();
}

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;

  const seriesData = parseSeriesData();
  if (!seriesData.length) {
    mount.innerHTML = `<p class="tagStudio__empty">none</p>`;
    return;
  }

  try {
    const [assignmentsJson, registryJson] = await Promise.all([
      fetchJson("/assets/data/tag_assignments.json"),
      fetchJson("/assets/data/tag_registry.json")
    ]);

    const assignmentsSeries = assignmentsJson && typeof assignmentsJson.series === "object"
      ? assignmentsJson.series
      : {};
    const registry = buildRegistryLookup(registryJson);
    const state = {
      mount,
      seriesData,
      assignmentsSeries,
      registry,
      groupDescriptions: new Map(),
      groupDescriptionLongs: new Map(),
      groupInfoOpen: false,
      filterGroup: "all"
    };
    try {
      const groupsJson = await fetchJson("/assets/data/tag_groups.json");
      state.groupDescriptions = buildGroupDescriptionMap(groupsJson);
      state.groupDescriptionLongs = buildGroupDescriptionLongMap(groupsJson);
    } catch (error) {
      state.groupDescriptions = new Map();
      state.groupDescriptionLongs = new Map();
    }
    renderTable(state);
    mount.addEventListener("click", (event) => {
      const infoToggle = event.target.closest("button[data-action='toggle-group-info']");
      if (infoToggle) {
        state.groupInfoOpen = !state.groupInfoOpen;
        renderTable(state);
        return;
      }

      const clickedInsideInfo = Boolean(event.target.closest('[data-role="group-info-wrap"]'));
      let closedInfo = false;
      if (!clickedInsideInfo && state.groupInfoOpen) {
        state.groupInfoOpen = false;
        closedInfo = true;
      }

      const button = event.target.closest("button[data-group]");
      if (!button) {
        if (closedInfo) renderTable(state);
        return;
      }
      const next = normalize(button.getAttribute("data-group"));
      state.filterGroup = GROUPS.includes(next) ? next : "all";
      renderTable(state);
    });

    document.addEventListener("click", (event) => {
      if (event.target.closest('[data-role="group-info-wrap"]')) return;
      closeOpenGroupInfo(state);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      closeOpenGroupInfo(state);
    });
  } catch (error) {
    mount.innerHTML = `<div class="tagStudioError">Failed to load series tag data.</div>`;
  }
}

function closeOpenGroupInfo(state) {
  if (!state.groupInfoOpen) return;
  state.groupInfoOpen = false;
  renderTable(state);
}

function parseSeriesData() {
  const node = document.getElementById("series-tags-series-data");
  if (!node) return [];
  try {
    const parsed = JSON.parse(node.textContent || "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((entry) => ({
        seriesId: normalize(entry && entry.series_id),
        title: String((entry && entry.title) || "").trim(),
        url: String((entry && entry.url) || "").trim()
      }))
      .filter((entry) => entry.seriesId && entry.title)
      .sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: "base" }));
  } catch (error) {
    return [];
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function buildRegistryLookup(registryJson) {
  const lookup = new Map();
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  for (const raw of tags) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    const group = normalize(raw.group);
    const label = String(raw.label || "").trim();
    if (!tagId || !label) continue;
    lookup.set(tagId, { group, label });
  }
  return lookup;
}

function buildGroupDescriptionMap(groupsJson) {
  const out = new Map();
  const groups = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  for (const raw of groups) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!GROUPS.includes(groupId) || !description) continue;
    out.set(groupId, description);
  }
  return out;
}

function buildGroupDescriptionLongMap(groupsJson) {
  const out = new Map();
  const groups = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  for (const raw of groups) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    const descriptionLong = String(raw.description_long || "").trim();
    if (!GROUPS.includes(groupId) || !descriptionLong) continue;
    out.set(groupId, descriptionLong);
  }
  return out;
}

function renderTable(state) {
  const rowsHtml = state.seriesData.map((series) => {
    const assigned = getSeriesTags(state.assignmentsSeries, series.seriesId);
    const tags = assigned
      .map((tagId) => toTagDisplay(tagId, state.registry))
      .sort((a, b) => a.sortLabel.localeCompare(b.sortLabel, undefined, { sensitivity: "base" }));
    const visibleTags = state.filterGroup === "all"
      ? tags
      : tags.filter((tag) => tag.group === state.filterGroup);

    const chips = visibleTags.length
      ? visibleTags.map((tag) => (
        `<li class="tagStudio__chip ${escapeHtml(tag.className)}" title="${escapeHtml(tag.tagId)}">${escapeHtml(tag.label)}</li>`
      )).join("")
      : `<li class="tagStudio__empty">none</li>`;

    return `
      <li class="seriesTags__row">
        <div class="seriesTags__col seriesTags__col--title">
          <a href="${escapeHtml(series.url)}">${escapeHtml(series.title)}</a>
        </div>
        <div class="seriesTags__col seriesTags__col--count">${assigned.length}</div>
        <div class="seriesTags__col seriesTags__col--tags">
          <ul class="seriesTags__chipList">${chips}</ul>
        </div>
      </li>
    `;
  }).join("");

  state.mount.innerHTML = `
    <div class="seriesTags">
      <div class="seriesTags__head">
        <div class="seriesTags__col seriesTags__col--title">series</div>
        <div class="seriesTags__col seriesTags__col--count">count</div>
        <div class="seriesTags__col seriesTags__col--tags">
          ${renderFilters(state)}
        </div>
      </div>
      <ul class="seriesTags__rows">${rowsHtml}</ul>
    </div>
  `;
}

function renderFilters(state) {
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const titleAttr = groupTitleAttr(state.groupDescriptions, group);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");

  return `
    <div class="tagStudio__key seriesTags__filters">
      <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags</button>
      ${groupButtons}
      ${renderGroupInfoControl(state)}
    </div>
  `;
}

function groupTitleAttr(groupDescriptions, group) {
  const description = String(groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state) {
  return `
    <span class="tagStudio__keyInfoWrap" data-role="group-info-wrap" data-scope="series">
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__keyInfoBtn"
        data-action="toggle-group-info"
        data-scope="series"
        aria-expanded="${state.groupInfoOpen ? "true" : "false"}"
        title="Group descriptions"
      >
        <em>i</em>
      </button>
      ${state.groupInfoOpen ? `
        <div class="tagStudio__keyInfoPopup" data-role="group-info-popup">
          ${renderGroupInfoSections(state)}
        </div>
      ` : ""}
    </span>
  `;
}

function renderGroupInfoSections(state) {
  const sections = GROUPS.map((group) => {
    const descriptionLong = String(state.groupDescriptionLongs.get(group) || "").trim();
    if (!descriptionLong) return "";
    const titleAttr = groupTitleAttr(state.groupDescriptions, group);
    return `
      <section class="tagStudio__groupInfoSection">
        <p class="tagStudio__groupInfoHead">
          <span class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)}" ${titleAttr}>${escapeHtml(group)}</span>
        </p>
        <p class="tagStudio__groupInfoText">${escapeHtml(descriptionLong)}</p>
      </section>
    `;
  }).filter(Boolean).join("");
  return sections || '<p class="tagStudio__empty">No group descriptions available.</p>';
}

function getSeriesTags(assignmentsSeries, seriesId) {
  const row = assignmentsSeries && assignmentsSeries[seriesId];
  if (!row || !Array.isArray(row.tags)) return [];
  return row.tags
    .map((value) => String(value || "").trim())
    .filter(Boolean);
}

function toTagDisplay(rawTagId, registry) {
  const tagId = normalize(rawTagId);
  const known = registry.get(tagId);
  if (known) {
    const className = GROUPS.includes(known.group)
      ? `tagStudio__chip--${known.group}`
      : "tagStudio__chip--warning";
    return {
      tagId,
      group: known.group,
      label: known.label,
      sortLabel: known.label,
      className
    };
  }

  const groupPrefix = groupFromTagId(tagId);
  const className = GROUPS.includes(groupPrefix)
    ? `tagStudio__chip--${groupPrefix}`
    : "tagStudio__chip--warning";
  return {
    tagId,
    group: groupPrefix,
    label: tagId,
    sortLabel: tagId,
    className
  };
}

function groupFromTagId(tagId) {
  const idx = tagId.indexOf(":");
  if (idx < 0) return "";
  return tagId.slice(0, idx);
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
