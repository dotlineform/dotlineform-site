import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  bindImagePresentation,
  hydrateImagePresentation,
  imagePresentationHtml,
  readImagePresentation
} from "./source-editor-image-presentation.js";
import { parseImageTokens, serializeImageToken } from "./image-token-parser.js";
import { sourceTokenAtSelection } from "./catalogue-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function actionCopy(kind) {
  return kind === "file"
    ? { title: "Add file", fieldLabel: "Link label", fileLabel: "File name", primary: "Add file" }
    : { title: "Add image", fieldLabel: "Alt text", fileLabel: "Image file name", primary: "Add image" };
}

function chooseSourceMedia(root, kind, mediaOptions, draft) {
  var copy = actionCopy(kind);
  var editing = kind === "image" && Boolean(draft && draft.mediaPath);
  if (editing) copy = Object.assign({}, copy, { title: "Edit image", primary: "Apply" });
  var selectedFile = null;
  return openDocsViewerManagementModal({
    root: root, title: copy.title, size: "compact",
    focusSelector: editing ? '[data-role="media-label"]' : '[data-role="choose-media-file"]',
    bodyHtml:
      '<div class="docsViewer__field">' +
        '<label class="docsViewer__fieldLabel" for="docsViewerMediaFilename">' + escapeHtml(copy.fileLabel) + '</label>' +
        '<div class="docsViewerSourceEditorMedia__file">' +
          '<input class="docsViewer__fieldInput" id="docsViewerMediaFilename" data-role="media-filename" type="text" readonly>' +
          '<button class="docsViewer__toolbarIconButton" data-role="choose-media-file" type="button" aria-label="Choose file" title="Choose file">' +
            '<span class="docsViewer__toolbarIcon docsViewer__icon--folder-open" aria-hidden="true"></span>' +
          '</button>' +
        '</div>' +
        '<input data-role="media-file" type="file" accept="' + escapeHtml(mediaOptions.accept) + '" hidden>' +
      '</div>' +
      '<div class="docsViewer__field">' +
        '<label class="docsViewer__fieldLabel" for="docsViewerMediaLabel">' + escapeHtml(copy.fieldLabel) + '</label>' +
        '<input class="docsViewer__fieldInput" id="docsViewerMediaLabel" data-role="media-label" type="text" required>' +
      '</div>' +
      (kind === "image" ? imagePresentationHtml() : "") +
      (kind === "image"
        ? '<label class="docsViewer__field"><span><input class="docsViewer__checkboxInput" data-role="create-thumb" type="checkbox" disabled> Create thumb</span></label>'
        : ""),
    actions: [{ role: "modal-primary", label: copy.primary }, { role: "modal-cancel", label: "Cancel" }],
    onOpen: function (api) {
      var input = api.host.querySelector('[data-role="media-file"]');
      var filename = api.host.querySelector('[data-role="media-filename"]');
      var label = api.host.querySelector('[data-role="media-label"]');
      var captionInput = api.host.querySelector('[data-role="media-caption-text"]');
      var thumbToggle = api.host.querySelector('[data-role="create-thumb"]');
      var labelEdited = editing;
      var captionEdited = editing;
      filename.value = editing ? draft.mediaPath.split("/").pop() : "";
      label.value = cleanString(draft && draft.label);
      if (kind === "image") {
        if (draft) hydrateImagePresentation(api.host, draft);
        bindImagePresentation(api.host);
      }
      api.host.querySelector('[data-role="choose-media-file"]').addEventListener("click", function () {
        input.value = "";
        input.click();
      });
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (!file) return;
        var suffix = "." + file.name.split(".").pop().toLowerCase();
        if (!mediaOptions.accept.split(",").includes(suffix)) {
          api.setStatus("Select a supported " + kind + " file.");
          return;
        }
        if (!file.size || file.size > mediaOptions.max_file_bytes) {
          api.setStatus(file.size ? "Selected media exceeds the 64 MiB file limit." : "Selected media file is empty.");
          return;
        }
        selectedFile = file;
        filename.value = file.name;
        if (!labelEdited) label.value = file.name.replace(/\.[^.]+$/, "").trim().split(/[_\-\s]+/).map(function (part) {
          return part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
        }).join(" ");
        if (captionInput && !captionEdited) captionInput.value = label.value;
        if (thumbToggle) {
          thumbToggle.disabled = !/\.(jpg|jpeg|png|webp|gif)$/i.test(file.name);
          if (thumbToggle.disabled) thumbToggle.checked = false;
        }
        api.setStatus("");
      });
      label.addEventListener("input", function () {
        labelEdited = true;
        if (captionInput && !captionEdited) captionInput.value = label.value;
      });
      if (captionInput) captionInput.addEventListener("input", function () { captionEdited = true; });
    },
    onSubmit: function (api) {
      var label = cleanString(api.host.querySelector('[data-role="media-label"]').value);
      var presentation = readImagePresentation(api.host);
      var thumbToggle = api.host.querySelector('[data-role="create-thumb"]');
      if ((!editing && !selectedFile) || !label) {
        api.setStatus("Choose a file and enter " + copy.fieldLabel.toLowerCase() + ".");
        return false;
      }
      if (kind === "image" && presentation.addCaption && !presentation.caption) {
        api.setStatus("Enter caption text or turn off Add caption.");
        return false;
      }
      if (kind === "image" && !presentation.placement) {
        api.setStatus("Choose an image placement.");
        return false;
      }
      return Object.assign({}, presentation, {
        confirmed: true, file: selectedFile, label: label,
        mediaPath: editing ? draft.mediaPath : "",
        createThumb: Boolean(thumbToggle && !thumbToggle.disabled && thumbToggle.checked)
      });
    }
  }).then(function (result) { return result && result.confirmed ? result : null; });
}

function confirmSourceMedia(root, kind, preview) {
  var copy = actionCopy(kind);
  var collision = cleanString(preview && preview.collision);
  var diagnostics = preview && preview.svg && preview.svg.diagnostics;
  var warnings = diagnostics && Array.isArray(diagnostics.warnings) ? diagnostics.warnings : [];
  if (collision !== "replace" && !warnings.length) return Promise.resolve(true);
  var reviewHtml = collision === "replace"
    ? ""
    : '<p class="docsViewer__modalNote muted small">SVG sanitization changed the selected source. Review the diagnostics before adding it.</p>';
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

/** Await native media writes before insertion, or apply presentation to the captured token. */
export async function publishAndInsertSourceMedia(options = {}) {
  var provider = options.provider || {};
  var adapter = options.adapter || null;
  var kind = cleanString(options.mediaKind) === "file" ? "file" : "image";
  if (typeof provider.readSourceMediaOptions !== "function" || typeof provider.applySourceMedia !== "function"
      || !adapter || typeof adapter.insertSourceMedia !== "function" || !options.capture) {
    throw new Error("Native media intake is unavailable on this route.");
  }
  var root = options.root || document.body;
  var snapshot = adapter.getBufferSnapshot();
  var bodyStart = sourceBodyStart(snapshot.value);
  var initialToken = kind === "image" ? sourceTokenAtSelection(
    parseImageTokens(snapshot.value.slice(bodyStart)).map(function (token) {
      return Object.assign({}, token, { start: token.start + bodyStart, end: token.end + bodyStart });
    }), options.capture
  ) : null;
  var capture = initialToken
    ? { start: initialToken.start, end: initialToken.end, text: initialToken.raw, revision: snapshot.revision }
    : options.capture;
  var draft = initialToken ? Object.assign({}, initialToken, {
    label: initialToken.alt, addCaption: Boolean(initialToken.caption)
  }) : null;
  var mediaOptions = await provider.readSourceMediaOptions(kind, options.target);
  var choice = await chooseSourceMedia(root, kind, mediaOptions, draft);
  if (!choice) return null;
  if (!choice.file && choice.mediaPath) {
    var token = serializeImageToken({ mediaPath: choice.mediaPath, alt: choice.label,
      caption: choice.addCaption ? choice.caption : "", summary: choice.summary,
      placement: choice.placement, fillWidth: choice.fillWidth });
    if (!token) throw new Error("Image fields are invalid.");
    var updated = { markdown: token, summary_text: "Image token updated." };
    if (!adapter.insertSourceMedia(capture, updated)) throw new Error("The Source image occurrence changed.");
    return updated;
  }
  var request = Object.assign({}, options.target, { media_kind: kind, label: choice.label });
  if (kind === "image") {
    request.source_text = adapter.getBufferSnapshot().value;
    request.create_thumb = choice.createThumb;
    request.add_caption = Boolean(choice.addCaption);
    request.caption = choice.addCaption ? choice.caption : "";
    request.summary = choice.summary;
    request.placement = choice.placement;
    request.fill_width = choice.fillWidth;
  }
  if (new Blob([JSON.stringify(request)]).size > mediaOptions.max_metadata_bytes) {
    throw new Error("Media metadata exceeds the 1 MiB limit.");
  }
  var payload = await provider.applySourceMedia(request, choice.file);
  if (payload.requires_confirmation) {
    if (!await confirmSourceMedia(root, kind, payload)) return null;
    payload = await provider.applySourceMedia(Object.assign({}, request, {
      confirm_replace: Boolean(payload.requires_replace_confirmation), confirm_sanitization: true
    }), choice.file);
  }
  if (payload.requires_confirmation) throw new Error("Media confirmation did not complete.");
  if (!adapter.insertSourceMedia(capture, payload)) {
    throw new Error("Media was stored, but its source reference could not be inserted.");
  }
  return payload;
}
