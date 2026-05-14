export function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function renderStatusPillsMarkup(options) {
  var settings = options || {};
  var doc = settings.doc || {};
  var activeStatus = String(settings.activeStatus || "").trim();
  var canWrite = Boolean(settings.canWrite);
  var menuOpen = Boolean(settings.menuOpen);
  var text = settings.text || {};
  var formatText = typeof settings.formatText === "function"
    ? settings.formatText
    : function (template) { return String(template || ""); };
  var activeStatusConfig = settings.activeStatusConfig || null;
  var menuLabel = activeStatusConfig
    ? formatText(text.statusPillReadonlyLabel, { label: activeStatusConfig.label, title: doc.title })
    : text.statusMenuLabel;
  var menuItems = (settings.statuses || []).map(function (statusConfig) {
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

export function renderBookmarkRowsMarkup(bookmarks, options) {
  var settings = options || {};
  var selectedDocId = String(settings.selectedDocId || "");
  var editingBookmarkKey = String(settings.editingBookmarkKey || "");
  return (bookmarks || []).map(function (record) {
    var isActive = record.doc_id === selectedDocId;
    var isEditing = record.key === editingBookmarkKey;
    var pillClass = "docsViewer__bookmarkPill" + (isActive ? " is-active" : "");
    if (isEditing) {
      return (
        '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
          '<input class="docsViewer__bookmarkInput" type="text" value="' + escapeHtml(record.label || record.default_title || record.doc_id) + '" data-bookmark-input="' + escapeHtml(record.key) + '" aria-label="Rename bookmark">' +
          '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
        '</div>'
      );
    }
    return (
      '<div class="' + pillClass + '" data-bookmark-key="' + escapeHtml(record.key) + '">' +
        '<button type="button" class="docsViewer__bookmarkOpen" data-bookmark-open="' + escapeHtml(record.doc_id) + '" title="Open bookmark. Right-click to rename." aria-current="' + (isActive ? "page" : "false") + '">' +
          '<span class="docsViewer__bookmarkLabel">' + escapeHtml(record.label || record.default_title || record.doc_id) + '</span>' +
        '</button>' +
        '<button type="button" class="docsViewer__bookmarkRemove" data-bookmark-remove="' + escapeHtml(record.key) + '" aria-label="Remove bookmark">x</button>' +
      '</div>'
    );
  }).join("");
}

export function renderResultEntry(docId, title, metaText, href) {
  return (
    '<li class="docsViewer__resultItem">' +
      '<a class="docsViewer__resultTitle" href="' + escapeHtml(href) + '">' + escapeHtml(title) + '</a>' +
      (metaText ? '<p class="docsViewer__resultMeta">' + escapeHtml(metaText) + '</p>' : '') +
    '</li>'
  );
}

export function renderSearchEntry(entry, href) {
  var metaText = entry.displayMeta || [entry.lastUpdated, entry.parentTitle].filter(Boolean).join(" • ");
  return renderResultEntry(entry.id, entry.title, metaText, href);
}

export function renderRecentEntry(doc, metaText, href) {
  return renderResultEntry(doc.doc_id, doc.title, metaText, href);
}
