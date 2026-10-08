function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

/** Author the caption choice, summary and layout for one exact Work image. */
export function catalogueImagePresentationHtml(options = {}) {
  var requestedIdPrefix = cleanString(options.idPrefix);
  var idPrefix = /^[A-Za-z][A-Za-z0-9_-]*$/.test(requestedIdPrefix)
    ? requestedIdPrefix
    : "docsViewerCatalogueImage";
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="catalogue-image-title-caption" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Title caption</span>' +
    "</label>" +
    '<label class="docsViewer__field docsViewer__field--textarea" for="' + idPrefix + 'Summary">' +
      '<span class="docsViewer__fieldLabel">Summary</span>' +
      '<textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="' + idPrefix + 'Summary" data-role="catalogue-image-summary" rows="3"></textarea>' +
    "</label>" +
    '<div class="docsViewerSourceEditorMedia__placement" role="group" aria-labelledby="' + idPrefix + 'PlacementLabel">' +
      '<span class="docsViewer__fieldLabel" id="' + idPrefix + 'PlacementLabel">Layout</span>' +
      '<div class="docsViewerCatalogueImageModal__layoutControls">' +
        '<div class="docsViewerSourceEditorMedia__placementOptions" role="radiogroup" aria-labelledby="' + idPrefix + 'PlacementLabel">' +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="full" checked>' +
            '<span>Full</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="left">' +
            '<span>Left</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="right">' +
            '<span>Right</span>' +
          "</label>" +
        "</div>" +
        '<label class="docsViewer__field docsViewer__field--checkbox">' +
          '<input class="docsViewer__checkboxInput" data-role="catalogue-image-fill-width" type="checkbox" checked>' +
          '<span class="docsViewer__fieldLabel">Fill available width</span>' +
        "</label>" +
      "</div>" +
    "</div>";
}

export function hydrateCatalogueImagePresentation(host, values = {}) {
  var placement = cleanString(values.placement);
  if (typeof values.useWorkTitleCaption !== "boolean"
    || typeof values.fillWidth !== "boolean"
    || !["full", "left", "right"].includes(placement)) {
    throw new Error("Catalogue image presentation is invalid.");
  }
  host.querySelector('[data-role="catalogue-image-title-caption"]').checked = values.useWorkTitleCaption;
  host.querySelector('[data-role="catalogue-image-summary"]').value = String(values.summary == null ? "" : values.summary);
  host.querySelector('[data-role="catalogue-image-fill-width"]').checked = values.fillWidth;
  host.querySelectorAll('[data-role="catalogue-image-placement"]').forEach(function (input) {
    input.checked = input.value === placement;
  });
}

export function readCatalogueImagePresentation(host) {
  var placement = host.querySelector('[data-role="catalogue-image-placement"]:checked');
  return {
    useWorkTitleCaption: host.querySelector('[data-role="catalogue-image-title-caption"]').checked,
    summary: host.querySelector('[data-role="catalogue-image-summary"]').value,
    placement: placement ? placement.value : "",
    fillWidth: host.querySelector('[data-role="catalogue-image-fill-width"]').checked
  };
}
