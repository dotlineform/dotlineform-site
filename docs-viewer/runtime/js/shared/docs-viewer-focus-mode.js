var NAVIGATION_KEYS = new Set([
  "Tab",
  "ArrowDown",
  "ArrowRight",
  "ArrowUp",
  "ArrowLeft",
  "Home",
  "End",
  "PageUp",
  "PageDown"
]);

/**
 * Install once for the viewer's page lifetime. Capture input before controls
 * move focus, including delayed modal/Back restoration. Only navigation keys
 * enable rings; pointer input clears them without changing actual focus.
 */
export function initDocsViewerFocusMode(root, documentRef) {
  delete root.dataset.keyboardNavigation;
  documentRef.addEventListener("pointerdown", function () {
    delete root.dataset.keyboardNavigation;
  }, true);
  documentRef.addEventListener("keydown", function (event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (NAVIGATION_KEYS.has(event.key)) root.dataset.keyboardNavigation = "true";
  }, true);
}
