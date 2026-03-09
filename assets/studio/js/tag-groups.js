import {
  getStudioGroups,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadStudioGroupsJson,
  normalizeStudioGroups
} from "./studio-data.js";
import {
  tagGroupsUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const UI = tagGroupsUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagGroupsPage);
} else {
  initTagGroupsPage();
}

async function initTagGroupsPage() {
  const root = document.querySelector(UI_SELECTOR.pageRoot);
  if (!root) return;
  const content = root.querySelector(UI_SELECTOR.content);
  if (!content) return;

  try {
    const config = await loadStudioConfig();
    STUDIO_GROUPS = getStudioGroups(config);
    const data = await loadStudioGroupsJson(config);
    const groups = normalizeStudioGroups(data, STUDIO_GROUPS);
    renderGroups(content, groups, config);
  } catch (error) {
    content.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(tagGroupsText(null, "load_failed_error", "Failed to load group descriptions from /assets/studio/data/tag_groups.json."))}</div>`;
  }
}

function renderGroups(content, groups, config) {
  if (!groups.length) {
    content.innerHTML = `<p class="${UI_CLASS.empty}">${escapeHtml(tagGroupsText(config, "empty_state", "No group descriptions available."))}</p>`;
    return;
  }

  content.innerHTML = `
    <div class="tagGroups__sections">
      ${groups.map((group) => `
        <section class="${UI_CLASS.section}">
          <p class="${UI_CLASS.head}">
            <span class="${classNames(UI_CLASS.chip, chipGroupClass(group.groupId))}">${escapeHtml(group.groupId)}</span>
          </p>
          ${group.description ? `<p class="tagGroups__short">${escapeHtml(group.description)}</p>` : ""}
          <p class="${UI_CLASS.text}">${escapeHtml(group.descriptionLong || tagGroupsText(config, "description_long_fallback", "No long description available."))}</p>
        </section>
      `).join("")}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function tagGroupsText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_groups.${key}`, fallback, tokens);
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}
