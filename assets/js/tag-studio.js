const GROUPS = ["subject", "domain", "form", "theme"];
const GROUP_INDEX = new Map(GROUPS.map((group, index) => [group, index]));
const POST_ENDPOINT = "http://127.0.0.1:8787/save-tags";
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
const POPUP_TAG_MATCH_CAP = 12;
const POPUP_ALIAS_MATCH_CAP = 12;

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
      fetchJson("/assets/data/tag_registry.json"),
      fetchJson("/assets/data/tag_aliases.json"),
      fetchJson("/assets/data/tag_assignments.json")
    ]);

    const state = buildState(mount, seriesId, registryJson, aliasesJson, assignmentsJson);
    renderShell(state);
    wireEvents(state);
    renderAll(state);
    void probeSaveMode(state);
  } catch (error) {
    renderFatalError(
      mount,
      "Failed to load tag data. Check /assets/data/tag_registry.json, /assets/data/tag_aliases.json, and /assets/data/tag_assignments.json."
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

  for (const rawTag of tags) {
    const tag = sanitizeTag(rawTag);
    if (!tag) continue;

    tagsById.set(tag.tag_id, tag);
    pushMapList(slugMap, tag.slug, tag);
    pushMapList(labelMap, normalize(tag.label), tag);

    if (tag.status === "active") {
      activeTags.push(tag);
    }
  }

  activeTags.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
  const activeTagsBySlug = activeTags.slice().sort((a, b) => {
    const bySlug = a.slug.localeCompare(b.slug, undefined, { sensitivity: "base" });
    if (bySlug !== 0) return bySlug;
    return a.tag_id.localeCompare(b.tag_id);
  });

  const aliases = new Map();
  const rawAliases = aliasesJson && typeof aliasesJson.aliases === "object" ? aliasesJson.aliases : {};
  for (const [aliasInput, targetInput] of Object.entries(rawAliases)) {
    const aliasKey = normalize(aliasInput);
    if (!aliasKey) continue;
    const targetTagIds = normalizeAliasTargets(targetInput);
    if (!targetTagIds.length) continue;
    aliases.set(aliasKey, targetTagIds);
  }
  const aliasOptions = buildAliasOptions(aliases, tagsById);

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
    activeTagsBySlug,
    aliasOptions,
    entries,
    nextEntryId,
    statusText: "",
    statusKind: "",
    pendingChooserRaw: "",
    refs: null,
    modalSnippet: "",
    saveMode: "patch"
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
      <section class="tagStudio__panel tagStudio__panel--editor">
        <div data-role="groups"></div>
        <div class="tagStudio__inputRow tagStudio__inputRow--editor">
          <input id="tagStudioInput" class="tagStudio__input" type="text" autocomplete="off" placeholder="tag slug or alias">
          <button type="button" class="tagStudio__button" data-role="add-tag">Add</button>
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save">Save Tags</button>
          <span class="tagStudio__saveMode" data-role="save-mode">Save mode: Patch</span>
        </div>
        <div class="tagStudio__popup tagStudio__popup--series" data-role="popup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="popup-list"></div>
        </div>
        <p class="tagStudio__status" data-role="status"></p>
        <p class="tagStudio__saveWarning" data-role="save-warning"></p>
        <p class="tagStudio__saveResult" data-role="save-result"></p>
      </section>
    </div>

    <div class="tagStudioModal" data-role="modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagStudioModalTitle">
        <h3 id="tagStudioModalTitle">Tag Patch Preview</h3>
        <p class="tagStudioModal__label">Canonical resolved tags</p>
        <pre class="tagStudioModal__pre" data-role="modal-tags"></pre>
        <p class="tagStudioModal__label">Patch snippet for <code>tag_assignments.json</code></p>
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
    popup: state.mount.querySelector('[data-role="popup"]'),
    popupList: state.mount.querySelector('[data-role="popup-list"]'),
    status: state.mount.querySelector('[data-role="status"]'),
    groups: state.mount.querySelector('[data-role="groups"]'),
    saveButton: state.mount.querySelector('[data-role="save"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    saveWarning: state.mount.querySelector('[data-role="save-warning"]'),
    saveResult: state.mount.querySelector('[data-role="save-result"]'),
    modal: state.mount.querySelector('[data-role="modal"]'),
    modalTags: state.mount.querySelector('[data-role="modal-tags"]'),
    modalSnippet: state.mount.querySelector('[data-role="modal-snippet"]'),
    copyButton: state.mount.querySelector('[data-role="copy-snippet"]')
  };
}

function wireEvents(state) {
  state.refs.input.addEventListener("input", () => {
    setStatus(state, "", "");
    renderStatus(state);
    renderPopup(state);
  });

  state.refs.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addFromInput(state);
    } else if (event.key === "Escape") {
      hidePopup(state);
    }
  });

  document.addEventListener("pointerdown", (event) => {
    if (!state.refs.popup || state.refs.popup.hidden) return;
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.closest('[data-role="popup"]')) return;
    if (target.closest("#tagStudioInput")) return;
    hidePopup(state);
  });

  state.refs.addButton.addEventListener("click", () => {
    addFromInput(state);
  });

  state.refs.popupList.addEventListener("click", (event) => {
    const tagButton = event.target.closest("button[data-popup-tag-id]");
    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-popup-tag-id"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      addResolvedTag(state, tag, tag.slug || tag.tag_id);
      state.refs.input.value = "";
      hidePopup(state);
      renderAll(state);
      return;
    }

    const aliasTargetButton = event.target.closest("button[data-popup-alias-target]");
    if (aliasTargetButton) {
      const tagId = normalize(aliasTargetButton.getAttribute("data-popup-alias-target"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      const aliasSource = normalize(aliasTargetButton.getAttribute("data-popup-alias-source"));
      addResolvedTag(state, tag, aliasSource || tag.tag_id);
      state.refs.input.value = "";
      hidePopup(state);
      renderAll(state);
      return;
    }

    const aliasPill = event.target.closest("[data-popup-alias]");
    if (aliasPill) return;
  });

  state.refs.groups.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-remove-entry-id]");
    if (!button) return;

    const entryId = Number(button.getAttribute("data-remove-entry-id"));
    removeEntry(state, entryId);
    renderAll(state);
  });

  state.refs.saveButton.addEventListener("click", () => {
    void handleSave(state);
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
    setStatus(state, "warn", "Enter a tag slug, tag id, or alias.");
    renderStatus(state);
    return;
  }

  const resolved = resolveInput(rawInput, state);
  if (resolved.type === "resolved") {
    addResolvedTag(state, resolved.tag, rawInput);
    state.refs.input.value = "";
    hidePopup(state);
    renderAll(state);
    return;
  }

  if (resolved.type === "ambiguous") {
    const candidateIds = resolved.candidates.map((tag) => tag.tag_id).slice(0, 6);
    const suffix = resolved.candidates.length > 6 ? ", ..." : "";
    setStatus(state, "warn", `Multiple matches for "${rawInput}": ${candidateIds.join(", ")}${suffix}. Choose one from autocomplete.`);
    renderStatus(state);
    return;
  }

  if (resolved.type === "unresolved") {
    setStatus(state, "error", `Unknown tag: "${rawInput}".`);
    renderStatus(state);
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

  const aliasTagIds = state.aliases.get(normalized);
  if (Array.isArray(aliasTagIds) && aliasTagIds.length) {
    const aliasCandidates = [];
    const seenAlias = new Set();
    for (const aliasTagId of aliasTagIds) {
      const normalizedAliasTagId = normalize(aliasTagId);
      if (!normalizedAliasTagId || seenAlias.has(normalizedAliasTagId)) continue;
      seenAlias.add(normalizedAliasTagId);
      const aliasTag = state.tagsById.get(normalizedAliasTagId);
      if (aliasTag) aliasCandidates.push(aliasTag);
    }
    if (aliasCandidates.length === 1) return { type: "resolved", tag: aliasCandidates[0] };
    if (aliasCandidates.length > 1) {
      aliasCandidates.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
      return { type: "ambiguous", candidates: aliasCandidates };
    }
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
  setSaveResult(state, "", "");
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
  setSaveResult(state, "", "");
}

function removeEntry(state, entryId) {
  const sizeBefore = state.entries.length;
  state.entries = state.entries.filter((entry) => entry.entryId !== entryId);
  if (state.entries.length < sizeBefore) {
    setStatus(state, "success", "Tag removed.");
    setSaveResult(state, "", "");
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
  renderGroups(state);
  renderPopup(state);
  renderSaveMode(state);
  renderSaveState(state);
}

function renderPopup(state) {
  const query = normalize(state.refs.input.value);
  if (!query) {
    hidePopup(state);
    return;
  }

  const selectedTagIds = getSelectedTagIdSet(state);
  const tagMatches = state.activeTagsBySlug
    .filter((tag) => tag.slug.startsWith(query) && !selectedTagIds.has(tag.tag_id))
    .slice(0, POPUP_TAG_MATCH_CAP);
  const aliasMatches = getPopupAliasMatches(state, query, selectedTagIds).slice(0, POPUP_ALIAS_MATCH_CAP);

  if (!tagMatches.length && !aliasMatches.length) {
    hidePopup(state);
    return;
  }

  const tagSection = tagMatches.length
    ? `
      <section class="tagStudioSuggest__section">
        <p class="tagStudioSuggest__heading">tags</p>
        <div class="tagStudioSuggest__tagRows">
          ${tagMatches.map((tag) => {
      return `
        <button
          type="button"
          class="tagStudio__popupPill tagStudio__chip--${escapeHtml(tag.group)}"
          data-popup-tag-id="${escapeHtml(tag.tag_id)}"
          title="${escapeHtml(tag.tag_id)}"
        >
          ${escapeHtml(tag.label)}
        </button>
      `;
    }).join("")}
        </div>
      </section>
    `
    : "";

  const aliasSection = aliasMatches.length
    ? `
      <section class="tagStudioSuggest__section">
        <p class="tagStudioSuggest__heading">aliases</p>
        <div class="tagStudioSuggest__aliasRows">
          ${aliasMatches.map((entry) => {
      return `
        <div class="tagStudioSuggest__aliasRow">
          <span
            class="tagStudio__popupPill tagStudioSuggest__aliasPill"
            data-popup-alias="${escapeHtml(entry.alias)}"
            title="${escapeHtml(entry.alias)}"
          >
            ${escapeHtml(entry.alias)}
          </span>
          <div class="tagStudioSuggest__aliasTargets">
            ${entry.targets.map((target) => `
              <button
                type="button"
                class="tagStudio__popupPill tagStudio__chip--${escapeHtml(target.group)} tagStudioSuggest__aliasTarget"
                data-popup-alias-target="${escapeHtml(target.tagId)}"
                data-popup-alias-source="${escapeHtml(entry.alias)}"
                title="${escapeHtml(target.tagId)}"
              >
                ${escapeHtml(target.label)}
              </button>
            `).join("")}
          </div>
        </div>
      `;
    }).join("")}
        </div>
      </section>
    `
    : "";

  state.refs.popupList.innerHTML = `
    <div class="tagStudioSuggest">
      ${tagSection}
      ${aliasSection}
    </div>
  `;
  state.refs.popup.hidden = false;
}

function hidePopup(state) {
  state.refs.popup.hidden = true;
  state.refs.popupList.innerHTML = "";
}

function getPopupAliasMatches(state, query, selectedTagIds) {
  return state.aliasOptions
    .filter((entry) => entry.alias.startsWith(query))
    .map((entry) => ({
      alias: entry.alias,
      targets: entry.targets.filter((target) => !selectedTagIds.has(target.tagId))
    }))
    .filter((entry) => entry.targets.length > 0);
}

function getSelectedTagIdSet(state) {
  const out = new Set();
  for (const entry of state.entries) {
    if (entry.type !== "resolved") continue;
    out.add(entry.canonicalId);
  }
  return out;
}

function buildAliasOptions(aliases, tagsById) {
  const out = [];
  for (const [alias, targets] of aliases.entries()) {
    const resolved = [];
    const seen = new Set();
    for (const targetTagId of targets) {
      const normalizedTagId = normalize(targetTagId);
      if (!normalizedTagId || seen.has(normalizedTagId)) continue;
      const tag = tagsById.get(normalizedTagId);
      if (!tag) continue;
      seen.add(normalizedTagId);
      resolved.push({
        tagId: normalizedTagId,
        group: tag.group,
        label: tag.label
      });
    }
    if (!resolved.length) continue;
    resolved.sort((a, b) => {
      const aIndex = GROUP_INDEX.has(a.group) ? GROUP_INDEX.get(a.group) : Number.MAX_SAFE_INTEGER;
      const bIndex = GROUP_INDEX.has(b.group) ? GROUP_INDEX.get(b.group) : Number.MAX_SAFE_INTEGER;
      if (aIndex !== bIndex) return aIndex - bIndex;
      return a.tagId.localeCompare(b.tagId);
    });
    out.push({ alias, targets: resolved });
  }
  out.sort((a, b) => a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" }));
  return out;
}

function renderGroups(state) {
  const groupedEntries = new Map(GROUPS.map((group) => [group, []]));
  for (const entry of state.entries) {
    if (entry.type !== "resolved") continue;
    if (!groupedEntries.has(entry.group)) continue;
    groupedEntries.get(entry.group).push(entry);
  }
  for (const group of GROUPS) {
    groupedEntries.get(group).sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
  }

  const rowsHtml = GROUPS.map((group) => {
    const entries = groupedEntries.get(group) || [];
    const chipsHtml = entries.map((entry) => `
      <span class="tagStudio__chip tagStudio__chip--${escapeHtml(entry.group)}">
        <span class="tagStudio__chipTag" title="${escapeHtml(entry.canonicalId)}">${escapeHtml(entry.label)}</span>
        <button type="button" class="tagStudio__chipRemove" data-remove-entry-id="${entry.entryId}" aria-label="Remove ${escapeHtml(entry.canonicalId)}">x</button>
      </span>
    `).join("");
    return `
      <div class="tagStudioGroupRow">
        <span class="tagStudioGroupRow__label">${escapeHtml(group)}:</span>
        <div class="tagStudioGroupRow__chips">${chipsHtml}</div>
      </div>
    `;
  }).join("");

  state.refs.groups.innerHTML = `<div class="tagStudioGroups">${rowsHtml}</div>`;
}

function renderSaveState(state) {
  const metrics = computeMetrics(state);
  const hasUnresolved = metrics.unresolvedCount > 0;
  state.refs.saveButton.disabled = hasUnresolved;
  state.refs.saveWarning.textContent = hasUnresolved ? "Resolve unknown tags before saving." : "";
}

function renderSaveMode(state) {
  if (!state.refs.saveMode) return;
  const label = state.saveMode === "post" ? "Local server" : "Patch";
  state.refs.saveMode.textContent = `Save mode: ${label}`;
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

async function probeSaveMode(state) {
  const ok = await isLocalSaveAvailable(500);
  state.saveMode = ok ? "post" : "patch";
  renderSaveMode(state);
}

async function isLocalSaveAvailable(timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(HEALTH_ENDPOINT, { signal: controller.signal });
    if (!response.ok) return false;
    const data = await response.json();
    return Boolean(data && data.ok);
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function handleSave(state) {
  const metrics = computeMetrics(state);
  if (metrics.unresolvedCount > 0) {
    setStatus(state, "error", "Resolve unknown tags before saving.");
    renderStatus(state);
    return;
  }

  const canonicalTags = getCanonicalTags(state);
  if (state.saveMode === "post") {
    try {
      const result = await postTags(state.seriesId, canonicalTags);
      const savedAt = String(result.updated_at_utc || utcTimestamp());
      setStatus(state, "success", `Saved at ${savedAt}.`);
      setSaveResult(state, "success", `Saved at ${savedAt}.`);
      renderStatus(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderSaveMode(state);
      setStatus(state, "error", "Local save failed. Switched to Patch mode.");
      setSaveResult(state, "error", "Local server save failed. Showing patch fallback.");
      renderStatus(state);
      openSaveModal(state);
      return;
    }
  }

  openSaveModal(state);
}

async function postTags(seriesId, tags) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(POST_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        series_id: seriesId,
        tags,
        client_time_utc: utcTimestamp()
      }),
      signal: controller.signal
    });

    let body = null;
    try {
      body = await response.json();
    } catch (error) {
      body = null;
    }

    if (!response.ok || !body || !body.ok) {
      const message = (body && body.error) ? String(body.error) : `HTTP ${response.status}`;
      throw new Error(message);
    }
    return body;
  } finally {
    clearTimeout(timer);
  }
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

function setSaveResult(state, kind, text) {
  if (!state.refs.saveResult) return;
  state.refs.saveResult.textContent = text || "";
  state.refs.saveResult.className = "tagStudio__saveResult";
  if (kind) state.refs.saveResult.classList.add(`is-${kind}`);
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function normalizeAliasTargets(value) {
  const rawTargets = (value && typeof value === "object" && !Array.isArray(value))
    ? value.tags
    : value;

  if (Array.isArray(rawTargets)) {
    const out = [];
    const seen = new Set();
    for (const item of rawTargets) {
      const normalized = normalize(item);
      if (!normalized || seen.has(normalized)) continue;
      seen.add(normalized);
      out.push(normalized);
    }
    return out;
  }

  const single = normalize(rawTargets);
  return single ? [single] : [];
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
