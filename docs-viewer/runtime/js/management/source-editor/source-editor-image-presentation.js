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
    : "docsViewerStagedMedia";
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="staged-media-caption" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Add caption</span>' +
    "</label>" +
    '<div class="docsViewerSourceEditorMedia__presentation" data-role="staged-media-presentation">' +
      '<label class="docsViewer__field" for="' + idPrefix + 'Caption">' +
        '<span class="docsViewer__fieldLabel">Caption</span>' +
        '<input class="docsViewer__fieldInput" id="' + idPrefix + 'Caption" data-role="staged-media-caption-text" type="text" required>' +
      "</label>" +
      '<label class="docsViewer__field docsViewer__field--textarea" for="' + idPrefix + 'Summary">' +
        '<span class="docsViewer__fieldLabel">Summary</span>' +
        '<textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="' + idPrefix + 'Summary" data-role="staged-media-summary" rows="3"></textarea>' +
      "</label>" +
      '<div class="docsViewerSourceEditorMedia__placement" role="group" aria-labelledby="' + idPrefix + 'PlacementLabel">' +
        '<span class="docsViewer__fieldLabel" id="' + idPrefix + 'PlacementLabel">Placement</span>' +
        '<div class="docsViewerSourceEditorMedia__placementOptions">' +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="' + idPrefix + 'Placement" value="full" checked>' +
            '<span>Full column</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="' + idPrefix + 'Placement" value="left">' +
            '<span>Image left</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="' + idPrefix + 'Placement" value="right">' +
            '<span>Image right</span>' +
          "</label>" +
        "</div>" +
      "</div>" +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" data-role="staged-media-fill-width" type="checkbox" checked>' +
        '<span class="docsViewer__fieldLabel">Fill available width</span>' +
      "</label>" +
    "</div>";
}

export function setImagePresentationEnabled(host, enabled) {
  var presentation = host && host.querySelector
    ? host.querySelector('[data-role="staged-media-presentation"]')
    : null;
  if (!presentation) return;
  presentation.hidden = !enabled;
  presentation.querySelectorAll("input, textarea").forEach(function (control) {
    control.disabled = !enabled;
  });
}

export function bindImagePresentation(host) {
  var captionToggle = host && host.querySelector
    ? host.querySelector('[data-role="staged-media-caption"]')
    : null;
  function project() {
    setImagePresentationEnabled(host, Boolean(captionToggle && captionToggle.checked));
  }
  if (captionToggle) captionToggle.addEventListener("change", project);
  project();
  return function () {
    if (captionToggle) captionToggle.removeEventListener("change", project);
  };
}

export function hydrateImagePresentation(host, values = {}) {
  var captionToggle = host.querySelector('[data-role="staged-media-caption"]');
  var captionInput = host.querySelector('[data-role="staged-media-caption-text"]');
  var summaryInput = host.querySelector('[data-role="staged-media-summary"]');
  var fillWidthInput = host.querySelector('[data-role="staged-media-fill-width"]');
  var placement = cleanString(values.placement) || "full";
  if (captionToggle) captionToggle.checked = booleanValue(values.addCaption, true);
  if (captionInput) captionInput.value = cleanString(values.caption);
  if (summaryInput) summaryInput.value = String(values.summary == null ? "" : values.summary).trim();
  if (fillWidthInput) fillWidthInput.checked = booleanValue(values.fillWidth, true);
  host.querySelectorAll('[data-role="staged-media-placement"]').forEach(function (input) {
    input.checked = input.value === placement;
  });
  setImagePresentationEnabled(host, Boolean(captionToggle && captionToggle.checked));
}

export function readImagePresentation(host) {
  var captionToggle = host.querySelector('[data-role="staged-media-caption"]');
  var captionInput = host.querySelector('[data-role="staged-media-caption-text"]');
  var summaryInput = host.querySelector('[data-role="staged-media-summary"]');
  var placementInput = host.querySelector('[data-role="staged-media-placement"]:checked');
  var fillWidthInput = host.querySelector('[data-role="staged-media-fill-width"]');
  return {
    addCaption: Boolean(captionToggle && captionToggle.checked),
    caption: cleanString(captionInput && captionInput.value),
    summary: String(summaryInput && summaryInput.value || "").trim(),
    placement: cleanString(placementInput && placementInput.value),
    fillWidth: Boolean(fillWidthInput && fillWidthInput.checked)
  };
}
