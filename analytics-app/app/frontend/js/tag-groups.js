import {
  getAnalyticsGroups,
  getAnalyticsText,
  loadAnalyticsConfigWithText
} from "./analytics-config.js";
import {
  loadAnalyticsGroupsJson,
  normalizeAnalyticsGroups
} from "./analytics-data.js";
import {
  initializeStudioRouteState,
  setStudioRouteReady
} from "./analytics-route-state.js";
import {
  tagGroupsUi
} from "./analytics-ui.js";

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
  initializeStudioRouteState(root, { route: "tag-groups", mode: "list" });

  try {
    const config = await loadAnalyticsConfigWithText("tag_groups");
    STUDIO_GROUPS = getAnalyticsGroups(config);
    const data = await loadAnalyticsGroupsJson(config);
    const groups = normalizeAnalyticsGroups(data, STUDIO_GROUPS);
    renderGroups(content, groups, config);
    setStudioRouteReady(root, true, {
      route: "tag-groups",
      mode: groups.length ? "list" : "empty",
      recordLoaded: groups.length > 0
    });
  } catch (error) {
    content.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(tagGroupsText(null, "load_failed_error", "Failed to load group descriptions from the local analytics API."))}</div>`;
    setStudioRouteReady(root, true, {
      route: "tag-groups",
      mode: "empty",
      recordLoaded: false
    });
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
  return getAnalyticsText(config, `tag_groups.${key}`, fallback, tokens);
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}
