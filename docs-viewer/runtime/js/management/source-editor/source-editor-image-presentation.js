import { imageWrapCheckboxHtml, mountImagePlacement, readImagePlacement } from "./image-placement.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function booleanValue(value, fallback) {
  return typeof value === "boolean" ? value : fallback;
}

export function imagePresentationHtml(options = {}) {
  var requestedIdPrefix = cleanString(options.idPrefix);
  var idPrefix = /^[A-Za-z][A-Za-z0-9_-]*$/.test(requestedIdPrefix)
    ? requestedIdPrefix
    : "docsViewerSourceMedia";
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="media-caption" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Add caption</span>' +
    "</label>" +
    '<div class="docsViewerSourceEditorMedia__presentation" data-role="media-presentation">' +
      '<label class="docsViewer__field" for="' + idPrefix + 'Caption">' +
        '<span class="docsViewer__fieldLabel">Caption</span>' +
        '<input class="docsViewer__fieldInput" id="' + idPrefix + 'Caption" data-role="media-caption-text" type="text" required>' +
      "</label>" +
    "</div>" +
      '<label class="docsViewer__field docsViewer__field--textarea" for="' + idPrefix + 'Summary">' +
        '<span class="docsViewer__fieldLabel">Summary</span>' +
        '<textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="' + idPrefix + 'Summary" data-role="media-summary" rows="3"></textarea>' +
      "</label>" +
      '<div class="docsViewerSourceEditorMedia__placement" role="group" aria-labelledby="' + idPrefix + 'PlacementLabel">' +
        '<span class="docsViewer__fieldLabel" id="' + idPrefix + 'PlacementLabel">Placement</span>' +
        '<div class="docsViewerSourceEditorMedia__placementOptions">' +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="full" checked>' +
            '<span>Full column</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="left">' +
            '<span>Image left</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="image-placement" type="radio" name="' + idPrefix + 'Placement" value="right">' +
            '<span>Image right</span>' +
          "</label>" +
        "</div>" +
        imageWrapCheckboxHtml() +
      "</div>" +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" data-role="media-fill-width" type="checkbox" checked>' +
        '<span class="docsViewer__fieldLabel">Fill available width</span>' +
      "</label>";
}

export function mountImagePresentation(host, values = {}) {
  var captionToggle = host.querySelector('[data-role="media-caption"]');
  var captionInput = host.querySelector('[data-role="media-caption-text"]');
  var captionField = host.querySelector('[data-role="media-presentation"]');
  var summaryInput = host.querySelector('[data-role="media-summary"]');
  var fillWidthInput = host.querySelector('[data-role="media-fill-width"]');
  captionToggle.checked = booleanValue(values.addCaption, true);
  captionInput.value = cleanString(values.caption);
  summaryInput.value = String(values.summary == null ? "" : values.summary).trim();
  fillWidthInput.checked = booleanValue(values.fillWidth, true);
  mountImagePlacement(host, cleanString(values.placement) || "full");

  function projectCaption() {
    captionField.hidden = captionInput.disabled = !captionToggle.checked;
  }
  captionToggle.addEventListener("change", projectCaption);
  projectCaption();
}

export function readImagePresentation(host) {
  var captionToggle = host.querySelector('[data-role="media-caption"]');
  var captionInput = host.querySelector('[data-role="media-caption-text"]');
  var summaryInput = host.querySelector('[data-role="media-summary"]');
  var fillWidthInput = host.querySelector('[data-role="media-fill-width"]');
  return {
    addCaption: captionToggle.checked,
    caption: captionInput.value.trim(),
    summary: summaryInput.value.trim(),
    placement: readImagePlacement(host),
    fillWidth: fillWidthInput.checked
  };
}
