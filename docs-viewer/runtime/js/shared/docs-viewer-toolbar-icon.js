/**
 * Create a decorative toolbar mask; its button owns the accessible name and state.
 * @param {Document} documentRef Document that owns the toolbar.
 * @param {string} artworkClass Exact maintained CSS class supplying the SVG mask image.
 * @returns {HTMLSpanElement} Icon span sized and tinted by shared toolbar CSS.
 */
export function createDocsViewerToolbarIcon(documentRef, artworkClass) {
  var icon = documentRef.createElement("span");
  icon.classList.add("docsViewer__toolbarIcon", artworkClass);
  icon.setAttribute("aria-hidden", "true");
  return icon;
}
