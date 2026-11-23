import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  imagePresentationHtml,
  mountImagePresentation,
  readImagePresentation
} from "./source-editor-image-presentation.js";
import { imageDetailAtOccurrence, planImageDetailReplacement } from "./image-detail-directive.js";
import { serializeImageToken } from "./image-token-parser.js";
import { parseSourceTokens, sourceTokenAtSelection } from "./source-token-parser.js";
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
  var editing = Boolean(draft && draft.mediaPath);
  if (editing) copy = Object.assign({}, copy, { title: "Edit " + kind, primary: "Apply" });
  var selectedFile = null;
  return openDocsViewerManagementModal({
    root: root, title: copy.title, size: kind === "image" ? "standard" : "compact",
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
      (kind === "image" && (!editing || draft.imageDetail)
        ? '<label class="docsViewer__field docsViewer__field--checkbox">' +
            '<input class="docsViewer__checkboxInput" data-role="image-detail" type="checkbox"' +
              (draft?.imageDetail && draft.imageDetail.directiveStart !== null ? ' checked' : '') + '>' +
            '<span class="docsViewer__fieldLabel">Image detail</span>' +
          '</label>'
        : "") +
      (kind === "image"
        ? '<label class="docsViewer__field docsViewer__field--checkbox">' +
            '<input class="docsViewer__checkboxInput" data-role="preserve-resolution" type="checkbox" disabled>' +
            '<span class="docsViewer__fieldLabel">Preserve original resolution</span>' +
          '</label>'
        : ""),
    actions: [{ role: "modal-primary", label: copy.primary }, { role: "modal-cancel", label: "Cancel" }],
    onOpen: function (api) {
      var input = api.host.querySelector('[data-role="media-file"]');
      var filename = api.host.querySelector('[data-role="media-filename"]');
      var label = api.host.querySelector('[data-role="media-label"]');
      var captionInput = api.host.querySelector('[data-role="media-caption-text"]');
      var preserveToggle = api.host.querySelector('[data-role="preserve-resolution"]');
      function setRasterControls(file) {
        var raster = Boolean(file && /\.(jpg|jpeg|png|webp|gif)$/i.test(file.name));
        [preserveToggle].forEach(function (toggle) {
          if (!toggle) return;
          toggle.disabled = !raster;
          if (!raster) toggle.checked = false;
        });
      }
      if (preserveToggle && draft) preserveToggle.checked = draft.preserveResolution;
      setRasterControls(draft && draft.pendingFile);
      var labelEdited = editing;
      var captionEdited = editing;
      filename.value = editing ? draft.mediaPath.split("/").pop() : "";
      label.value = cleanString(draft && draft.label);
      if (kind === "image") mountImagePresentation(api.host, draft || {});
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
          return kind === "image" ? part.toLowerCase() : part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
        }).join(" ");
        if (captionInput && !captionEdited) captionInput.value = label.value;
        setRasterControls(file);
        api.setStatus("");
      });
      label.addEventListener("input", function () {
        labelEdited = true;
        if (captionInput && !captionEdited) captionInput.value = label.value;
      });
      if (captionInput) {
        captionInput.addEventListener("input", function () { captionEdited = true; });
        var captionToggle = api.host.querySelector('[data-role="media-caption"]');
        captionToggle.addEventListener("change", function () {
          if (captionToggle.checked && !captionInput.value.trim()) captionInput.value = label.value;
        });
      }
    },
    onSubmit: function (api) {
      var label = cleanString(api.host.querySelector('[data-role="media-label"]').value);
      var presentation = kind === "image" ? readImagePresentation(api.host) : {};
      var preserveToggle = api.host.querySelector('[data-role="preserve-resolution"]');
      var imageDetailToggle = api.host.querySelector('[data-role="image-detail"]');
      var preserveResolution = Boolean(preserveToggle && !preserveToggle.disabled && preserveToggle.checked);
      var pendingFile = draft && draft.pendingFile
        && (preserveResolution !== draft.preserveResolution) ? draft.pendingFile : null;
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
        confirmed: true, file: selectedFile || pendingFile, label: label,
        mediaPath: editing ? draft.mediaPath : "",
        preserveResolution: preserveResolution,
        imageDetail: Boolean(imageDetailToggle && imageDetailToggle.checked)
      });
    }
  }).then(function (result) { return result && result.confirmed ? result : null; });
}

function sourceFileTokens(body) {
  var links = new Map();
  var pattern = /\[((?:\\.|[^\]\\])*)\]\(\[\[media:[^\]\r\n]+\]\]\)/g;
  for (var link of body.matchAll(pattern)) {
    links.set(link.index + link[0].indexOf("[[media:"), link);
  }
  return parseSourceTokens(body, function (raw, location) {
    var match = /^\[\[media:(docs\/(?:collections\/[a-z0-9-]+\/)?files\/[^\]\s]+)\]\]$/.exec(raw);
    if (!match) return null;
    var token = { raw: raw, mediaPath: match[1], label: "", start: location.start, end: location.start + raw.length,
      tokenStart: location.start, tokenEnd: location.start + raw.length };
    var link = links.get(location.start);
    if (link) {
      token.raw = link[0];
      token.start = link.index;
      token.end = link.index + link[0].length;
      token.label = link[1].replace(/\\(.)/g, "$1");
    }
    return token;
  });
}

function captureSourceFileEdit(source, selection) {
  var bodyStart = sourceBodyStart(source);
  var occurrences = sourceFileTokens(source.slice(bodyStart));
  var start = selection.start - bodyStart;
  var end = selection.end - bodyStart;
  var token = sourceTokenAtSelection(occurrences, { start: start, end: end }) || occurrences.find(function (occurrence) {
    return occurrence.tokenStart === start && occurrence.tokenEnd === end;
  });
  return token && {
    token: token,
    capture: {
      start: token.start + bodyStart,
      end: token.end + bodyStart,
      text: token.raw,
      revision: selection.revision
    }
  };
}

/** Retain a native File for Save, or apply presentation to the captured token locally. */
export async function prepareAndInsertSourceMedia(options = {}) {
  var provider = options.provider || {};
  var adapter = options.adapter || null;
  var kind = cleanString(options.mediaKind) === "file" ? "file" : "image";
  var mediaOptions = options.mediaOptions;
  if (!mediaOptions || typeof provider.prepareSourceMedia !== "function"
      || !adapter || typeof adapter.insertSourceMedia !== "function" || !options.action?.capture) {
    throw new Error("Native media intake is unavailable on this route.");
  }
  var root = options.root || document.body;
  var action = kind === "file" ? captureSourceFileEdit(options.source, options.action.capture) || options.action : options.action;
  var capture = action.capture;
  var initialToken = action.token;
  var imageDetail = kind === "image" && initialToken ? imageDetailAtOccurrence(options.source, capture) : null;
  var draft = initialToken ? Object.assign({}, initialToken, {
    label: kind === "image" ? initialToken.alt : initialToken.label, addCaption: Boolean(initialToken.caption),
    imageDetail: imageDetail
  }) : null;
  var existing = initialToken && adapter.pendingSourceMedia(initialToken.mediaPath);
  if (draft && existing) {
    draft.pendingFile = existing.file;
    draft.preserveResolution = existing.preserveResolution;
  }
  var choice = await chooseSourceMedia(root, kind, mediaOptions, draft);
  if (!choice) return null;
  var reuse = choice.file && existing && existing.file === choice.file;
  var mediaPath = choice.mediaPath;
  if (choice.file) {
    mediaPath = reuse ? existing.mediaPath : (await provider.prepareSourceMedia(Object.assign({}, options.target, {
      media_kind: kind, filename: choice.file.name
    }))).media_identity;
  }
  var markdown = kind === "image" ? serializeImageToken({
    mediaPath: mediaPath, alt: choice.label, caption: choice.addCaption ? choice.caption : "",
    summary: choice.summary, placement: choice.placement, fillWidth: choice.fillWidth
  }) : fileLink(choice.label, mediaPath);
  if (!markdown) throw new Error("Image fields are invalid.");
  if (kind === "image") {
    var replacement = planImageDetailReplacement(options.source, capture, markdown, imageDetail, choice.imageDetail);
    capture = replacement.capture;
    markdown = replacement.markdown;
  }
  if (!choice.file) {
    var updated = { markdown: markdown, summary_text: "Media reference updated." };
    if (!adapter.insertSourceMedia(capture, updated)) throw new Error("The Source occurrence changed.");
    return updated;
  }
  var payload = { markdown: markdown, summary_text: "Media reference inserted. Save to store the selected file." };
  if (!adapter.insertSourceMedia(capture, payload, {
    file: choice.file, mediaKind: kind, mediaPath: mediaPath,
    replace: kind === "image" || (reuse ? existing.replace : Boolean(initialToken)),
    preserveResolution: choice.preserveResolution,
    editedPath: initialToken && initialToken.mediaPath
  })) throw new Error("The Source occurrence changed; no media was stored.");
  return payload;
}

function fileLink(label, mediaPath) {
  return "[" + label.replace(/\\/g, "\\\\").replace(/\[/g, "\\[").replace(/\]/g, "\\]")
    + "]([[media:" + mediaPath + "]])";
}
