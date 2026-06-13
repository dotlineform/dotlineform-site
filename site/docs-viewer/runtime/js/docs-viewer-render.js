export function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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
