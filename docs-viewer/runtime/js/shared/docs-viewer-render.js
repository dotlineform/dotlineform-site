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

/**
 * @typedef {Object} DocsViewerResultRow
 * @property {string} docId Exact document ID within the ordinary or named collection.
 * @property {string} collection Empty for an ordinary document.
 * @property {string} title Link label; titles are not identity.
 * @property {string} href Reader-owned route, including any collection subdoc.
 * @property {string} iconUrl Loaded configured collection artwork, or empty for dlf-doc.
 */

/**
 * Compact decorative icon/title row carrying exact ordinary or collection document identity.
 * @param {DocsViewerResultRow} options Row presentation from already loaded inputs.
 */
export function renderResultEntry(options) {
  var icon = options.iconUrl
    ? '<span class="docsViewer__listIcon" aria-hidden="true" style="mask-image:url(&quot;' + escapeHtml(options.iconUrl) + '&quot;)"></span>'
    : '<span class="docsViewer__listIcon docsViewer__icon--dlf-doc" aria-hidden="true"></span>';
  return (
    '<li class="docsViewer__resultItem">' +
      '<a class="docsViewer__resultTitle" data-result-doc-id="' + escapeHtml(options.docId) +
      '" data-result-collection="' + escapeHtml(options.collection) + '" href="' + escapeHtml(options.href) + '">' +
      icon + '<span>' + escapeHtml(options.title) + '</span></a>' +
    '</li>'
  );
}
