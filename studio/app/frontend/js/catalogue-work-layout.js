/** Own panel presentation without rebuilding the member list or changing the Work draft.
 * Expansion lasts for this page session; record changes only update preview availability.
 * @param {{ root: HTMLElement, listExpandButton: HTMLButtonElement, summaryPanelNode: HTMLElement }} elements
 * @param {(change: () => void) => void} preserveListAnchor Apply layout with the list's visible row retained.
 */
export function createWorkEditorLayout({ root, listExpandButton, summaryPanelNode }, preserveListAnchor) {
  let expanded = false;
  let previewAvailable = false;
  const indicator = listExpandButton.querySelector("span");

  function render() {
    root.dataset.workLayout = expanded ? "expanded-list" : previewAvailable ? "standard" : "without-preview";
    summaryPanelNode.hidden = expanded || !previewAvailable;
    indicator.textContent = expanded ? "<" : ">";
    const label = expanded ? "Restore normal panel layout" : "Expand member works list";
    listExpandButton.title = label;
    listExpandButton.setAttribute("aria-label", label);
    listExpandButton.setAttribute("aria-expanded", String(expanded));
  }

  listExpandButton.addEventListener("click", () => {
    expanded = !expanded;
    preserveListAnchor(render);
  });
  render();

  return {
    setPreviewAvailable(available) {
      previewAvailable = Boolean(available);
      render();
    }
  };
}
