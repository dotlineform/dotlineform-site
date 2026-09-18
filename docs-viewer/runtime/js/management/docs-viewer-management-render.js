import {
  escapeHtml
} from "../shared/docs-viewer-render.js";

export function renderSettingsWarningsMarkup(warnings) {
  var items = Array.isArray(warnings) ? warnings.filter(Boolean) : [];
  return items.length
    ? '<ul>' + items.map(function (item) {
      return '<li>' + escapeHtml(item) + '</li>';
    }).join("") + '</ul>'
    : "";
}
