import {
  escapeHtml
} from "../shared/docs-viewer-render.js";

export function renderMetadataParentPopupMarkup(matches, options) {
  var settings = options || {};
  var records = Array.isArray(matches) ? matches : [];
  if (!records.length) {
    return '<p class="docsViewer__parentPopupEmpty">' + escapeHtml(settings.emptyText || "") + "</p>";
  }
  var optionTitle = typeof settings.optionTitle === "function"
    ? settings.optionTitle
    : function (option) { return String(option && option.label || ""); };
  return records.map(function (option, index) {
    var optionId = "docsViewerMetadataParentOption-" + index;
    var title = optionTitle(option);
    var isActive = index === 0;
    return (
      '<button type="button" class="docsViewer__parentOption' + (isActive ? " is-active" : "") + '" ' +
        'id="' + optionId + '" role="option" aria-selected="' + (isActive ? "true" : "false") + '" ' +
        'tabindex="-1" data-parent-index="' + index + '">' +
        '<span class="docsViewer__parentOptionTitle">' + escapeHtml(title) + "</span>" +
      "</button>"
    );
  }).join("");
}

export function renderMetadataStatusOptionsMarkup(options, selectedValue, selectedSuffix) {
  var selected = String(selectedValue || "");
  return (options || []).map(function (option) {
    var isSelected = option.value === selected;
    var selectedAttr = isSelected ? " selected" : "";
    var label = option.label + (isSelected ? String(selectedSuffix || "") : "");
    return '<option value="' + escapeHtml(option.value) + '"' + selectedAttr + ">" + escapeHtml(label) + "</option>";
  }).join("");
}

export function renderSettingsWarningsMarkup(warnings) {
  var items = Array.isArray(warnings) ? warnings.filter(Boolean) : [];
  return items.length
    ? '<ul>' + items.map(function (item) {
      return '<li>' + escapeHtml(item) + '</li>';
    }).join("") + '</ul>'
    : "";
}
