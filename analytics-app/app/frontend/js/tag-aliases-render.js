import {
  getStudioText
} from "./studio-config.js";
import {
  countAliasesByGroup,
  getVisibleAliases
} from "./tag-aliases-domain.js";
import {
  tagAliasesUi
} from "./studio-ui.js";

const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const UI = tagAliasesUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

export function renderTagAliasesControls(state) {
  const studioGroups = getStudioGroups(state);
  const counts = countAliasesByGroup(state.aliases);
  const totalCount = state.aliases.length;
  const allTagsLabel = aliasesText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
  const groupButtons = studioGroups.map((group) => {
    const count = Number(counts[group] || 0);
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group), UI_CLASS.groupFilterButton)}"
        data-group="${escapeHtml(group)}"
        ${stateAttr(state.filterGroup === group ? UI_STATE.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)} [${count}]
      </button>
    `;
  }).join("");

  state.refs.key.innerHTML = `
    <button type="button" class="tagStudio__button ${UI_CLASS.allFilterButton}" data-group="all"${stateAttr(state.filterGroup === "all" ? UI_STATE.active : "")}>${escapeHtml(allTagsLabel)}</button>
    ${groupButtons}
    ${renderGroupInfoControl(state)}
  `;
}

export function renderTagAliasesList(state) {
  const visible = getVisibleAliases(state);
  const aliasHeading = aliasesText(state.config, "table_heading_alias", "alias");
  const tagsHeading = aliasesText(state.config, "group_tags_heading", "tags");

  const headerHtml = `
    <div class="${UI_CLASS.listHead}">
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="alias"${stateAttr(state.sortKey === "alias" ? UI_STATE.active : "")}>
        ${escapeHtml(aliasHeading)}${sortIndicator(state, "alias")}
      </button>
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="tags"${stateAttr(state.sortKey === "tags" ? UI_STATE.active : "")}>
        ${escapeHtml(tagsHeading)}${sortIndicator(state, "tags")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="${UI_CLASS.empty}">${escapeHtml(aliasesText(state.config, "empty_state", "none"))}</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="${UI_CLASS.listRows}">
      ${visible.map((entry) => renderAliasRow(state, entry)).join("")}
    </ul>
  `;
}

export function renderTagAliasesError(state, message) {
  state.mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(message)}</div>`;
}

function renderAliasRow(state, entry) {
  const sortedTargets = entry.resolvedTargets.slice().sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" }));
  return `
    <li class="${UI_CLASS.listRow}">
      <div class="${UI_CLASS.aliasCol}">
        <span class="${UI_CLASS.chip}">
          <button
            type="button"
            class="${UI_CLASS.aliasButton}"
            data-edit-alias="${escapeHtml(entry.alias)}"
            title="${escapeHtml(aliasesText(state.config, "alias_edit_title", "Edit alias {alias}", { alias: entry.alias }))}"
            aria-label="${escapeHtml(aliasesText(state.config, "alias_edit_aria_label", "Edit alias {alias}", { alias: entry.alias }))}"
          >
            ${escapeHtml(entry.alias)}
          </button>
          <button
            type="button"
            class="${UI_CLASS.chipRemove}"
            data-promote-alias="${escapeHtml(entry.alias)}"
            aria-label="${escapeHtml(aliasesText(state.config, "alias_promote_aria_label", "Promote alias {alias}", { alias: entry.alias }))}"
            title="${escapeHtml(aliasesText(state.config, "alias_promote_title", "Promote alias to canonical tag"))}"
          >
            →
          </button>
          <button
            type="button"
            class="${UI_CLASS.chipRemove}"
            data-delete-alias="${escapeHtml(entry.alias)}"
            aria-label="${escapeHtml(aliasesText(state.config, "alias_delete_aria_label", "Delete alias {alias}", { alias: entry.alias }))}"
            title="${escapeHtml(aliasesText(state.config, "alias_delete_title", "Delete alias"))}"
          >
            ×
          </button>
        </span>
      </div>
      <div class="${UI_CLASS.tagsCol}">
        <div class="${UI_CLASS.tagList}">
          ${sortedTargets.map((target) => renderAliasTargetChip(state, target)).join("")}
        </div>
      </div>
    </li>
  `;
}

function renderAliasTargetChip(state, target) {
  return `
    <span class="${classNames(UI_CLASS.chip, target.known ? chipGroupClass(target.group) : UI_CLASS.chipWarning)}" title="${escapeHtml(target.tagId)}">
      ${escapeHtml(String(target.label || "").toLowerCase())}
      ${target.known ? `
        <button
          type="button"
          class="${UI_CLASS.chipRemove}"
          data-demote-tag-id="${escapeHtml(target.tagId)}"
          title="${escapeHtml(aliasesText(state.config, "tag_demote_title", "Demote canonical tag to alias"))}"
          aria-label="${escapeHtml(aliasesText(state.config, "tag_demote_aria_label", "Demote {tag_id}", { tag_id: target.tagId }))}"
        >
          ←
        </button>
      ` : ""}
    </span>
  `;
}

function getStudioGroups(state) {
  return Array.isArray(state && state.studioGroups) && state.studioGroups.length
    ? state.studioGroups
    : DEFAULT_STUDIO_GROUPS;
}

function groupTitleAttr(state, group) {
  const description = String(state.groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state) {
  const title = aliasesText(state.config, "group_info_title", "Open group descriptions in a new tab");
  const ariaLabel = aliasesText(state.config, "group_info_aria_label", "Open group descriptions in a new tab");
  return `
    <a
      class="${classNames(UI_CLASS.keyPill, UI_CLASS.keyInfoButton)}"
      href="${escapeHtml(state.groupInfoPagePath || "/analytics/tag-groups/")}"
      target="_blank"
      rel="noopener noreferrer"
      title="${escapeHtml(title)}"
      aria-label="${escapeHtml(ariaLabel)}"
    >
      <em>i</em>
    </a>
  `;
}

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function stateAttr(stateValue) {
  return stateValue ? ` data-state="${escapeHtml(stateValue)}"` : "";
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
