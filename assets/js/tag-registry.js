const GROUPS = ["subject", "domain", "form", "theme"];

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagRegistryPage);
} else {
  initTagRegistryPage();
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;

  const state = {
    mount,
    tags: [],
    filterGroup: "all"
  };

  renderShell(state);

  try {
    const data = await fetchJson("/assets/data/tag_registry.json");
    state.tags = normalizeRegistryTags(data).sort(compareTagsByLabel);
    renderControls(state);
    renderList(state);
  } catch (error) {
    renderError(state, "Failed to load tag registry from /assets/data/tag_registry.json.");
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function normalizeRegistryTags(data) {
  const rawTags = Array.isArray(data && data.tags) ? data.tags : [];
  const tags = [];

  for (const raw of rawTags) {
    if (!raw || typeof raw !== "object") continue;
    const group = normalize(raw.group);
    const tagId = normalize(raw.tag_id);
    const label = String(raw.label || "").trim();
    if (!GROUPS.includes(group) || !tagId || !label) continue;
    tags.push({ group, tagId, label });
  }

  return tags;
}

function compareTagsByLabel(a, b) {
  const byLabel = a.label.localeCompare(b.label, undefined, { sensitivity: "base" });
  if (byLabel !== 0) return byLabel;
  return a.tagId.localeCompare(b.tagId);
}

function renderShell(state) {
  state.mount.innerHTML = `
    <section class="tagStudio__panel">
      <div class="tagRegistry__controls">
        <div class="tagStudio__key tagRegistry__key" data-role="key"></div>
      </div>
      <div data-role="list"></div>
    </section>
  `;

  state.refs = {
    key: state.mount.querySelector('[data-role="key"]'),
    list: state.mount.querySelector('[data-role="list"]')
  };

  state.mount.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-group]");
    if (!button) return;
    const group = normalize(button.getAttribute("data-group"));
    state.filterGroup = group && group !== "all" ? group : "all";
    renderControls(state);
    renderList(state);
  });
}

function renderControls(state) {
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags</button>
    ${groupButtons}
  `;
}

function renderList(state) {
  const tags = state.filterGroup === "all"
    ? state.tags
    : state.tags.filter((tag) => tag.group === state.filterGroup);

  if (!tags.length) {
    state.refs.list.innerHTML = `<p class="tagStudio__empty">none</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    <ul class="tagStudio__chipList">
      ${tags.map((tag) => `
        <li class="tagStudio__chip tagStudio__chip--${escapeHtml(tag.group)}" title="${escapeHtml(tag.tagId)}">
          ${escapeHtml(tag.label)}
        </li>
      `).join("")}
    </ul>
  `;
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
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
