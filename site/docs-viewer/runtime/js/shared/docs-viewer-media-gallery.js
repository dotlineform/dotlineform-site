/** Gallery density has one owner for both page membership and rendered dimensions. */
export const DOCS_VIEWER_MEDIA_GALLERY_LAYOUT = Object.freeze({
  columns: 8,
  rows: 6,
  thumbnailSize: 64,
  gap: 8
});

/** Wrap the page index and slice a normalized gallery in its supplied order. Empty galleries stay at page zero. */
export function docsViewerMediaGalleryPage(gallery, pageIndex = 0) {
  if (!Number.isInteger(pageIndex)) throw new Error("Gallery page must be an integer.");
  var pageSize = DOCS_VIEWER_MEDIA_GALLERY_LAYOUT.columns * DOCS_VIEWER_MEDIA_GALLERY_LAYOUT.rows;
  var total = gallery.members.length;
  var pageCount = Math.ceil(total / pageSize);
  var index = pageCount ? ((pageIndex % pageCount) + pageCount) % pageCount : 0;
  var start = index * pageSize;
  var end = Math.min(start + pageSize, total);
  return { pageIndex: index, pageCount: pageCount, total: total, start: start, end: end,
    members: gallery.members.slice(start, end) };
}

/** Locate a Work in the explicit sequence, wrapping neighbours when more than one Work exists. */
export function docsViewerMediaGalleryPosition(gallery, target) {
  var index = gallery.members.findIndex(function (member) {
    return member.target.kind === target.kind && member.target.id === target.id;
  });
  if (index < 0) return null;
  var total = gallery.members.length;
  var pageSize = DOCS_VIEWER_MEDIA_GALLERY_LAYOUT.columns * DOCS_VIEWER_MEDIA_GALLERY_LAYOUT.rows;
  return { index: index, total: total, pageIndex: Math.floor(index / pageSize),
    previous: total > 1 ? gallery.members[(index + total - 1) % total].target : null,
    next: total > 1 ? gallery.members[(index + 1) % total].target : null };
}
