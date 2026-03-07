import {
  getStudioGroups,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadStudioGroupsJson,
  normalizeStudioGroups
} from "./studio-data.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagGroupsPage);
} else {
  initTagGroupsPage();
}

async function initTagGroupsPage() {
  const mount = document.getElementById("tag-groups");
  if (!mount) return;

  try {
    const config = await loadStudioConfig();
    STUDIO_GROUPS = getStudioGroups(config);
    const data = await loadStudioGroupsJson(config);
    const groups = normalizeStudioGroups(data, STUDIO_GROUPS);
    renderGroups(mount, groups, config);
  } catch (error) {
    mount.innerHTML = `<div class="tagStudioError">${escapeHtml(tagGroupsText(null, "load_failed_error", "Failed to load group descriptions from /assets/studio/data/tag_groups.json."))}</div>`;
  }
}

function renderGroups(mount, groups, config) {
  if (!groups.length) {
    mount.innerHTML = `<p class="tagStudio__empty">${escapeHtml(tagGroupsText(config, "empty_state", "No group descriptions available."))}</p>`;
    return;
  }

  mount.innerHTML = `
    <div class="tagStudio__panel">
      <div class="tagGroups__sections">
        ${groups.map((group) => `
          <section class="tagStudio__groupInfoSection tagGroups__section">
            <p class="tagStudio__groupInfoHead">
              <span class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group.groupId)}">${escapeHtml(group.groupId)}</span>
            </p>
            ${group.description ? `<p class="tagGroups__short">${escapeHtml(group.description)}</p>` : ""}
            <p class="tagStudio__groupInfoText">${escapeHtml(group.descriptionLong || tagGroupsText(config, "description_long_fallback", "No long description available."))}</p>
          </section>
        `).join("")}
      </div>
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
