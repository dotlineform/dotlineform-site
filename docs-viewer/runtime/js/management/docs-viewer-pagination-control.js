import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

/**
 * Mount a local pagination button; the report owns mode changes and rendering.
 * @param {Object} options
 * @param {HTMLElement} options.host Toolbar that receives the button.
 * @param {boolean} options.enabled Initial pagination mode.
 * @param {string} options.itemsLabel Plural item name for the accessible label.
 * @param {function(boolean): void} options.change Request a new pagination mode.
 * @returns {{button: HTMLButtonElement, update: function(boolean): void}}
 */
export function mountDocsViewerPaginationControl({ host, enabled, itemsLabel, change }) {
  const button = host.ownerDocument.createElement("button");
  button.type = "button";
  button.className = "docsViewer__toolbarIconButton";
  const icon = createDocsViewerToolbarIcon(host.ownerDocument, "docsViewer__icon--dlf-paginate-off");
  button.appendChild(icon);
  let pagination = enabled;
  button.addEventListener("click", () => change(!pagination));
  const control = {
    button,
    update(value) {
      pagination = value;
      icon.classList.toggle("docsViewer__icon--dlf-paginate-on", value);
      icon.classList.toggle("docsViewer__icon--dlf-paginate-off", !value);
      button.setAttribute("aria-pressed", String(value));
      button.title = value ? "Pagination on. Show all " + itemsLabel + "." : "Pagination off. Show pages.";
      button.setAttribute("aria-label", button.title);
    }
  };
  control.update(enabled);
  host.appendChild(button);
  return control;
}
