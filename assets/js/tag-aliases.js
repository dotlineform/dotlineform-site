const GROUPS = ["subject", "domain", "form", "theme"];
const TAG_ID_RE = /^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$/;
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
const IMPORT_ENDPOINT = "http://127.0.0.1:8787/import-tag-aliases";
const DELETE_ENDPOINT = "http://127.0.0.1:8787/delete-tag-alias";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagAliasesPage);
} else {
  initTagAliasesPage();
}

async function initTagAliasesPage() {
  const mount = document.getElementById("tag-aliases");
  if (!mount) return;

  const state = {
    mount,
    aliases: [],
    registryById: new Map(),
    aliasesUpdatedAt: "",
    searchQuery: "",
    filterGroup: "all",
    sortKey: "alias",
    sortDir: "asc",
    importMode: "add",
    saveMode: "patch",
    selectedFile: null,
    patchSnippet: "",
    refs: null
  };

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadData(state);
    renderControls(state);
    renderList(state);
  } catch (error) {
    renderError(state, "Failed to load aliases from /assets/data/tag_aliases.json.");
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  state.mount.innerHTML = `
    <section class="tagStudio__panel">
      <div class="tagRegistry__importBox">
        <div class="tagRegistry__importRow">
          <label class="tagRegistry__fileWrap">
            <span class="tagRegistry__importLabel">import file</span>
            <button type="button" class="tagStudio__button tagStudio__button--primary tagRegistry__chooseBtn" data-role="choose-file">Choose file</button>
            <input type="file" class="tagRegistry__fileInput" data-role="import-file" accept=".json,application/json" hidden>
          </label>
          <label class="tagRegistry__modeWrap">
            <span class="tagRegistry__importLabel">mode</span>
            <select class="tagRegistry__modeSelect" data-role="import-mode">
              <option value="add">add (no overwrite)</option>
              <option value="merge">add + overwrite</option>
              <option value="replace">replace entire aliases</option>
            </select>
          </label>
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="import-btn">Import</button>
          <span class="tagRegistry__saveMode" data-role="save-mode">Import mode: Patch</span>
        </div>
        <p class="tagRegistry__selected" data-role="selected-file"></p>
        <p class="tagRegistry__result" data-role="import-result"></p>
      </div>

      <div class="tagAliases__controls">
        <div class="tagStudio__key tagRegistry__key" data-role="key"></div>
        <label class="tagRegistry__searchWrap">
          <span class="visually-hidden">Search aliases</span>
          <input
            type="text"
            class="tagStudio__input tagRegistry__searchInput"
            data-role="search"
            placeholder="search"
            autocomplete="off"
          >
        </label>
      </div>

      <div data-role="list"></div>
    </section>

    <div class="tagStudioModal" data-role="patch-modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagAliasesPatchTitle">
        <h3 id="tagAliasesPatchTitle">Aliases Patch Preview</h3>
        <p class="tagStudioModal__label">Manual patch snippet (new aliases only)</p>
        <pre class="tagStudioModal__pre" data-role="patch-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-patch">Copy</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">Close</button>
        </div>
      </div>
    </div>
  `;

  state.refs = {
    key: state.mount.querySelector('[data-role="key"]'),
    search: state.mount.querySelector('[data-role="search"]'),
    chooseFile: state.mount.querySelector('[data-role="choose-file"]'),
    importFile: state.mount.querySelector('[data-role="import-file"]'),
    importMode: state.mount.querySelector('[data-role="import-mode"]'),
    importButton: state.mount.querySelector('[data-role="import-btn"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    selectedFile: state.mount.querySelector('[data-role="selected-file"]'),
    importResult: state.mount.querySelector('[data-role="import-result"]'),
    list: state.mount.querySelector('[data-role="list"]'),
    patchModal: state.mount.querySelector('[data-role="patch-modal"]'),
    patchSnippet: state.mount.querySelector('[data-role="patch-snippet"]'),
    copyPatch: state.mount.querySelector('[data-role="copy-patch"]')
  };
}

function wireEvents(state) {
  state.refs.search.addEventListener("input", () => {
    state.searchQuery = normalize(state.refs.search.value);
    renderList(state);
  });

  state.refs.chooseFile.addEventListener("click", () => {
    state.refs.importFile.click();
  });

  state.refs.importFile.addEventListener("change", () => {
    const files = state.refs.importFile.files;
    state.selectedFile = files && files.length ? files[0] : null;
    state.refs.selectedFile.textContent = state.selectedFile ? `Selected: ${state.selectedFile.name}` : "";
  });

  state.refs.importMode.addEventListener("change", () => {
    syncImportModeFromControl(state);
  });

  state.refs.importButton.addEventListener("click", () => {
    void handleImport(state);
  });

  state.mount.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("button[data-delete-alias]");
    if (deleteButton) {
      const alias = normalize(deleteButton.getAttribute("data-delete-alias"));
      if (alias) void handleAliasDelete(state, alias);
      return;
    }

    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      state.filterGroup = group && group !== "all" ? group : "all";
      renderControls(state);
      renderList(state);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (sortButton) {
      const key = normalize(sortButton.getAttribute("data-sort-key"));
      if (!key) return;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      renderList(state);
      return;
    }
  });

  state.refs.patchModal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-modal"]')) return;
    closePatchModal(state);
  });

  state.refs.copyPatch.addEventListener("click", async () => {
    if (!state.patchSnippet) return;
    try {
      await navigator.clipboard.writeText(state.patchSnippet);
      setImportResult(state, "success", "Patch snippet copied to clipboard.");
    } catch (error) {
      setImportResult(state, "error", "Copy failed. Select and copy the snippet manually.");
    }
  });
}

function syncImportModeFromControl(state) {
  const mode = normalize(state.refs.importMode.value);
  if (mode === "replace") {
    state.importMode = "replace";
  } else if (mode === "merge") {
    state.importMode = "merge";
  } else {
    state.importMode = "add";
  }
}

async function loadData(state) {
  const [registryData, aliasesData] = await Promise.all([
    fetchJson("/assets/data/tag_registry.json"),
    fetchJson("/assets/data/tag_aliases.json")
  ]);
  state.registryById = buildRegistryLookup(registryData);
  state.aliasesUpdatedAt = normalizeTimestamp(aliasesData && aliasesData.updated_at_utc);
  state.aliases = normalizeAliases(aliasesData, state.aliasesUpdatedAt, state.registryById);
}

function buildRegistryLookup(data) {
  const map = new Map();
  const tags = Array.isArray(data && data.tags) ? data.tags : [];
  for (const raw of tags) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    const group = normalize(raw.group);
    const label = String(raw.label || "").trim();
    if (!tagId || !GROUPS.includes(group) || !label) continue;
    map.set(tagId, { group, label });
  }
  return map;
}

function normalizeAliases(data, fallbackUpdatedAt, registryById) {
  const aliasesObj = data && typeof data.aliases === "object" && data.aliases ? data.aliases : {};
  const entries = [];

  for (const [rawAlias, rawValue] of Object.entries(aliasesObj)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalizedValue = null;
    try {
      normalizedValue = normalizeAliasValue(rawValue);
    } catch (error) {
      continue;
    }

    const targets = normalizedValue.targets;
    const resolvedTargets = targets.map((tagId) => {
      const info = registryById.get(tagId);
      return {
        tagId,
        group: info ? info.group : "",
        label: info ? info.label : tagId,
        known: Boolean(info)
      };
    });
    const groups = Array.from(new Set(resolvedTargets.filter((item) => item.known).map((item) => item.group)));
    const hasUnknown = resolvedTargets.some((item) => !item.known);
    const updatedAtUtc = fallbackUpdatedAt;

    entries.push({
      alias,
      value: normalizedValue.value,
      targets,
      resolvedTargets,
      groups,
      hasUnknown,
      updatedAtUtc,
      updatedAtMs: toTimestampMs(updatedAtUtc)
    });
  }
  return entries;
}

function normalizeAliasValue(rawValue) {
  if (typeof rawValue === "string") {
    const value = normalize(rawValue);
    if (!TAG_ID_RE.test(value)) {
      throw new Error("Invalid alias tag_id value.");
    }
    return { value, targets: [value] };
  }
  if (!Array.isArray(rawValue)) {
    throw new Error("Alias value must be string or array.");
  }

  const out = [];
  const seen = new Set();
  for (const raw of rawValue) {
    const value = normalize(raw);
    if (!value || !TAG_ID_RE.test(value)) {
      throw new Error("Invalid alias tag_id array value.");
    }
    if (seen.has(value)) continue;
    seen.add(value);
    out.push(value);
  }
  if (!out.length) {
    throw new Error("Alias array value must include at least one tag_id.");
  }
  return { value: out, targets: out.slice() };
}

function renderControls(state) {
  const counts = countAliasesByGroup(state.aliases);
  const totalCount = state.aliases.length;
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const count = Number(counts[group] || 0);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
      >
        ${escapeHtml(group)} [${count}]
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags [${totalCount}]</button>
    ${groupButtons}
  `;
}

function countAliasesByGroup(aliases) {
  const counts = { subject: 0, domain: 0, form: 0, theme: 0 };
  for (const entry of aliases || []) {
    for (const group of entry.groups || []) {
      if (GROUPS.includes(group)) {
        counts[group] += 1;
      }
    }
  }
  return counts;
}

function renderList(state) {
  const visible = getVisibleAliases(state);

  const headerHtml = `
    <div class="tagAliases__head">
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "updatedat")}" data-sort-key="updatedat">
        timestamp${sortIndicator(state, "updatedat")}
      </button>
      <button type="button" class="tagRegistry__sortBtn${sortBtnClass(state, "alias")}" data-sort-key="alias">
        alias${sortIndicator(state, "alias")}
      </button>
      <span class="tagAliases__headLabel">group tags</span>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="tagStudio__empty">none</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="tagAliases__rows">
      ${visible.map((entry) => {
        const sortedTargets = entry.resolvedTargets.slice().sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
        return `
        <li class="tagAliases__row">
          <div class="tagAliases__tsCol">${escapeHtml(formatTimestamp(entry.updatedAtUtc))}</div>
          <div class="tagAliases__aliasCol">
            <span class="tagStudio__chip ${escapeHtml(getAliasClass(entry))}">
              <span>${escapeHtml(entry.alias)}</span>
              <button
                type="button"
                class="tagStudio__chipRemove"
                data-delete-alias="${escapeHtml(entry.alias)}"
                aria-label="Delete alias ${escapeHtml(entry.alias)}"
                title="Delete alias"
              >
                ×
              </button>
            </span>
          </div>
          <div class="tagAliases__tagsCol">
            <div class="tagAliases__tagList">
              ${sortedTargets.map((target) => `
                <span class="tagStudio__chip ${escapeHtml(target.known ? `tagStudio__chip--${target.group}` : "tagStudio__chip--warning")}" title="${escapeHtml(target.tagId)}">
                  ${escapeHtml(String(target.label || "").toLowerCase())}
                </span>
              `).join("")}
            </div>
          </div>
        </li>
      `;
      }).join("")}
    </ul>
  `;
}

function getAliasClass(entry) {
  if (!entry || entry.hasUnknown || !entry.groups.length || entry.groups.length > 1) {
    return "tagStudio__chip--warning";
  }
  const group = entry.groups[0];
  return GROUPS.includes(group) ? `tagStudio__chip--${group}` : "tagStudio__chip--warning";
}

function getVisibleAliases(state) {
  const filtered = state.aliases.filter((entry) => {
    const searchMatch = !state.searchQuery || normalize(entry.alias).startsWith(state.searchQuery);
    if (!searchMatch) return false;
    if (state.filterGroup === "all") return true;
    return Array.isArray(entry.groups) && entry.groups.includes(state.filterGroup);
  });

  const direction = state.sortDir === "desc" ? -1 : 1;
  filtered.sort((a, b) => direction * compareAliases(a, b, state.sortKey));
  return filtered;
}

function compareAliases(a, b, sortKey) {
  if (sortKey === "updatedat") {
    if (a.updatedAtMs === null && b.updatedAtMs === null) return compareAliases(a, b, "alias");
    if (a.updatedAtMs === null) return 1;
    if (b.updatedAtMs === null) return -1;
    if (a.updatedAtMs !== b.updatedAtMs) return a.updatedAtMs - b.updatedAtMs;
    return compareAliases(a, b, "alias");
  }
  return a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" });
}

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function sortBtnClass(state, key) {
  return state.sortKey === key ? " is-active" : "";
}

async function probeImportMode(state) {
  const ok = await pingHealthEndpoint();
  state.saveMode = ok ? "post" : "patch";
  renderImportMode(state);
}

function renderImportMode(state) {
  const label = state.saveMode === "post" ? "Local server" : "Patch";
  state.refs.saveMode.textContent = `Import mode: ${label}`;
}

async function pingHealthEndpoint() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 500);
  try {
    const response = await fetch(HEALTH_ENDPOINT, { signal: controller.signal, cache: "no-store" });
    if (!response.ok) return false;
    const payload = await response.json();
    return Boolean(payload && payload.ok);
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", "Choose an import file first.");
    return;
  }

  let importAliases = null;
  try {
    importAliases = await readImportAliasesFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || "Invalid import file."));
    return;
  }

  if (state.saveMode === "post") {
    try {
      const response = await postJson(IMPORT_ENDPOINT, {
        mode: state.importMode,
        import_aliases: importAliases,
        import_filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
        client_time_utc: utcTimestamp()
      });
      setImportResult(state, "success", buildImportSummary(response));
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setImportResult(state, "error", `Server import failed; switched to patch mode. ${error.message || ""}`.trim());
    }
  }

  const patchResult = buildManualPatchForNewAliases(state, importAliases);
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function handleAliasDelete(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;

  const ok = window.confirm(`Delete alias "${aliasKey}"?`);
  if (!ok) return;

  if (state.saveMode === "post") {
    try {
      const response = await postJson(DELETE_ENDPOINT, {
        alias: aliasKey,
        client_time_utc: utcTimestamp()
      });
      const summary = String(response.summary_text || "").trim() || `deleted alias ${aliasKey}`;
      setImportResult(state, "success", summary);
      await loadData(state);
      renderControls(state);
      renderList(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderImportMode(state);
      setImportResult(state, "error", `Server delete failed; switched to patch mode. ${error.message || ""}`.trim());
    }
  }

  const patchResult = buildManualPatchForAliasDelete(aliasKey);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function buildManualPatchForNewAliases(state, importAliases) {
  const importRows = normalizeImportAliasRows(importAliases.aliases || {});
  const existing = new Set(state.aliases.map((entry) => entry.alias));
  const nowUtc = utcTimestamp();
  const aliasesToAdd = {};
  let newCount = 0;

  for (const row of importRows) {
    if (existing.has(row.alias)) continue;
    aliasesToAdd[row.alias] = row.value;
    newCount += 1;
  }

  if (newCount === 0) {
    return {
      kind: "warn",
      message: `Patch mode (${state.importMode}): ${importRows.length} imported; 0 new aliases to add.`,
      snippet: ""
    };
  }

  const snippet = JSON.stringify(
    {
      updated_at_utc: nowUtc,
      aliases_to_add: aliasesToAdd
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: `Patch mode (${state.importMode}): ${importRows.length} imported; ${newCount} new aliases available to append.`,
    snippet
  };
}

function buildImportSummary(response) {
  const summaryText = String(response.summary_text || "").trim();
  if (summaryText) return summaryText;
  const mode = normalize(response.mode || "");
  return [
    `mode ${mode || "unknown"}`,
    `Imported ${Number(response.imported_total || 0)} aliases`,
    `added ${Number(response.added || 0)}`,
    `overwritten ${Number(response.overwritten || 0)}`,
    `unchanged ${Number(response.unchanged || 0)}`,
    `removed ${Number(response.removed || 0)}`,
    `final ${Number(response.final_total || 0)}`
  ].join("; ");
}

function buildManualPatchForAliasDelete(aliasKey) {
  const nowUtc = utcTimestamp();
  const snippet = JSON.stringify(
    {
      updated_at_utc: nowUtc,
      aliases_to_remove: [aliasKey]
    },
    null,
    2
  );

  return {
    kind: "warn",
    message: `Patch mode: alias "${aliasKey}" marked for removal.`,
    snippet
  };
}

function normalizeImportAliasRows(rawAliases) {
  if (!rawAliases || typeof rawAliases !== "object") return [];
  const out = [];
  const seen = new Set();
  for (const [rawAlias, rawValue] of Object.entries(rawAliases)) {
    const alias = normalize(rawAlias);
    if (!alias) continue;
    let normalized = null;
    try {
      normalized = normalizeAliasValue(rawValue);
    } catch (error) {
      continue;
    }
    if (seen.has(alias)) {
      const idx = out.findIndex((item) => item.alias === alias);
      if (idx >= 0) out[idx] = { alias, value: normalized.value, targets: normalized.targets };
      continue;
    }
    seen.add(alias);
    out.push({ alias, value: normalized.value, targets: normalized.targets });
  }
  return out;
}

async function readImportAliasesFromFile(file) {
  const rawText = await file.text();
  let payload = null;
  try {
    payload = JSON.parse(rawText);
  } catch (error) {
    throw new Error("Import file is not valid JSON.");
  }

  if (!payload || typeof payload !== "object") {
    throw new Error("Import file must be a JSON object.");
  }
  const rows = normalizeImportAliasRows(payload.aliases);
  if (!rows.length) {
    throw new Error("Import file must include aliases object with at least one alias.");
  }

  const aliasesObj = {};
  for (const row of rows) {
    aliasesObj[row.alias] = row.value;
  }
  return {
    tag_aliases_version: String(payload.tag_aliases_version || "tag_aliases_v1"),
    updated_at_utc: normalizeTimestamp(payload.updated_at_utc) || "",
    aliases: aliasesObj
  };
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  let responsePayload = null;
  try {
    responsePayload = await response.json();
  } catch (error) {
    throw new Error(`HTTP ${response.status}`);
  }
  if (!response.ok || !responsePayload || !responsePayload.ok) {
    const message = responsePayload && responsePayload.error ? responsePayload.error : `HTTP ${response.status}`;
    throw new Error(message);
  }
  return responsePayload;
}

function openPatchModal(state, snippet) {
  state.patchSnippet = snippet;
  state.refs.patchSnippet.textContent = snippet;
  state.refs.patchModal.hidden = false;
}

function closePatchModal(state) {
  state.refs.patchModal.hidden = true;
}

function setImportResult(state, kind, message) {
  state.refs.importResult.textContent = message || "";
  state.refs.importResult.className = "tagRegistry__result";
  if (kind) state.refs.importResult.classList.add(`is-${kind}`);
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function toTimestampMs(value) {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) ? ms : null;
}

function normalizeTimestamp(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const ms = Date.parse(raw);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

function formatTimestamp(value) {
  const normalized = normalizeTimestamp(value);
  if (!normalized) return "—";
  const date = new Date(normalized);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} - ${hour}:${minute}`;
}

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function renderError(state, message) {
  state.mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
