export function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * @typedef {Object} DocsViewerResultRow
 * @property {string} [galleryId] Exact Gallery ID for a Media View result.
 * @property {string} docId Exact document ID within the ordinary or named collection.
 * @property {string} collection Empty for an ordinary document.
 * @property {string} title Link label; titles are not identity.
 * @property {string} href Reader-owned route, including exact collection identity.
 * @property {string} iconUrl Loaded configured collection artwork, or empty for dlf-doc.
 */

/**
 * Compact decorative icon/title row carrying exact ordinary or collection document identity.
 * @param {DocsViewerResultRow} options Row presentation from already loaded inputs.
 */
export function renderResultEntry(options) {
  var title = '<span>' + escapeHtml(options.title) + '</span>';
  if (options.galleryId) {
    var galleryIcon = '<span class="docsViewer__listIcon docsViewer__icon--images" aria-hidden="true"></span>';
    return '<li class="docsViewer__resultItem"><button type="button" class="docsViewer__resultTitle" data-result-gallery-id="'
      + escapeHtml(options.galleryId) + '">' + galleryIcon + title + '</button></li>';
  }
  var icon = options.iconUrl
    ? '<span class="docsViewer__listIcon" aria-hidden="true" style="mask-image:url(&quot;' + escapeHtml(options.iconUrl) + '&quot;)"></span>'
    : '<span class="docsViewer__listIcon docsViewer__icon--dlf-doc" aria-hidden="true"></span>';
  return (
    '<li class="docsViewer__resultItem">' +
      '<a class="docsViewer__resultTitle" data-result-doc-id="' + escapeHtml(options.docId) +
      '" data-result-collection="' + escapeHtml(options.collection) + '" href="' + escapeHtml(options.href) + '">' +
      icon + title + '</a>' +
    '</li>'
  );
}
