import { IMAGE_PLACEMENTS, imageWrapCheckboxHtml, mountImagePlacement, readImagePlacement } from "./image-placement.js";

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
      '<input class="docsViewer__checkboxInput" data-role="catalogue-image-title-caption" type="checkbox" tabindex="-1" checked>' +
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
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="full" tabindex="-1" checked>' +
            '<span>Full</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="left" tabindex="-1">' +
            '<span>Left</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="right" tabindex="-1">' +
            '<span>Right</span>' +
          "</label>" +
        "</div>" +
        '<label class="docsViewer__field docsViewer__field--checkbox">' +
          '<input class="docsViewer__checkboxInput" data-role="catalogue-image-fill-width" type="checkbox" tabindex="-1" checked>' +
          '<span class="docsViewer__fieldLabel">Fill available width</span>' +
        "</label>" +
      "</div>" +
      '<label class="docsViewer__field docsViewer__field--compactLabel docsViewerCatalogueImageModal__leftSize" hidden>' +
        '<span class="docsViewer__fieldLabel">Image width</span>' +
        '<select class="docsViewer__fieldInput" data-role="catalogue-image-left-size" tabindex="-1">' +
          '<option value="">50%</option>' +
          '<option value="third">33%</option>' +
          '<option value="thumbnail">Thumbnail</option>' +
        "</select>" +
      "</label>" +
      imageWrapCheckboxHtml({ tabStop: false }) +
    "</div>";
}

export function hydrateCatalogueImagePresentation(host, values = {}) {
  var placement = cleanString(values.placement);
  if (typeof values.useWorkTitleCaption !== "boolean"
    || typeof values.fillWidth !== "boolean"
    || !IMAGE_PLACEMENTS.has(placement)) {
    throw new Error("Catalogue image presentation is invalid.");
  }
  host.querySelector('[data-role="catalogue-image-title-caption"]').checked = values.useWorkTitleCaption;
  host.querySelector('[data-role="catalogue-image-summary"]').value = String(values.summary == null ? "" : values.summary);
  var fillWidth = host.querySelector('[data-role="catalogue-image-fill-width"]');
  var leftSize = host.querySelector('[data-role="catalogue-image-left-size"]');
  var sizeField = leftSize.closest("label");
  var fillField = fillWidth.closest("label");
  fillWidth.checked = values.leftSize === "thumbnail" || values.fillWidth;
  leftSize.value = values.leftSize || "";
  function projectFillWidth() {
    fillField.hidden = !sizeField.hidden && leftSize.value === "thumbnail";
  }
  mountImagePlacement(host, placement, function (side) {
    sizeField.hidden = side !== "left";
    projectFillWidth();
  });
  leftSize.addEventListener("change", projectFillWidth);
}

export function readCatalogueImagePresentation(host) {
  var placement = readImagePlacement(host);
  var leftSize = placement === "left" || placement === "wrap-left"
    ? host.querySelector('[data-role="catalogue-image-left-size"]').value : "";
  return {
    useWorkTitleCaption: host.querySelector('[data-role="catalogue-image-title-caption"]').checked,
    summary: host.querySelector('[data-role="catalogue-image-summary"]').value,
    placement: placement,
    fillWidth: leftSize !== "thumbnail" && host.querySelector('[data-role="catalogue-image-fill-width"]').checked,
    leftSize: leftSize
  };
}
