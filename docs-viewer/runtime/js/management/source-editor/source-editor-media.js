import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  bindImagePresentation,
  imagePresentationHtml,
  readImagePresentation
} from "./source-editor-image-presentation.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function actionCopy(kind) {
  return kind === "file"
    ? { title: "Add file", fieldLabel: "Link label", empty: "No staged files are available.", primary: "Add file" }
    : { title: "Add image", fieldLabel: "Alt text", empty: "No staged images are available.", primary: "Add image" };
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
      select.addEventListener("change", projectSuggestedLabel);
      label.addEventListener("input", projectCaptionSuggestion);
      if (captionInput) {
        captionInput.addEventListener("input", function () {
          captionEdited = true;
        });
      }
      if (captionToggle) bindImagePresentation(api.host);
      projectSuggestedLabel();
    },
    onSubmit: function (api) {
      var select = api.host.querySelector('[data-role="staged-media-file"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var filename = cleanString(select && select.value);
      var labelValue = cleanString(label && label.value);
      var presentation = readImagePresentation(api.host);
      var addCaption = kind === "image" && presentation.addCaption;
      if (!filename || !labelValue) {
        api.setStatus("Choose a staged file and enter " + copy.fieldLabel.toLowerCase() + ".");
        return false;
      }
      if (addCaption && !presentation.caption) {
        api.setStatus("Enter caption text or turn off Add caption.");
        var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
        if (captionInput) captionInput.focus();
        return false;
      }
      if (addCaption && !presentation.placement) {
        api.setStatus("Choose an image placement.");
        return false;
      }
      return {
        confirmed: true,
        stagedFilename: filename,
        label: labelValue,
        addCaption: addCaption,
        caption: presentation.caption,
        summary: presentation.summary,
        placement: presentation.placement,
        fillWidth: presentation.fillWidth
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
