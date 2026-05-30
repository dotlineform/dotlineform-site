import {
  getAnalyticsText
} from "./analytics-config.js";
import {
  normalize
} from "./tag-studio-domain.js";
import {
  seriesTagEditorUi
} from "./analytics-ui.js";

const POPUP_TAG_MATCH_CAP = 12;
const POPUP_ALIAS_MATCH_CAP = 12;
const POPUP_WORK_MATCH_CAP = 12;
const UI = seriesTagEditorUi;
const { className: UI_CLASS } = UI;

export function renderWorkPopup(state) {
  const queryRaw = String(state.refs.workInput.value || "").trim();
  if (!queryRaw) {
    hideWorkPopup(state);
    return;
  }

  const matches = getMatchingWorkOptions(state, queryRaw).slice(0, POPUP_WORK_MATCH_CAP);
  if (!matches.length) {
    hideWorkPopup(state);
    return;
  }

  state.refs.workPopupList.innerHTML = `
    <div class="${UI_CLASS.suggest}">
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_works", "works"))}</p>
        <div class="${UI_CLASS.suggestWorkRows}">
          ${matches.map((item) => `
            <button type="button" class="${UI_CLASS.suggestWorkButton}" data-popup-work-id="${escapeHtml(item.workId)}">
              <span class="${UI_CLASS.suggestWorkId}">${escapeHtml(item.workId)}</span>
              <span class="${UI_CLASS.suggestWorkTitle}">${escapeHtml(item.title || "")}</span>
            </button>
          `).join("")}
        </div>
      </section>
    </div>
  `;
  state.refs.workPopup.hidden = false;
}

export function hideWorkPopup(state) {
  state.refs.workPopup.hidden = true;
  state.refs.workPopupList.innerHTML = "";
}

export function getMatchingWorkOptions(state, query) {
  const normalizedQuery = normalize(query);
  if (!normalizedQuery) return [];
  return state.seriesWorkOptions.filter((item) => {
    if (item.workId.startsWith(normalizedQuery)) return true;
    if (item.shortWorkId.startsWith(normalizedQuery)) return true;
    return item.titleKey.startsWith(normalizedQuery);
  });
}

export function renderPopup(state) {
  const query = normalize(state.refs.input.value);
  if (!query) {
    hidePopup(state);
    return;
  }

  const selectedTagIds = getEditableTagIdSet(state);
  const inheritedTagIds = getSeriesTagIdSet(state);
  const tagMatches = state.activeTagsBySlug
    .filter((tag) => {
      if (!tag.slug.startsWith(query)) return false;
      if (selectedTagIds.has(tag.tag_id)) return false;
      if (state.selectedWorkId && inheritedTagIds.has(tag.tag_id)) return false;
      return true;
    })
    .slice(0, POPUP_TAG_MATCH_CAP);
  const aliasMatches = getPopupAliasMatches(state, query, selectedTagIds, state.selectedWorkId ? inheritedTagIds : new Set()).slice(0, POPUP_ALIAS_MATCH_CAP);

  if (!tagMatches.length && !aliasMatches.length) {
    hidePopup(state);
    return;
  }

  const tagSection = tagMatches.length
    ? `
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_tags", "tags"))}</p>
        <div class="${UI_CLASS.suggestTagRows}">
          ${tagMatches.map((tag) => `
            <button
              type="button"
              class="${classNames(UI_CLASS.popupPill, chipGroupClass(tag.group))}"
              data-popup-tag-id="${escapeHtml(tag.tag_id)}"
              title="${escapeHtml(tag.tag_id)}"
            >
              ${escapeHtml(tag.label)}
            </button>
          `).join("")}
        </div>
      </section>
    `
    : "";

  const aliasSection = aliasMatches.length
    ? `
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_aliases", "aliases"))}</p>
        <div class="${UI_CLASS.suggestAliasRows}">
          ${aliasMatches.map((entry) => `
            <div class="${UI_CLASS.suggestAliasRow}">
              <span
                class="${classNames(UI_CLASS.popupPill, UI_CLASS.suggestAliasPill)}"
                data-popup-alias="${escapeHtml(entry.alias)}"
                title="${escapeHtml(entry.alias)}"
              >
                ${escapeHtml(entry.alias)}
              </span>
              <div class="${UI_CLASS.suggestAliasTargets}">
                ${entry.targets.map((target) => `
                  <button
                    type="button"
                    class="${classNames(UI_CLASS.popupPill, chipGroupClass(target.group), UI_CLASS.suggestAliasTarget)}"
                    data-popup-alias-target="${escapeHtml(target.tagId)}"
                    data-popup-alias-source="${escapeHtml(entry.alias)}"
                    title="${escapeHtml(target.tagId)}"
                  >
                    ${escapeHtml(target.label)}
                  </button>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </section>
    `
    : "";

  state.refs.popupList.innerHTML = `
    <div class="${UI_CLASS.suggest}">
      ${tagSection}
      ${aliasSection}
    </div>
  `;
  state.refs.popup.hidden = false;
}

export function hidePopup(state) {
  state.refs.popup.hidden = true;
  state.refs.popupList.innerHTML = "";
}

function getPopupAliasMatches(state, query, selectedTagIds, inheritedTagIds) {
  return state.aliasOptions
    .filter((entry) => entry.alias.startsWith(query))
    .map((entry) => ({
      alias: entry.alias,
      targets: entry.targets.filter((target) => !selectedTagIds.has(target.tagId) && !inheritedTagIds.has(target.tagId))
    }))
    .filter((entry) => entry.targets.length > 0);
}

function getEditableTagIdSet(state) {
  const out = new Set();
  for (const entry of getEditableEntries(state)) {
    out.add(entry.canonicalId);
  }
  return out;
}

function getEditableEntries(state) {
  if (!state.selectedWorkId) return state.seriesEntries;
  return state.workEntriesById.get(state.selectedWorkId) || [];
}

function getSeriesTagIdSet(state) {
  const out = new Set();
  for (const entry of state.seriesEntries) {
    out.add(entry.canonicalId);
  }
  return out;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function studioText(config, key, fallback, tokens) {
  return getAnalyticsText(config, `series_tag_editor.${key}`, fallback, tokens);
}
