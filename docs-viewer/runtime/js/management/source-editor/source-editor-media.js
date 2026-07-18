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

function chooseStagedMedia(root, kind, files) {
  var copy = actionCopy(kind);
  var records = Array.isArray(files) ? files : [];
  if (!records.length) return Promise.resolve(null);
  var optionsHtml = records.map(function (file) {
    return '<option value="' + escapeHtml(file.filename) + '">' + escapeHtml(file.filename) + "</option>";
  }).join("");
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
      "</div>",
    actions: [
      { role: "modal-primary", label: copy.primary },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var select = api.host.querySelector('[data-role="staged-media-file"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      function projectSuggestedLabel() {
        var selected = records.find(function (record) { return record.filename === select.value; });
        label.value = cleanString(selected && selected.suggested_label);
      }
      select.addEventListener("change", projectSuggestedLabel);
      projectSuggestedLabel();
    },
    onSubmit: function (api) {
      var select = api.host.querySelector('[data-role="staged-media-file"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var filename = cleanString(select && select.value);
      var labelValue = cleanString(label && label.value);
      if (!filename || !labelValue) {
        api.setStatus("Choose a staged file and enter " + copy.fieldLabel.toLowerCase() + ".");
        return false;
      }
      return { confirmed: true, stagedFilename: filename, label: labelValue };
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
