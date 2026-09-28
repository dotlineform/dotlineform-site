function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

/** Catalogue images bind their visible text to one exact generated Work. */
export function catalogueImagePresentationHtml(options = {}) {
  var requestedIdPrefix = cleanString(options.idPrefix);
  var idPrefix = /^[A-Za-z][A-Za-z0-9_-]*$/.test(requestedIdPrefix)
    ? requestedIdPrefix
    : "docsViewerCatalogueImage";
  return "" +
    '<div class="docsViewer__field">' +
      '<span class="docsViewer__fieldLabel">Alt text from Work title</span>' +
      '<span data-role="catalogue-image-derived-alt">Choose a Work</span>' +
    "</div>" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="catalogue-image-title-caption" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Use Work title for caption</span>' +
    "</label>" +
    '<p class="muted small" data-role="catalogue-image-derived-caption">Choose a Work</p>' +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="catalogue-image-metadata" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Include Work metadata</span>' +
    "</label>" +
    '<label class="docsViewer__field docsViewer__field--textarea" for="' + idPrefix + 'Summary">' +
      '<span class="docsViewer__fieldLabel">Static summary (optional)</span>' +
      '<textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="' + idPrefix + 'Summary" data-role="catalogue-image-summary" rows="3"></textarea>' +
    "</label>" +
    '<div class="docsViewerSourceEditorMedia__placement" role="group" aria-labelledby="' + idPrefix + 'PlacementLabel">' +
      '<span class="docsViewer__fieldLabel" id="' + idPrefix + 'PlacementLabel">Placement</span>' +
      '<div class="docsViewerSourceEditorMedia__placementOptions">' +
        '<label class="docsViewerSourceEditorMedia__placementOption">' +
          '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="full" checked>' +
          '<span>Full column</span>' +
        "</label>" +
        '<label class="docsViewerSourceEditorMedia__placementOption">' +
          '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="left">' +
          '<span>Image left</span>' +
        "</label>" +
        '<label class="docsViewerSourceEditorMedia__placementOption">' +
          '<input class="docsViewerSourceEditorMedia__radioInput" data-role="catalogue-image-placement" type="radio" name="' + idPrefix + 'Placement" value="right">' +
          '<span>Image right</span>' +
        "</label>" +
      "</div>" +
    "</div>" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="catalogue-image-fill-width" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Fill available width</span>' +
    "</label>";
}

export function hydrateCatalogueImagePresentation(host, values = {}) {
  var placement = cleanString(values.placement);
  if (typeof values.useWorkTitleCaption !== "boolean"
    || typeof values.includeWorkMetadata !== "boolean"
    || typeof values.fillWidth !== "boolean"
    || !["full", "left", "right"].includes(placement)) {
    throw new Error("Catalogue image presentation is invalid.");
  }
  host.querySelector('[data-role="catalogue-image-title-caption"]').checked = values.useWorkTitleCaption;
  host.querySelector('[data-role="catalogue-image-metadata"]').checked = values.includeWorkMetadata;
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
    includeWorkMetadata: host.querySelector('[data-role="catalogue-image-metadata"]').checked,
    summary: host.querySelector('[data-role="catalogue-image-summary"]').value,
    placement: placement ? placement.value : "",
    fillWidth: host.querySelector('[data-role="catalogue-image-fill-width"]').checked
  };
}

export function bindCatalogueImageDerivedTitle(host) {
  var captionChoice = host.querySelector('[data-role="catalogue-image-title-caption"]');
  var alt = host.querySelector('[data-role="catalogue-image-derived-alt"]');
  var caption = host.querySelector('[data-role="catalogue-image-derived-caption"]');
  var title = "";
  function project() {
    alt.textContent = title || "Choose a Work";
    caption.textContent = !title ? "Choose a Work"
      : captionChoice.checked ? "Visible caption: " + title : "No visible Work-title caption";
  }
  captionChoice.addEventListener("change", project);
  project();
  return function (value) {
    title = cleanString(value);
    project();
  };
}
