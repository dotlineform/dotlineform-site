import {
  getStudioText
} from "./studio-config.js";
import {
  countTagsByGroup,
  formatTimestampMinute,
  getVisibleSortedTags
} from "./tag-registry-domain.js";
import {
  tagRegistryUi
} from "./tag-ui.js";
import {
  tagRegistryDocumentHref
} from "./tag-registry-documents.js";

const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const UI = tagRegistryUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

export function renderTagRegistryControls(state) {
  const studioGroups = getStudioGroups(state);
  const groupCounts = countTagsByGroup(state.tags);
  const totalCount = state.tags.length;
  const allTagsLabel = registryText(state.config, "all_tags_filter", "All tags [{count}]", { count: totalCount });
  const groupButtons = studioGroups.map((group) => {
    const count = Number(groupCounts[group] || 0);
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
    <button type="button" class="studioUi__button ${UI_CLASS.allFilterButton}" data-group="all"${stateAttr(state.filterGroup === "all" ? UI_STATE.active : "")}>${escapeHtml(allTagsLabel)}</button>
    ${groupButtons}
  `;
}

export function renderTagRegistryList(state) {
  const visible = getVisibleSortedTags(state);
  const tagHeading = registryText(state.config, "table_heading_tag", "tag");
  const documentsHeading = registryText(state.config, "table_heading_documents", "documents");
  const updatedHeading = registryText(state.config, "table_heading_updated", "updated");
  const headerHtml = `
    <div class="${UI_CLASS.listHead}">
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="tag"${stateAttr(state.sortKey === "tag" ? UI_STATE.active : "")}>
        ${escapeHtml(tagHeading)}${sortIndicator(state, "tag")}
      </button>
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="documents"${stateAttr(state.sortKey === "documents" ? UI_STATE.active : "")}>
        ${escapeHtml(documentsHeading)}${sortIndicator(state, "documents")}
      </button>
      <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="updated"${stateAttr(state.sortKey === "updated" ? UI_STATE.active : "")}>
        ${escapeHtml(updatedHeading)}${sortIndicator(state, "updated")}
      </button>
    </div>
  `;

  if (!visible.length) {
    state.refs.list.innerHTML = `${headerHtml}<p class="${UI_CLASS.empty}">${escapeHtml(registryText(state.config, "empty_state", "none"))}</p>`;
    return;
  }

  state.refs.list.innerHTML = `
    ${headerHtml}
    <ul class="${UI_CLASS.listRows}">
      ${visible.map((tag) => renderTagRow(state, tag)).join("")}
    </ul>
  `;
}

export function renderTagRegistryError(state, message) {
  state.mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(message)}</div>`;
}

function renderTagRow(state, tag) {
  return `
    <li class="${UI_CLASS.listRow}">
      <div class="${UI_CLASS.tagCol}">
        <div class="${UI_CLASS.tagActions}">
          <span class="${classNames(UI_CLASS.chip, chipGroupClass(tag.group), UI_CLASS.tagChip)}" title="${escapeHtml(tag.tagId)}">
            <button type="button" class="${UI_CLASS.tagInlineButton}" data-tag-id="${escapeHtml(tag.tagId)}" aria-label="${escapeHtml(registryText(state.config, "tag_edit_aria_label", "Edit {tag_id}", { tag_id: tag.tagId }))}">
              ${escapeHtml(tag.tagId)}
            </button>
            <button
              type="button"
              class="${classNames(UI_CLASS.chipRemove, UI_CLASS.demoteButton)}"
              data-demote-tag-id="${escapeHtml(tag.tagId)}"
              title="${escapeHtml(registryText(state.config, "tag_demote_title", "Demote canonical tag to alias"))}"
              aria-label="${escapeHtml(registryText(state.config, "tag_demote_aria_label", "Demote {tag_id}", { tag_id: tag.tagId }))}"
            >
              ←
            </button>
            <button
              type="button"
              class="${UI_CLASS.chipRemove}"
              data-delete-tag-id="${escapeHtml(tag.tagId)}"
              title="${escapeHtml(registryText(state.config, "tag_delete_title", "Delete canonical tag"))}"
              aria-label="${escapeHtml(registryText(state.config, "tag_delete_aria_label", "Delete {tag_id}", { tag_id: tag.tagId }))}"
            >
              ×
            </button>
          </span>
        </div>
      </div>
      <div class="${UI_CLASS.documentsCol}">
        ${renderDocumentLinks(state, tag)}
      </div>
      <div class="${UI_CLASS.updatedCol}">
        ${escapeHtml(formatTimestampMinute(tag.updatedAtUtc) || "—")}
      </div>
    </li>
  `;
}

function renderDocumentLinks(state, tag) {
  const documents = Array.isArray(tag && tag.documents) ? tag.documents : [];
  if (!documents.length) return "—";
  return `<span class="${UI_CLASS.documentLinks}">${documents.map((record) => `
    <a
      class="${UI_CLASS.documentLink}"
      href="${escapeHtml(tagRegistryDocumentHref(state.config, record.url))}"
      target="_blank"
      rel="noopener noreferrer"
    >${escapeHtml(record.document_title || registryText(state.config, "unavailable_document", "Unavailable document"))}</a>
  `).join(", ")}</span>`;
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

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "asc" ? " ↑" : " ↓";
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
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
