const GROUPS = ["subject", "domain", "form", "theme"];
const GROUP_INDEX = new Map(GROUPS.map((group, index) => [group, index]));

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagStudio);
} else {
  initTagStudio();
}

async function initTagStudio() {
  const mount = document.getElementById("tag-studio");
  if (!mount) return;

  const seriesId = String(mount.dataset.seriesId || "").trim();
  if (!seriesId) {
    renderFatalError(mount, "Tag Studio error: missing series id.");
    return;
  }

  try {
    const [registryJson, aliasesJson, assignmentsJson] = await Promise.all([
      fetchJson("/assets/data/tag_registry_v1.json"),
      fetchJson("/assets/data/tag_aliases_v1.json"),
      fetchJson("/assets/data/tag_assignments_v1.json")
    ]);

    const state = buildState(mount, seriesId, registryJson, aliasesJson, assignmentsJson);
    renderShell(state);
    wireEvents(state);
    renderAll(state);
  } catch (error) {
    renderFatalError(
      mount,
      "Failed to load tag data. Check /assets/data/tag_registry_v1.json, /assets/data/tag_aliases_v1.json, and /assets/data/tag_assignments_v1.json."
    );
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${url}`);
  }
  return response.json();
}

function buildState(mount, seriesId, registryJson, aliasesJson, assignmentsJson) {
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const tagsById = new Map();
  const slugMap = new Map();
  const labelMap = new Map();
  const activeTags = [];
  const activeByGroup = new Map(GROUPS.map((group) => [group, []]));

  for (const rawTag of tags) {
    const tag = sanitizeTag(rawTag);
    if (!tag) continue;

    tagsById.set(tag.tag_id, tag);
    pushMapList(slugMap, tag.slug, tag);
    pushMapList(labelMap, normalize(tag.label), tag);

    if (tag.status === "active") {
      activeTags.push(tag);
      if (activeByGroup.has(tag.group)) {
        activeByGroup.get(tag.group).push(tag);
      }
    }
  }

  activeTags.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
  for (const group of GROUPS) {
    activeByGroup.get(group).sort((a, b) => a.tag_id.localeCompare(b.tag_id));
  }

  const aliases = new Map();
  const rawAliases = aliasesJson && typeof aliasesJson.aliases === "object" ? aliasesJson.aliases : {};
  for (const [aliasInput, targetInput] of Object.entries(rawAliases)) {
    const aliasKey = normalize(aliasInput);
    const targetTagId = normalize(targetInput);
    if (!aliasKey) continue;
    aliases.set(aliasKey, targetTagId);
  }

  const entries = [];
  let nextEntryId = 1;
  const seriesAssignments = assignmentsJson && typeof assignmentsJson.series === "object" ? assignmentsJson.series : {};
  const existingAssignment = getSeriesAssignment(seriesAssignments, seriesId);
  const existingTags = Array.isArray(existingAssignment && existingAssignment.tags) ? existingAssignment.tags : [];

  for (const input of existingTags) {
    const resolved = resolveInput(input, { tagsById, slugMap, labelMap, aliases });
    if (resolved.type === "resolved") {
      entries.push(makeResolvedEntry(nextEntryId++, String(input), resolved.tag));
    } else if (String(input || "").trim()) {
      entries.push(makeUnresolvedEntry(nextEntryId++, String(input)));
    }
  }

  return {
    mount,
    seriesId,
    tagsById,
    slugMap,
    labelMap,
    aliases,
    activeTags,
    activeByGroup,
    entries,
    nextEntryId,
    statusText: "",
    statusKind: "",
    pendingChooserRaw: "",
    refs: null,
    modalSnippet: ""
  };
}

function sanitizeTag(rawTag) {
  if (!rawTag || typeof rawTag !== "object") return null;

  const tagId = normalize(rawTag.tag_id);
  const group = normalize(rawTag.group);
  const label = String(rawTag.label || "").trim();
  const status = normalize(rawTag.status || "active");

  if (!tagId || !group || !label) return null;
  if (!GROUP_INDEX.has(group)) return null;

  const splitIndex = tagId.indexOf(":");
  const slug = splitIndex >= 0 ? tagId.slice(splitIndex + 1) : tagId;

  return {
    tag_id: tagId,
    group,
    label,
    status,
    slug
  };
}

function pushMapList(map, key, value) {
  if (!key) return;
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}

function getSeriesAssignment(seriesAssignments, seriesId) {
  if (seriesAssignments[seriesId]) return seriesAssignments[seriesId];

  const lowerSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(seriesAssignments)) {
    if (normalize(key) === lowerSeriesId) return value;
  }
  return null;
}

function renderShell(state) {
  state.mount.innerHTML = `
    <div class="tagStudio">
      <section class="tagStudio__panel">
        <label class="tagStudio__label" for="tagStudioInput">Add Tag</label>
        <div class="tagStudio__inputRow">
          <input id="tagStudioInput" class="tagStudio__input" type="text" autocomplete="off" placeholder="form:radial or radial">
          <button type="button" class="tagStudio__button" data-role="add-tag">Add</button>
        </div>
        <ul class="tagStudio__autocomplete" data-role="autocomplete" hidden></ul>
        <div class="tagStudio__chooser" data-role="chooser" hidden></div>
        <p class="tagStudio__status" data-role="status"></p>
      </section>

      <div class="tagStudio__grid">
        <section class="tagStudio__panel">
          <h3 class="tagStudio__heading">Current Tags</h3>
          <div data-role="groups"></div>
        </section>

        <section class="tagStudio__panel">
          <h3 class="tagStudio__heading">Metrics</h3>
          <div data-role="metrics"></div>
        </section>

        <section class="tagStudio__panel">
          <h3 class="tagStudio__heading">Suggestions</h3>
          <div data-role="suggestions"></div>
        </section>
      </div>

      <div class="tagStudio__actions">
        <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save">Save Tags</button>
        <span class="tagStudio__saveWarning" data-role="save-warning"></span>
      </div>
    </div>

    <div class="tagStudioModal" data-role="modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagStudioModalTitle">
        <h3 id="tagStudioModalTitle">Tag Patch Preview</h3>
        <p class="tagStudioModal__label">Canonical resolved tags</p>
        <pre class="tagStudioModal__pre" data-role="modal-tags"></pre>
        <p class="tagStudioModal__label">Patch snippet for <code>tag_assignments_v1.json</code></p>
        <pre class="tagStudioModal__pre" data-role="modal-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-snippet">Copy</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">Close</button>
        </div>
      </div>
    </div>
  `;

  state.refs = {
    input: state.mount.querySelector("#tagStudioInput"),
    addButton: state.mount.querySelector('[data-role="add-tag"]'),
    autocomplete: state.mount.querySelector('[data-role="autocomplete"]'),
    chooser: state.mount.querySelector('[data-role="chooser"]'),
    status: state.mount.querySelector('[data-role="status"]'),
    groups: state.mount.querySelector('[data-role="groups"]'),
    metrics: state.mount.querySelector('[data-role="metrics"]'),
    suggestions: state.mount.querySelector('[data-role="suggestions"]'),
    saveButton: state.mount.querySelector('[data-role="save"]'),
    saveWarning: state.mount.querySelector('[data-role="save-warning"]'),
    modal: state.mount.querySelector('[data-role="modal"]'),
    modalTags: state.mount.querySelector('[data-role="modal-tags"]'),
    modalSnippet: state.mount.querySelector('[data-role="modal-snippet"]'),
    copyButton: state.mount.querySelector('[data-role="copy-snippet"]')
  };
}

function wireEvents(state) {
  state.refs.input.addEventListener("input", () => {
    renderAutocomplete(state);
    hideChooser(state);
  });

  state.refs.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addFromInput(state);
    } else if (event.key === "Escape") {
      hideAutocomplete(state);
      hideChooser(state);
    }
  });

  state.refs.addButton.addEventListener("click", () => {
    addFromInput(state);
  });

  state.refs.autocomplete.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-tag-id]");
    if (!button) return;

    const tagId = normalize(button.getAttribute("data-tag-id"));
    const tag = state.tagsById.get(tagId);
    if (!tag) return;

    addResolvedTag(state, tag, tag.tag_id);
    state.refs.input.value = "";
    hideAutocomplete(state);
    hideChooser(state);
    renderAll(state);
  });

  state.refs.chooser.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-tag-id]");
    if (!button) return;

    const tagId = normalize(button.getAttribute("data-tag-id"));
    const tag = state.tagsById.get(tagId);
    if (!tag) return;

    addResolvedTag(state, tag, state.pendingChooserRaw || tag.tag_id);
    state.pendingChooserRaw = "";
    state.refs.input.value = "";
    hideAutocomplete(state);
    hideChooser(state);
    renderAll(state);
  });

  state.refs.groups.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-remove-entry-id]");
    if (!button) return;

    const entryId = Number(button.getAttribute("data-remove-entry-id"));
    removeEntry(state, entryId);
    renderAll(state);
  });

  state.refs.suggestions.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-tag-id]");
    if (!button) return;

    const tagId = normalize(button.getAttribute("data-tag-id"));
    const tag = state.tagsById.get(tagId);
    if (!tag) return;

    addResolvedTag(state, tag, tag.tag_id);
    renderAll(state);
  });

  state.refs.saveButton.addEventListener("click", () => {
    openSaveModal(state);
  });

  state.refs.modal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-modal"]')) return;
    closeModal(state);
  });

  state.refs.copyButton.addEventListener("click", async () => {
    if (!state.modalSnippet) return;
    try {
      await navigator.clipboard.writeText(state.modalSnippet);
      setStatus(state, "success", "Patch snippet copied to clipboard.");
    } catch (error) {
      setStatus(state, "error", "Copy failed. Select and copy the snippet manually.");
    }
    renderStatus(state);
  });
}

function addFromInput(state) {
  const rawInput = String(state.refs.input.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", "Enter a tag id or shorthand.");
    renderStatus(state);
    return;
  }

  const resolved = resolveInput(rawInput, state);
  if (resolved.type === "resolved") {
    addResolvedTag(state, resolved.tag, rawInput);
    state.refs.input.value = "";
    hideAutocomplete(state);
    hideChooser(state);
    renderAll(state);
    return;
  }

  if (resolved.type === "ambiguous") {
    renderChooser(state, rawInput, resolved.candidates);
    setStatus(state, "warn", "Multiple matches found. Choose one.");
    renderStatus(state);
    return;
  }

  if (resolved.type === "unresolved") {
    addUnresolvedTag(state, rawInput);
    state.refs.input.value = "";
    hideAutocomplete(state);
    hideChooser(state);
    setStatus(state, "error", `Unknown tag: "${rawInput}".`);
    renderAll(state);
  }
}

function resolveInput(rawInput, state) {
  const raw = String(rawInput || "").trim();
  if (!raw) return { type: "empty" };

  const normalized = normalize(raw);
  if (normalized.includes(":")) {
    const canonical = state.tagsById.get(normalized);
    if (canonical) return { type: "resolved", tag: canonical };
    return { type: "unresolved" };
  }

  const aliasTagId = state.aliases.get(normalized);
  if (aliasTagId) {
    const aliasTag = state.tagsById.get(aliasTagId);
    if (aliasTag) return { type: "resolved", tag: aliasTag };
  }

  const candidates = [];
  const seen = new Set();

  for (const list of [state.slugMap.get(normalized), state.labelMap.get(normalized)]) {
    if (!Array.isArray(list)) continue;
    for (const tag of list) {
      if (!tag || !tag.tag_id || seen.has(tag.tag_id)) continue;
      seen.add(tag.tag_id);
      candidates.push(tag);
    }
  }

  if (candidates.length === 1) return { type: "resolved", tag: candidates[0] };
  if (candidates.length > 1) {
    candidates.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
    return { type: "ambiguous", candidates };
  }
  return { type: "unresolved" };
}

function addResolvedTag(state, tag, rawInput) {
  if (!tag || !tag.tag_id) return;

  const tagId = normalize(tag.tag_id);
  const alreadyExists = state.entries.some((entry) => entry.type === "resolved" && entry.canonicalId === tagId);
  if (alreadyExists) {
    setStatus(state, "warn", `Already added: ${tagId}.`);
    return;
  }

  state.entries.push(makeResolvedEntry(state.nextEntryId++, rawInput, tag));
  setStatus(state, "success", `Added ${tagId}.`);
}

function addUnresolvedTag(state, rawInput) {
  const normalizedRaw = normalize(rawInput);
  const alreadyExists = state.entries.some(
    (entry) => entry.type === "unresolved" && normalize(entry.rawInput) === normalizedRaw
  );
  if (alreadyExists) {
    setStatus(state, "warn", `Unknown tag already listed: "${rawInput}".`);
    return;
  }

  state.entries.push(makeUnresolvedEntry(state.nextEntryId++, rawInput));
}

function removeEntry(state, entryId) {
  const sizeBefore = state.entries.length;
  state.entries = state.entries.filter((entry) => entry.entryId !== entryId);
  if (state.entries.length < sizeBefore) {
    setStatus(state, "success", "Tag removed.");
  }
}

function makeResolvedEntry(entryId, rawInput, tag) {
  return {
    entryId,
    type: "resolved",
    rawInput: String(rawInput || "").trim(),
    canonicalId: normalize(tag.tag_id),
    group: normalize(tag.group),
    label: String(tag.label || tag.tag_id).trim()
  };
}

function makeUnresolvedEntry(entryId, rawInput) {
  return {
    entryId,
    type: "unresolved",
    rawInput: String(rawInput || "").trim()
  };
}

function renderAll(state) {
  renderStatus(state);
  renderAutocomplete(state);
  renderGroups(state);
  renderMetrics(state);
  renderSuggestions(state);
  renderSaveState(state);
}

function renderAutocomplete(state) {
  const query = normalize(state.refs.input.value);
  if (!query) {
    hideAutocomplete(state);
    return;
  }

  const matches = state.activeTags
    .filter((tag) => {
      return (
        tag.tag_id.includes(query) ||
        tag.slug.includes(query) ||
        normalize(tag.label).includes(query)
      );
    })
    .slice(0, 10);

  if (!matches.length) {
    hideAutocomplete(state);
    return;
  }

  state.refs.autocomplete.innerHTML = matches
    .map((tag) => {
      const exists = state.entries.some((entry) => entry.type === "resolved" && entry.canonicalId === tag.tag_id);
      return `
        <li>
          <button type="button" class="tagStudio__suggestionBtn" data-tag-id="${escapeHtml(tag.tag_id)}"${exists ? " disabled" : ""}>
            <span>${escapeHtml(tag.tag_id)}</span>
            <small>${escapeHtml(tag.label)}</small>
          </button>
        </li>
      `;
    })
    .join("");
  state.refs.autocomplete.hidden = false;
}

function hideAutocomplete(state) {
  state.refs.autocomplete.hidden = true;
  state.refs.autocomplete.innerHTML = "";
}

function renderChooser(state, rawInput, candidates) {
  state.pendingChooserRaw = String(rawInput || "").trim();
  state.refs.chooser.innerHTML = `
    <p class="tagStudio__chooserTitle">Choose canonical tag for "${escapeHtml(state.pendingChooserRaw)}"</p>
    <ul class="tagStudio__chooserList">
      ${candidates
        .map((tag) => {
          return `
            <li>
              <button type="button" class="tagStudio__chooserBtn" data-tag-id="${escapeHtml(tag.tag_id)}">
                ${escapeHtml(tag.tag_id)} <small>${escapeHtml(tag.label)}</small>
              </button>
            </li>
          `;
        })
        .join("")}
    </ul>
  `;
  state.refs.chooser.hidden = false;
}

function hideChooser(state) {
  state.pendingChooserRaw = "";
  state.refs.chooser.hidden = true;
  state.refs.chooser.innerHTML = "";
}

function renderGroups(state) {
  const grouped = new Map(GROUPS.map((group) => [group, []]));
  const unresolved = [];

  for (const entry of state.entries) {
    if (entry.type === "resolved" && grouped.has(entry.group)) {
      grouped.get(entry.group).push(entry);
    } else if (entry.type === "unresolved") {
      unresolved.push(entry);
    }
  }

  state.refs.groups.innerHTML = GROUPS
    .map((group) => {
      const entries = grouped.get(group);
      const chips = entries.length
        ? entries
            .map((entry) => {
              return `
                <li class="tagStudio__chip tagStudio__chip--${escapeHtml(group)}">
                  <span class="tagStudio__chipTag">${escapeHtml(entry.canonicalId)}</span>
                  <small class="tagStudio__chipLabel">${escapeHtml(entry.label)}</small>
                  <button type="button" class="tagStudio__chipRemove" data-remove-entry-id="${entry.entryId}" aria-label="Remove ${escapeHtml(entry.canonicalId)}">x</button>
                </li>
              `;
            })
            .join("")
        : '<li class="tagStudio__empty">none</li>';

      return `
        <section class="tagStudio__group">
          <h4 class="tagStudio__groupTitle">${escapeHtml(group)}</h4>
          <ul class="tagStudio__chipList">${chips}</ul>
        </section>
      `;
    })
    .join("");

  if (unresolved.length) {
    state.refs.groups.insertAdjacentHTML(
      "beforeend",
      `
        <section class="tagStudio__group">
          <h4 class="tagStudio__groupTitle">unknown inputs</h4>
          <ul class="tagStudio__chipList">
            ${unresolved
              .map((entry) => {
                return `
                  <li class="tagStudio__chip tagStudio__chip--warning">
                    <span class="tagStudio__chipTag">${escapeHtml(entry.rawInput)}</span>
                    <button type="button" class="tagStudio__chipRemove" data-remove-entry-id="${entry.entryId}" aria-label="Remove ${escapeHtml(entry.rawInput)}">x</button>
                  </li>
                `;
              })
              .join("")}
          </ul>
        </section>
      `
    );
  }
}

function renderMetrics(state) {
  const metrics = computeMetrics(state);
  const collisionText = metrics.collisions.length
    ? metrics.collisions.map((entry) => `${entry.tagId} (${entry.count})`).join(", ")
    : "none";

  state.refs.metrics.innerHTML = `
    <dl class="tagStudio__metrics">
      ${GROUPS.map((group) => `<div><dt>${escapeHtml(group)}</dt><dd>${metrics.groupCounts[group]}</dd></div>`).join("")}
      <div><dt>collisions</dt><dd>${metrics.collisions.length}</dd></div>
      <div><dt>unresolved</dt><dd>${metrics.unresolvedCount}</dd></div>
    </dl>
    <p class="tagStudio__metricDetail"><strong>collision ids:</strong> ${escapeHtml(collisionText)}</p>
  `;
}

function renderSuggestions(state) {
  const metrics = computeMetrics(state);
  const missingGroups = GROUPS.filter((group) => metrics.groupCounts[group] === 0);

  if (!missingGroups.length) {
    state.refs.suggestions.innerHTML = `<p class="tagStudio__empty">All groups have at least one tag.</p>`;
    return;
  }

  state.refs.suggestions.innerHTML = missingGroups
    .map((group) => {
      const examples = (state.activeByGroup.get(group) || []).slice(0, 3);
      const buttons = examples.length
        ? examples
            .map((tag) => {
              return `<button type="button" class="tagStudio__exampleBtn" data-tag-id="${escapeHtml(tag.tag_id)}">${escapeHtml(tag.tag_id)}</button>`;
            })
            .join("")
        : '<span class="tagStudio__empty">no active examples</span>';

      return `
        <div class="tagStudio__suggestionGroup">
          <h4 class="tagStudio__groupTitle">${escapeHtml(group)}</h4>
          <div class="tagStudio__exampleRow">${buttons}</div>
        </div>
      `;
    })
    .join("");
}

function renderSaveState(state) {
  const metrics = computeMetrics(state);
  const hasUnresolved = metrics.unresolvedCount > 0;
  state.refs.saveButton.disabled = hasUnresolved;
  state.refs.saveWarning.textContent = hasUnresolved ? "Resolve unknown tags before saving." : "";
}

function computeMetrics(state) {
  const groupCounts = Object.fromEntries(GROUPS.map((group) => [group, 0]));
  const canonicalCounts = new Map();
  let unresolvedCount = 0;

  for (const entry of state.entries) {
    if (entry.type === "resolved") {
      if (groupCounts[entry.group] !== undefined) groupCounts[entry.group] += 1;
      canonicalCounts.set(entry.canonicalId, (canonicalCounts.get(entry.canonicalId) || 0) + 1);
    } else if (entry.type === "unresolved") {
      unresolvedCount += 1;
    }
  }

  const collisions = [];
  for (const [tagId, count] of canonicalCounts.entries()) {
    if (count > 1) collisions.push({ tagId, count });
  }
  collisions.sort((a, b) => a.tagId.localeCompare(b.tagId));

  return { groupCounts, collisions, unresolvedCount };
}

function openSaveModal(state) {
  const metrics = computeMetrics(state);
  if (metrics.unresolvedCount > 0) {
    setStatus(state, "error", "Resolve unknown tags before saving.");
    renderStatus(state);
    return;
  }

  const canonicalTags = getCanonicalTags(state);
  const timestamp = utcTimestamp();
  const snippet = buildPatchSnippet(state.seriesId, canonicalTags, timestamp);
  state.modalSnippet = snippet;

  state.refs.modalTags.textContent = JSON.stringify(canonicalTags, null, 2);
  state.refs.modalSnippet.textContent = snippet;
  state.refs.modal.hidden = false;
}

function closeModal(state) {
  state.refs.modal.hidden = true;
}

function getCanonicalTags(state) {
  const seen = new Set();
  const tags = [];

  for (const entry of state.entries) {
    if (entry.type !== "resolved") continue;
    if (seen.has(entry.canonicalId)) continue;
    seen.add(entry.canonicalId);
    tags.push(entry.canonicalId);
  }

  tags.sort((a, b) => {
    const ga = groupFromTagId(a);
    const gb = groupFromTagId(b);
    const ia = GROUP_INDEX.has(ga) ? GROUP_INDEX.get(ga) : Number.MAX_SAFE_INTEGER;
    const ib = GROUP_INDEX.has(gb) ? GROUP_INDEX.get(gb) : Number.MAX_SAFE_INTEGER;
    if (ia !== ib) return ia - ib;
    return a.localeCompare(b);
  });

  return tags;
}

function groupFromTagId(tagId) {
  const normalized = normalize(tagId);
  const splitIndex = normalized.indexOf(":");
  return splitIndex >= 0 ? normalized.slice(0, splitIndex) : normalized;
}

function buildPatchSnippet(seriesId, canonicalTags, timestamp) {
  const tagsText = JSON.stringify(canonicalTags, null, 2).replace(/\n/g, "\n    ");
  return `${JSON.stringify(seriesId)}: {\n  "tags": ${tagsText},\n  "updated_at_utc": ${JSON.stringify(timestamp)}\n}`;
}

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function setStatus(state, kind, text) {
  state.statusKind = kind || "";
  state.statusText = text || "";
}

function renderStatus(state) {
  state.refs.status.textContent = state.statusText || "";
  state.refs.status.className = "tagStudio__status";
  if (state.statusKind) {
    state.refs.status.classList.add(`is-${state.statusKind}`);
  }
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

function renderFatalError(mount, message) {
  mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
}
