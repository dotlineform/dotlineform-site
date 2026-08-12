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

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function actionCopy(kind) {
  return kind === "file"
    ? { title: "Add file", fieldLabel: "Link label", empty: "No files are available in this folder.", primary: "Add file" }
    : { title: "Add image", fieldLabel: "Alt text", empty: "No images are available in this folder.", primary: "Add image" };
}

function byteSize(value) {
  var size = Number(value);
  if (!Number.isFinite(size) || size < 0) return "";
  return size.toLocaleString("en-GB") + (size === 1 ? " byte" : " bytes");
}

function chooseStagedMedia(root, kind, listing, draft) {
  var copy = actionCopy(kind);
  var records = Array.isArray(listing && listing.files) ? listing.files : [];
  var sourceDirectory = cleanString(listing && listing.current_directory);
  var canChooseFolder = cleanString(listing && listing.source_kind) === "media_source";
  var sourceCopy = canChooseFolder ? sourceDirectory : "Import staging";
  var filesHtml = records.map(function (file, index) {
    var size = byteSize(file && file.size_bytes);
    var checked = cleanString(draft && draft.stagedFilename) === cleanString(file && file.filename)
      ? " checked"
      : "";
    return '<label class="docsViewer__stagedMediaOption" for="docsViewerStagedMediaFile-' + index + '">' +
      '<input class="docsViewer__checkboxInput" id="docsViewerStagedMediaFile-' + index + '" data-role="staged-media-file" name="docsViewerStagedMediaFile" type="radio" value="' + escapeHtml(file.filename) + '"' + checked + '>' +
      '<span class="docsViewer__stagedMediaOptionCopy">' +
        '<span class="docsViewer__stagedMediaFilename">' + escapeHtml(file.filename) + "</span>" +
        (size ? '<span class="docsViewer__stagedMediaSize muted small">' + escapeHtml(size) + "</span>" : "") +
      "</span>" +
    "</label>";
  }).join("");
  if (!filesHtml) {
    filesHtml = '<p class="docsViewer__modalNote muted small">' + escapeHtml(copy.empty) + "</p>";
  }
  var captionHtml = kind === "image" ? imagePresentationHtml() : "";
  var chooseFolderRequested = false;
  return openDocsViewerManagementModal({
    root: root,
    title: copy.title,
    size: "compact",
    focusSelector: records.length
      ? '[data-role="staged-media-file"]'
      : canChooseFolder
      ? '[data-role="choose-media-source-folder"]'
      : '[data-role="staged-media-label"]',
    bodyHtml: "" +
      '<div class="docsViewer__stagedMediaSource">' +
        '<span class="docsViewer__fieldLabel">Source folder</span>' +
        '<span class="docsViewer__stagedMediaSourcePath">' + escapeHtml(sourceCopy) + "</span>" +
        (canChooseFolder
          ? '<button class="docsViewer__actionButton" data-role="choose-media-source-folder" type="button">Choose folder…</button>'
          : "") +
      "</div>" +
      '<div class="docsViewer__field docsViewer__field--listbox">' +
        '<span class="docsViewer__fieldLabel">Source file</span>' +
        '<div class="docsViewer__stagedMediaOptions">' + filesHtml + "</div>" +
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
      var folderButton = api.host.querySelector('[data-role="choose-media-source-folder"]');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var captionToggle = api.host.querySelector('[data-role="staged-media-caption"]');
      var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
      var captionEdited = Boolean(draft);
      label.value = cleanString(draft && draft.label);
      if (kind === "image" && draft) hydrateImagePresentation(api.host, draft);
      function projectSuggestedLabel() {
        var selectedInput = api.host.querySelector('[data-role="staged-media-file"]:checked');
        var selected = records.find(function (record) {
          return selectedInput && record.filename === selectedInput.value;
        });
        label.value = cleanString(selected && selected.suggested_label);
        if (captionInput) {
          captionInput.value = label.value;
          captionEdited = false;
        }
      }
      function projectCaptionSuggestion() {
        if (captionInput && !captionEdited) captionInput.value = label.value;
      }
      api.host.querySelectorAll('[data-role="staged-media-file"]').forEach(function (input) {
        input.addEventListener("change", projectSuggestedLabel);
      });
      label.addEventListener("input", projectCaptionSuggestion);
      if (captionInput) {
        captionInput.addEventListener("input", function () {
          captionEdited = true;
        });
      }
      if (captionToggle) bindImagePresentation(api.host);
      if (folderButton) {
        folderButton.addEventListener("click", function () {
          chooseFolderRequested = true;
          var primary = api.host.querySelector('[data-role="modal-primary"]');
          if (primary) primary.click();
        });
      }
    },
    onSubmit: function (api) {
      var selectedInput = api.host.querySelector('[data-role="staged-media-file"]:checked');
      var label = api.host.querySelector('[data-role="staged-media-label"]');
      var filename = cleanString(selectedInput && selectedInput.value);
      var labelValue = cleanString(label && label.value);
      var presentation = readImagePresentation(api.host);
      var addCaption = kind === "image" && presentation.addCaption;
      if (chooseFolderRequested) {
        return {
          chooseFolder: true,
          stagedFilename: filename,
          label: labelValue,
          addCaption: addCaption,
          caption: presentation.caption,
          summary: presentation.summary,
          placement: presentation.placement,
          fillWidth: presentation.fillWidth
        };
      }
      if (!filename || !labelValue) {
        api.setStatus("Choose a source file and enter " + copy.fieldLabel.toLowerCase() + ".");
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
        sourceDirectory: sourceDirectory,
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
    return result && (result.confirmed || result.chooseFolder) ? result : null;
  });
}

async function chooseMediaSourceFolder(root, kind, listing, provider) {
  var module = await import("/docs-viewer/runtime/js/shared-frontend/folder-picker.js");
  if (!module || typeof module.createFolderPicker !== "function") {
    throw new Error("Folder picker module did not expose createFolderPicker().");
  }
  var picker = null;
  var result = await openDocsViewerManagementModal({
    root: root,
    title: "Choose source folder",
    bodyHtml: '<div data-role="media-source-folder-picker"></div>',
    actions: [
      { role: "modal-primary", label: "Choose folder" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var host = api.host.querySelector('[data-role="media-source-folder-picker"]');
      picker = module.createFolderPicker(host, {
        rootDirectory: cleanString(listing.source_root),
        rootLabel: cleanString(listing.source_root).split("/").slice(-1)[0],
        initialDirectory: cleanString(listing.current_directory),
        loadDirectory: function (request) {
          return provider.listStagedMedia(kind, { sourceDirectory: request.directory });
        },
        onError: function (error) {
          api.setStatus(error && error.message ? error.message : "Folder could not be loaded.");
        },
        onSubmit: function (request) {
          return { confirmed: true, sourceDirectory: request.directory };
        }
      });
      Promise.resolve(picker.ready).then(function () {
        picker.focusPreferred();
      }).catch(function (error) {
        api.setStatus(error && error.message ? error.message : "Folder could not be loaded.");
      });
    },
    onSubmit: function () {
      if (!picker) return false;
      return picker.submit();
    }
  });
  if (picker) picker.destroy();
  return result && result.confirmed ? cleanString(result.sourceDirectory) : "";
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

  var root = options.root || document.body;
  var listing = await provider.listStagedMedia(kind);
  var choice;
  var draft = null;
  while (true) {
    if (listing && listing.available === false && cleanString(listing.message)) {
      throw new Error(cleanString(listing.message));
    }
    choice = await chooseStagedMedia(root, kind, listing || {}, draft);
    if (!choice) return null;
    if (!choice.chooseFolder) break;
    draft = choice;
    var selectedDirectory = await chooseMediaSourceFolder(root, kind, listing || {}, provider);
    if (selectedDirectory) {
      if (selectedDirectory !== cleanString(listing && listing.current_directory)) {
        draft = null;
      }
      listing = await provider.listStagedMedia(kind, { sourceDirectory: selectedDirectory });
    }
  }
  var request = {
    media_kind: kind,
    staged_filename: choice.stagedFilename,
    label: choice.label
  };
  if (cleanString(listing && listing.source_kind) === "media_source") {
    request.source_directory = choice.sourceDirectory;
  }
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
  var confirmed = await confirmStagedMedia(root, kind, preview);
  if (!confirmed) return null;
  var payload = await provider.applyStagedMedia(Object.assign({}, request, {
    confirm_replace: Boolean(preview.requires_replace_confirmation)
  }));
  if (!adapter.replaceSelection(payload.markdown)) {
    throw new Error("Media was published, but its Markdown reference could not be inserted.");
  }
  return payload;
}
