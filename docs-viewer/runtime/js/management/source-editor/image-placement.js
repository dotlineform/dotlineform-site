export const IMAGE_PLACEMENTS = new Set(["full", "left", "right", "wrap-left", "wrap-right"]);

const PLACEMENT_INPUT = '[data-role="image-placement"]';
const WRAP_INPUT = '[data-role="image-wrap"]';

export function imageWrapCheckboxHtml({ tabStop = true } = {}) {
  return '<label class="docsViewer__field docsViewer__field--checkbox docsViewerSourceEditorMedia__wrap" hidden>' +
    '<input class="docsViewer__checkboxInput" data-role="image-wrap" type="checkbox"' + (tabStop ? "" : ' tabindex="-1"') + '>' +
    '<span class="docsViewer__fieldLabel">Wrap body text</span>' +
  "</label>";
}

/** Project the token placement into the two controls and track the selected side. */
export function mountImagePlacement(host, placement) {
  const wrap = placement.startsWith("wrap-");
  const side = wrap ? placement.slice(5) : placement;
  const wrapInput = host.querySelector(WRAP_INPUT);
  const wrapField = wrapInput.closest("label");
  wrapInput.checked = wrap;
  wrapField.hidden = side === "full";
  host.querySelectorAll(PLACEMENT_INPUT).forEach((input) => {
    input.checked = input.value === side;
    input.addEventListener("change", () => {
      wrapField.hidden = input.value === "full";
    });
  });
}

export function readImagePlacement(host) {
  const side = host.querySelector(PLACEMENT_INPUT + ":checked")?.value || "";
  return side && side !== "full" && host.querySelector(WRAP_INPUT).checked ? "wrap-" + side : side;
}
