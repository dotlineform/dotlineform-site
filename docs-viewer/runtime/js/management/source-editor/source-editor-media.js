import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function actionCopy(kind) {
  return kind === "file"
    ? { title: "Add file", fieldLabel: "Link label", empty: "No staged files are available.", primary: "Add file" }
    : { title: "Add image", fieldLabel: "Alt text", empty: "No staged images are available.", primary: "Add image" };
}

function imagePresentationHtml() {
  return "" +
    '<label class="docsViewer__field docsViewer__field--checkbox">' +
      '<input class="docsViewer__checkboxInput" data-role="staged-media-caption" type="checkbox" checked>' +
      '<span class="docsViewer__fieldLabel">Add caption</span>' +
    "</label>" +
    '<div class="docsViewerSourceEditorMedia__presentation" data-role="staged-media-presentation">' +
      '<label class="docsViewer__field" for="docsViewerStagedMediaCaption">' +
        '<span class="docsViewer__fieldLabel">Caption</span>' +
        '<input class="docsViewer__fieldInput" id="docsViewerStagedMediaCaption" data-role="staged-media-caption-text" type="text" required>' +
      "</label>" +
      '<label class="docsViewer__field docsViewer__field--textarea" for="docsViewerStagedMediaSummary">' +
        '<span class="docsViewer__fieldLabel">Summary</span>' +
        '<textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="docsViewerStagedMediaSummary" data-role="staged-media-summary" rows="3"></textarea>' +
      "</label>" +
      '<div class="docsViewerSourceEditorMedia__placement" role="group" aria-labelledby="docsViewerStagedMediaPlacementLabel">' +
        '<span class="docsViewer__fieldLabel" id="docsViewerStagedMediaPlacementLabel">Placement</span>' +
        '<div class="docsViewerSourceEditorMedia__placementOptions">' +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="docsViewerStagedMediaPlacement" value="full" checked>' +
            '<span>Full column</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="docsViewerStagedMediaPlacement" value="left">' +
            '<span>Image left</span>' +
          "</label>" +
          '<label class="docsViewerSourceEditorMedia__placementOption">' +
            '<input class="docsViewerSourceEditorMedia__radioInput" data-role="staged-media-placement" type="radio" name="docsViewerStagedMediaPlacement" value="right">' +
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

function setImagePresentationEnabled(host, enabled) {
  var presentation = host.querySelector('[data-role="staged-media-presentation"]');
  if (!presentation) return;
  presentation.hidden = !enabled;
  presentation.querySelectorAll("input, textarea").forEach(function (control) {
    control.disabled = !enabled;
  });
}

function chooseStagedMedia(root, kind, files) {
  var copy = actionCopy(kind);
  var records = Array.isArray(files) ? files : [];
  if (!records.length) return Promise.resolve(null);
  var optionsHtml = records.map(function (file) {
    return '<option value="' + escapeHtml(file.filename) + '">' + escapeHtml(file.filename) + "</option>";
  }).join("");
  var captionHtml = kind === "image" ? imagePresentationHtml() : "";
  return openDocsViewerManagementModal({
    root: root,
    title: copy.title,
    size: "compact",
    focusSelector: '[data-role="staged-media-file"]',
    bodyHtml: "" +
      '<div class="docsViewer__field">' +
        '<label class="docsViewer__fieldLabel" for="docsViewerStagedMediaFile">Staged file</label>' +
        '<select class="docsViewer__fieldInput" id="docsViewerStagedMediaFile" data-role="staged-media-file">' + optionsHtml + "</select>" +
      "</div>" +
      '<div class="docsViewer__field">' +
        '<label class="docsViewer__fieldLabel" for="docsViewerStagedMediaLabel">' + escapeHtml(copy.fieldLabel) + "</label>" +
        '<input class="docsViewer__fieldInput" id="docsViewerStagedMediaLabel" data-role="staged-media-label" type="text" required>' +
      "</div>" +
      captionHtml,
    actions: [
      { role: "modal-primary", label: copy.primary },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var select = api.host.querySelector('[data-role="staged-media-file"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var captionToggle = api.host.querySelector('[data-role="staged-media-caption"]');
      var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
      var captionEdited = false;
      function projectSuggestedLabel() {
        var selected = records.find(function (record) { return record.filename === select.value; });
        label.value = cleanString(selected && selected.suggested_label);
        if (captionInput) {
          captionInput.value = label.value;
          captionEdited = false;
        }
      }
      function projectCaptionSuggestion() {
        if (captionInput && !captionEdited) captionInput.value = label.value;
      }
      function projectCaptionAvailability() {
        setImagePresentationEnabled(api.host, Boolean(captionToggle && captionToggle.checked));
      }
      select.addEventListener("change", projectSuggestedLabel);
      label.addEventListener("input", projectCaptionSuggestion);
      if (captionInput) {
        captionInput.addEventListener("input", function () {
          captionEdited = true;
        });
      }
      if (captionToggle) captionToggle.addEventListener("change", projectCaptionAvailability);
      projectSuggestedLabel();
      projectCaptionAvailability();
    },
    onSubmit: function (api) {
      var select = api.host.querySelector('[data-role="staged-media-file"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var captionToggle = api.host.querySelector('[data-role="staged-media-caption"]');
      var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
      var summaryInput = api.host.querySelector('[data-role="staged-media-summary"]');
      var placementInput = api.host.querySelector('[data-role="staged-media-placement"]:checked');
      var fillWidthInput = api.host.querySelector('[data-role="staged-media-fill-width"]');
      var filename = cleanString(select && select.value);
      var labelValue = cleanString(label && label.value);
      var addCaption = Boolean(captionToggle && captionToggle.checked);
      var captionValue = cleanString(captionInput && captionInput.value);
      var summaryValue = cleanString(summaryInput && summaryInput.value);
      var placementValue = cleanString(placementInput && placementInput.value);
      var fillWidth = Boolean(fillWidthInput && fillWidthInput.checked);
      if (!filename || !labelValue) {
        api.setStatus("Choose a staged file and enter " + copy.fieldLabel.toLowerCase() + ".");
        return false;
      }
      if (addCaption && !captionValue) {
        api.setStatus("Enter caption text or turn off Add caption.");
        if (captionInput) captionInput.focus();
        return false;
      }
      if (addCaption && !placementValue) {
        api.setStatus("Choose an image placement.");
        return false;
      }
      return {
        confirmed: true,
        stagedFilename: filename,
        label: labelValue,
        addCaption: addCaption,
        caption: captionValue,
        summary: summaryValue,
        placement: placementValue,
        fillWidth: fillWidth
      };
    }
  }).then(function (result) {
    return result && result.confirmed ? result : null;
  });
}

function confirmStagedMedia(root, kind, preview) {
  var copy = actionCopy(kind);
  var collision = cleanString(preview && preview.collision);
  var diagnostics = preview && preview.svg && preview.svg.diagnostics;
  var warnings = diagnostics && Array.isArray(diagnostics.warnings) ? diagnostics.warnings : [];
  if (collision !== "replace" && !warnings.length) return Promise.resolve(true);
  var reviewHtml = collision === "replace"
    ? ""
    : '<p class="docsViewer__modalNote muted small">SVG sanitization changed the staged source. Review the diagnostics before adding it.</p>';
  var warningHtml = warnings.map(function (warning) {
    return '<p class="docsViewer__modalNote muted small">' + escapeHtml(warning) + "</p>";
  }).join("");
  return openDocsViewerManagementModal({
    root: root,
    title: collision === "replace" ? "Replace " + kind : "Review " + kind,
    size: "compact",
    bodyHtml: "" +
      '<p class="docsViewer__modalNote muted small"><strong>Media:</strong> ' + escapeHtml(preview.media_identity) + "</p>" +
      reviewHtml +
      warningHtml,
    actions: [
      { role: "modal-primary", label: collision === "replace" ? "Replace" : copy.primary },
      { role: "modal-cancel", label: "Cancel" }
    ]
  }).then(function (result) {
    return Boolean(result && result.confirmed);
  });
}

export async function publishAndInsertStagedMedia(options = {}) {
  var provider = options.provider || {};
  var adapter = options.adapter || null;
  var kind = cleanString(options.mediaKind) === "file" ? "file" : "image";
  if (
    typeof provider.listStagedMedia !== "function" ||
    typeof provider.previewStagedMedia !== "function" ||
    typeof provider.applyStagedMedia !== "function" ||
    !adapter || typeof adapter.replaceSelection !== "function"
  ) {
    throw new Error("Staged media publication is unavailable on this route.");
  }

  var listing = await provider.listStagedMedia(kind);
  var files = Array.isArray(listing && listing.files) ? listing.files : [];
  if (listing && listing.available === false && cleanString(listing.message)) {
    throw new Error(cleanString(listing.message));
  }
  if (!files.length) {
    throw new Error(actionCopy(kind).empty);
  }
  var choice = await chooseStagedMedia(options.root || document.body, kind, files);
  if (!choice) return null;
  var request = {
    media_kind: kind,
    staged_filename: choice.stagedFilename,
    label: choice.label
  };
  if (kind === "image") {
    request.add_caption = Boolean(choice.addCaption);
    if (choice.addCaption) {
      request.caption = choice.caption;
      request.summary = choice.summary;
      request.placement = choice.placement;
      request.fill_width = Boolean(choice.fillWidth);
    }
  }
  var preview = await provider.previewStagedMedia(request);
  var confirmed = await confirmStagedMedia(options.root || document.body, kind, preview);
  if (!confirmed) return null;
  var payload = await provider.applyStagedMedia(Object.assign({}, request, {
    confirm_replace: Boolean(preview.requires_replace_confirmation)
  }));
  if (!adapter.replaceSelection(payload.markdown)) {
    throw new Error("Media was published, but its Markdown reference could not be inserted.");
  }
  return payload;
}
