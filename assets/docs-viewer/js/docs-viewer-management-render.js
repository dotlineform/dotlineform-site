import {
  escapeHtml
} from "./docs-viewer-render.js";

export function renderStatusPillsMarkup(options) {
  var settings = options || {};
  var doc = settings.doc || {};
  var activeStatus = String(settings.activeStatus || "").trim();
  var canWrite = Boolean(settings.canWrite);
  var menuOpen = Boolean(settings.menuOpen);
  var text = settings.text || {};
  var statuses = Array.isArray(settings.statuses) ? settings.statuses : [];
  var formatText = typeof settings.formatText === "function"
    ? settings.formatText
    : function (template) { return String(template || ""); };
  var activeStatusConfig = settings.activeStatusConfig || null;
  var menuLabel = activeStatusConfig
    ? formatText(text.statusPillReadonlyLabel, { label: activeStatusConfig.label, title: doc.title })
    : text.statusMenuLabel;
  var menuItems = statuses.map(function (statusConfig) {
    var selected = statusConfig.ui_status === activeStatus;
    var labelTemplate = canWrite
      ? (selected ? text.statusPillClearLabel : text.statusPillSetLabel)
      : text.statusPillReadonlyLabel;
    var label = formatText(labelTemplate, { label: statusConfig.label, title: doc.title });
    var className = "docsViewer__statusMenuItem" + (selected ? " is-active" : "");
    return (
      '<button type="button" role="menuitemradio" class="' + className + '" data-ui-status="' + escapeHtml(statusConfig.ui_status) + '" aria-checked="' + (selected ? "true" : "false") + '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(label) + '"' + (canWrite ? "" : " disabled") + '>' +
        '<span class="docsViewer__statusPillEmoji" aria-hidden="true">' + escapeHtml(statusConfig.emoji) + '</span>' +
        '<span class="visually-hidden">' + escapeHtml(statusConfig.label) + '</span>' +
      '</button>'
    );
  }).join("");
  return (
    '<button type="button" class="docsViewer__statusMenuToggle" data-ui-status-menu-toggle="true" aria-expanded="' + (menuOpen ? "true" : "false") + '" aria-label="' + escapeHtml(menuLabel) + '" title="' + escapeHtml(menuLabel) + '"' + (canWrite ? "" : " disabled") + '>🏷️</button>' +
    '<div class="docsViewer__statusMenu" role="menu"' + (menuOpen && canWrite ? "" : " hidden") + ">" +
      menuItems +
    "</div>"
  );
}

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
        'data-parent-index="' + index + '">' +
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
