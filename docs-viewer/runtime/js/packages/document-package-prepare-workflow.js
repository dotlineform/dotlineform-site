import {
  getDocumentPackageConfig,
  getPackageDocuments,
  prepareDocumentPackage,
  saveDocumentPackageContext
} from "./document-package-client.js";
import {
  createDocumentPackagePrepareRequest,
  documentPackageContentFormats,
  documentPackageExternalContext,
  documentPackageExternalContextChanged,
  documentPackageExternalContextMissingValues,
  documentPackageProfile,
  documentPackageProfileLabel,
  documentPackageProfileIncludesDescendants,
  documentPackageProfileRequiresDescendants,
  documentPackageSelectionEligibility,
  documentPackageTargetFormats,
  projectDocumentPackageSelection
} from "./document-package-prepare-model.js";
import {
  packageIssueMessage,
  packageText
} from "./document-package-view.js";
import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../management/docs-viewer-management-modal-shell.js";

const DOCUMENT_PACKAGE_PREPARE_COUNT_ORDER = Object.freeze([
  "selected",
  "exported",
  "failed",
  "skipped",
  "truncated"
]);

function formatLabel(value) {
  const normalized = packageText(value);
  if (normalized === "plain_text") return "Plain text";
  return normalized.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function normalizeCheckedDocIds(values) {
  const seen = new Set();
  return (Array.isArray(values) ? values : []).map(packageText).filter((value) => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function writeSelectOptions(select, values, selectedValue, labelForValue = formatLabel) {
  if (!select) return;
  select.replaceChildren(...values.map((value) => {
    const option = select.ownerDocument.createElement("option");
    option.value = packageText(value);
    option.textContent = labelForValue(value);
    option.selected = option.value === packageText(selectedValue);
    return option;
  }));
}

function contextFieldsHtml(profile, externalContext) {
  const context = externalContext || documentPackageExternalContext(profile);
  const descriptions = context.field_descriptions || {};
  const fields = Array.isArray(profile && profile.document_fields) ? profile.document_fields : [];
  return [
    '<label class="docsViewer__field" for="docsViewerPackageContextTask">',
    '  <span class="docsViewer__fieldLabel">Task</span>',
    '  <input class="docsViewer__fieldInput" id="docsViewerPackageContextTask" data-package-context-task value="' + escapeHtml(context.task) + '">',
    '</label>',
    '<label class="docsViewer__field" for="docsViewerPackageContextGuidance">',
    '  <span class="docsViewer__fieldLabel">Response guidance</span>',
    '  <textarea class="docsViewer__fieldInput" id="docsViewerPackageContextGuidance" data-package-context-guidance rows="3">' + escapeHtml(context.response_guidance) + '</textarea>',
    '</label>',
    ...fields.map((field, index) => {
      const outputPath = packageText(field && field.output_path);
      return [
        '<label class="docsViewer__field" for="docsViewerPackageContextField-' + String(index + 1) + '">',
        '  <span class="docsViewer__fieldLabel">' + escapeHtml(outputPath) + '</span>',
        '  <textarea class="docsViewer__fieldInput" id="docsViewerPackageContextField-' + String(index + 1) + '" data-package-context-field data-output-path="' + escapeHtml(outputPath) + '" rows="2">' + escapeHtml(descriptions[outputPath]) + '</textarea>',
        '</label>'
      ].join("");
    })
  ].join("");
}

function readContextFields(host) {
  const fieldDescriptions = {};
  host.querySelectorAll("[data-package-context-field]").forEach((node) => {
    const outputPath = packageText(node.dataset.outputPath);
    if (outputPath) fieldDescriptions[outputPath] = packageText(node.value);
  });
  return {
    task: packageText(host.querySelector("[data-package-context-task]")?.value),
    response_guidance: packageText(host.querySelector("[data-package-context-guidance]")?.value),
    field_descriptions: fieldDescriptions
  };
}

function optionsBodyHtml() {
  return [
    '<label class="docsViewer__field" for="docsViewerPackageProfile">',
    '  <span class="docsViewer__fieldLabel">Profile</span>',
    '  <select class="docsViewer__fieldInput" id="docsViewerPackageProfile" data-package-profile></select>',
    '</label>',
    '<p class="docsViewer__modalNote muted small" data-package-profile-description></p>',
    '<label class="docsViewer__field" for="docsViewerPackageTargetFormat">',
    '  <span class="docsViewer__fieldLabel">Package format</span>',
    '  <select class="docsViewer__fieldInput" id="docsViewerPackageTargetFormat" data-package-target-format></select>',
    '</label>',
    '<label class="docsViewer__field" for="docsViewerPackageContentFormat" data-package-content-format-field>',
    '  <span class="docsViewer__fieldLabel">Content format</span>',
    '  <select class="docsViewer__fieldInput" id="docsViewerPackageContentFormat" data-package-content-format></select>',
    '</label>',
    '<label class="docsViewer__field docsViewer__field--checkbox">',
    '  <input class="docsViewer__checkboxInput" type="checkbox" data-package-include-descendants>',
    '  <span class="docsViewer__fieldLabel">Include descendants</span>',
    '</label>',
    '<label class="docsViewer__field docsViewer__field--checkbox" data-package-missing-summary-field>',
    '  <input class="docsViewer__checkboxInput" type="checkbox" data-package-missing-summary-only>',
    '  <span class="docsViewer__fieldLabel">Only documents missing summaries</span>',
    '</label>',
    '<label class="docsViewer__field docsViewer__field--checkbox" data-package-include-non-viewable-field>',
    '  <input class="docsViewer__checkboxInput" type="checkbox" data-package-include-non-viewable>',
    '  <span class="docsViewer__fieldLabel">Include non-viewable documents</span>',
    '</label>',
    '<section class="docsViewerPackagePrepare__selectionSummary" aria-live="polite">',
    '  <p data-package-effective-total></p>',
    '  <ul class="muted small" data-package-selection-details hidden></ul>',
    '</section>',
    '<details class="docsViewerPackagePrepare__context" data-package-context-details>',
    '  <summary>Edit package context</summary>',
    '  <div class="docsViewerPackagePrepare__contextFields" data-package-context-fields></div>',
    '</details>'
  ].join("");
}

function countLabel(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function selectionProjectionMessages(projection) {
  const messages = [];
  if (projection.total === 0) {
    messages.push("No documents remain after applying the selected package filters.");
  }
  if (projection.excludedNonViewableCount) {
    messages.push(
      countLabel(
        projection.excludedNonViewableCount,
        "non-viewable document excluded.",
        "non-viewable documents excluded."
      )
    );
  }
  if (projection.excludedWithSummaryCount) {
    messages.push(
      countLabel(
        projection.excludedWithSummaryCount,
        "document excluded because it already has a summary.",
        "documents excluded because they already have summaries."
      )
    );
  }
  if (projection.excludedByLimitCount) {
    messages.push(
      countLabel(
        projection.excludedByLimitCount,
        "document excluded by the profile maximum.",
        "documents excluded by the profile maximum."
      )
    );
  }
  if (projection.includedNonViewableCount) {
    messages.push(
      countLabel(
        projection.includedNonViewableCount,
        "non-viewable document included.",
        "non-viewable documents included."
      )
    );
  }
  return messages;
}

function writeSelectionProjection(host, projection) {
  const total = host.querySelector("[data-package-effective-total]");
  const details = host.querySelector("[data-package-selection-details]");
  const primary = host.querySelector('[data-role="modal-primary"]');
  if (total) {
    total.textContent = `Total documents to be prepared: ${projection.total}`;
  }
  if (details) {
    const messages = selectionProjectionMessages(projection);
    details.replaceChildren(...messages.map((message) => {
      const item = details.ownerDocument.createElement("li");
      item.textContent = message;
      return item;
    }));
    details.hidden = !messages.length;
  }
  if (primary) primary.disabled = projection.total === 0;
}

export function documentPackagePrepareResultHtml(payload) {
  const report = payload && typeof payload === "object" ? payload : {};
  const summary = packageText(report.summary_text);
  const counts = report.counts && typeof report.counts === "object" ? report.counts : {};
  const orderedCountKeys = new Set(DOCUMENT_PACKAGE_PREPARE_COUNT_ORDER);
  const countRows = [
    ...DOCUMENT_PACKAGE_PREPARE_COUNT_ORDER
      .filter((key) => Object.prototype.hasOwnProperty.call(counts, key))
      .map((key) => [key, counts[key]]),
    ...Object.entries(counts).filter(([key]) => !orderedCountKeys.has(key))
  ].filter(([, value]) => Number.isFinite(Number(value)));
  const paths = [
    report.output_file,
    report.metadata_file,
    report.context_file,
    ...(Array.isArray(report.output_files) ? report.output_files : [])
  ].map(packageText).filter((value, index, all) => value && all.indexOf(value) === index);
  const issues = [
    ...(Array.isArray(report.errors) ? report.errors : []),
    ...(Array.isArray(report.warnings) ? report.warnings : []),
    ...(Array.isArray(report.issues) ? report.issues : [])
  ].map(packageIssueMessage).filter(Boolean);
  return [
    summary ? '<p class="docsViewerPackagePrepare__summary">' + escapeHtml(summary) + '</p>' : "",
    countRows.length ? '<dl class="docsViewerPackagePrepare__counts">' + countRows.map(([key, value]) => (
      '<div><dt>' + escapeHtml(key.replace(/_/g, " ")) + '</dt><dd>' + escapeHtml(String(value)) + '</dd></div>'
    )).join("") + '</dl>' : "",
    paths.length ? '<section class="docsViewerPackagePrepare__resultSection"><strong>Files</strong>' + paths.map((path) => (
      '<code>' + escapeHtml(path) + '</code>'
    )).join("") + '</section>' : "",
    issues.length ? '<section class="docsViewerPackagePrepare__resultSection"><strong>Issues</strong><ul>' + issues.map((issue) => (
      '<li>' + escapeHtml(issue) + '</li>'
    )).join("") + '</ul></section>' : ""
  ].filter(Boolean).join("") || '<p>The action completed.</p>';
}

function openPrepareOptions(options) {
  const profiles = Array.isArray(options.profiles) ? options.profiles : [];
  const choicesByProfile = new Map();
  const contextByProfile = new Map(profiles.map((profile) => [
    packageText(profile && profile.profile_id),
    documentPackageExternalContext(profile)
  ]));
  let currentProfileId = packageText(profiles[0] && profiles[0].profile_id);

  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Prepare package",
    size: "compact",
    bodyHtml: optionsBodyHtml(),
    focusSelector: "[data-package-profile]",
    actions: [
      { role: "modal-primary", label: "Prepare package" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      const profileSelect = api.host.querySelector("[data-package-profile]");
      const targetFormatSelect = api.host.querySelector("[data-package-target-format]");
      const contentFormatField = api.host.querySelector("[data-package-content-format-field]");
      const contentFormatSelect = api.host.querySelector("[data-package-content-format]");
      const descendantsInput = api.host.querySelector("[data-package-include-descendants]");
      const missingSummaryField = api.host.querySelector("[data-package-missing-summary-field]");
      const missingSummaryInput = api.host.querySelector("[data-package-missing-summary-only]");
      const includeNonViewableField = api.host.querySelector("[data-package-include-non-viewable-field]");
      const includeNonViewableInput = api.host.querySelector("[data-package-include-non-viewable]");
      const description = api.host.querySelector("[data-package-profile-description]");
      const contextFields = api.host.querySelector("[data-package-context-fields]");
      let currentProjection = null;

      function captureCurrentProfile() {
        if (!currentProfileId) return;
        choicesByProfile.set(currentProfileId, {
          targetFormat: packageText(targetFormatSelect && targetFormatSelect.value),
          contentFormat: packageText(contentFormatSelect && contentFormatSelect.value),
          includeDescendants: Boolean(descendantsInput && descendantsInput.checked),
          missingSummaryOnly: Boolean(missingSummaryInput && missingSummaryInput.checked),
          includeNonViewable: Boolean(includeNonViewableInput && includeNonViewableInput.checked)
        });
        contextByProfile.set(currentProfileId, readContextFields(api.host));
      }

      function updateSelectionProjection() {
        const profile = documentPackageProfile(profiles, currentProfileId);
        if (!profile) return;
        currentProjection = projectDocumentPackageSelection({
          profile,
          documents: options.documents,
          checkedDocIds: options.checkedDocIds,
          includeDescendants: Boolean(descendantsInput && descendantsInput.checked),
          missingSummaryOnly: Boolean(missingSummaryInput && missingSummaryInput.checked),
          includeNonViewable: Boolean(includeNonViewableInput && includeNonViewableInput.checked)
        });
        writeSelectionProjection(api.host, currentProjection);
      }

      function renderCurrentProfile() {
        const profile = documentPackageProfile(profiles, currentProfileId);
        if (!profile) return;
        currentProfileId = packageText(profile.profile_id);
        const targetFormats = documentPackageTargetFormats(profile);
        const contentFormats = documentPackageContentFormats(profile);
        const choice = choicesByProfile.get(currentProfileId) || {};
        writeSelectOptions(
          targetFormatSelect,
          targetFormats,
          choice.targetFormat || packageText(profile.target_format) || targetFormats[0]
        );
        writeSelectOptions(
          contentFormatSelect,
          contentFormats,
          choice.contentFormat || packageText(profile.content_format) || contentFormats[0]
        );
        contentFormatField.hidden = !contentFormats.length;
        descendantsInput.checked = documentPackageProfileRequiresDescendants(profile)
          ? true
          : Object.prototype.hasOwnProperty.call(choice, "includeDescendants")
            ? choice.includeDescendants
            : documentPackageProfileIncludesDescendants(profile);
        descendantsInput.disabled = documentPackageProfileRequiresDescendants(profile);
        const selection = profile.selection && typeof profile.selection === "object"
          ? profile.selection
          : {};
        const supportsMissingSummaryOnly = selection.supports_missing_summary_only === true;
        missingSummaryField.hidden = !supportsMissingSummaryOnly;
        missingSummaryInput.disabled = !supportsMissingSummaryOnly;
        missingSummaryInput.checked = supportsMissingSummaryOnly
          ? Object.prototype.hasOwnProperty.call(choice, "missingSummaryOnly")
            ? choice.missingSummaryOnly
            : selection.default_missing_summary_only === true
          : false;
        const supportsIncludeNonViewable = selection.supports_include_non_viewable === true;
        includeNonViewableField.hidden = !supportsIncludeNonViewable;
        includeNonViewableInput.disabled = !supportsIncludeNonViewable;
        includeNonViewableInput.checked = supportsIncludeNonViewable
          ? Object.prototype.hasOwnProperty.call(choice, "includeNonViewable")
            ? choice.includeNonViewable
            : selection.include_non_viewable !== false
          : selection.include_non_viewable !== false;
        description.textContent = packageText(profile.description);
        contextFields.innerHTML = contextFieldsHtml(profile, contextByProfile.get(currentProfileId));
        updateSelectionProjection();
      }

      writeSelectOptions(
        profileSelect,
        profiles.map((profile) => packageText(profile && profile.profile_id)).filter(Boolean),
        currentProfileId,
        (profileId) => documentPackageProfileLabel(documentPackageProfile(profiles, profileId)) || profileId
      );
      profileSelect.addEventListener("change", function () {
        captureCurrentProfile();
        currentProfileId = packageText(profileSelect.value);
        renderCurrentProfile();
      });
      [descendantsInput, missingSummaryInput, includeNonViewableInput].forEach((input) => {
        input.addEventListener("change", updateSelectionProjection);
      });
      api.capturePrepareOptions = captureCurrentProfile;
      api.prepareOptionState = function () {
        captureCurrentProfile();
        updateSelectionProjection();
        return {
          choices: choicesByProfile.get(currentProfileId) || {},
          externalContext: contextByProfile.get(currentProfileId),
          profile: documentPackageProfile(profiles, currentProfileId),
          projection: currentProjection
        };
      };
      renderCurrentProfile();
    },
    onSubmit: function (api) {
      const state = api.prepareOptionState ? api.prepareOptionState() : null;
      const profile = state && state.profile;
      if (!profile) {
        api.setStatus("A document-package profile is required.");
        return false;
      }
      if (!state.projection || state.projection.total === 0) {
        api.setStatus("No documents remain for package preparation.");
        return false;
      }
      const missingContextValues = documentPackageExternalContextChanged(profile, state.externalContext)
        ? documentPackageExternalContextMissingValues(profile, state.externalContext)
        : [];
      if (missingContextValues.length) {
        api.setStatus("Complete every package context field: " + missingContextValues.join(", ") + ".");
        return false;
      }
      try {
        const request = createDocumentPackagePrepareRequest({
          scope: options.scope,
          profile,
          documents: options.documents,
          effectiveDocIds: state.projection.docIds,
          missingSummaryOnly: state.projection.missingSummaryOnly,
          includeNonViewable: state.projection.includeNonViewable,
          targetFormat: state.choices.targetFormat,
          contentFormat: state.choices.contentFormat,
          activityContext: options.activityContext
        });
        return {
          confirmed: true,
          externalContext: documentPackageExternalContextChanged(profile, state.externalContext)
            ? state.externalContext
            : null,
          profile,
          request
        };
      } catch (error) {
        api.setStatus(error && error.message ? error.message : "Package options are invalid.");
        return false;
      }
    }
  });
}

function resultPayloadForError(error) {
  if (error && error.payload && typeof error.payload === "object") return error.payload;
  const message = packageText(error && error.message) || "Document package preparation failed.";
  return { ok: false, summary_text: message, errors: [message] };
}

function showPrepareResult(options) {
  const payload = options.payload || {};
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: payload.ok === false ? "Document package was not prepared" : "Document package prepared",
    size: "compact",
    bodyHtml: documentPackagePrepareResultHtml(payload),
    actions: [{ role: "modal-primary", label: "Close" }]
  });
}

export async function openDocumentPackagePrepareWorkflow(options = {}) {
  const root = options.root || document.body;
  const scope = packageText(options.scope).toLowerCase();
  const checkedDocIds = normalizeCheckedDocIds(options.checkedDocIds);
  const callbacks = options.callbacks || {};
  const client = {
    getConfig: getDocumentPackageConfig,
    getDocuments: getPackageDocuments,
    prepare: prepareDocumentPackage,
    saveContext: saveDocumentPackageContext,
    ...(options.client || {})
  };
  const setBusy = (busy) => {
    if (typeof callbacks.setBusy === "function") callbacks.setBusy(Boolean(busy));
  };
  const setMessage = (message, isError) => {
    if (typeof callbacks.setMessage === "function") callbacks.setMessage(message, Boolean(isError));
  };

  if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
  if (!scope || !checkedDocIds.length) {
    const error = new Error(!scope ? "A Docs Viewer scope is required." : "Select one or more documents.");
    setMessage(error.message, true);
    return { confirmed: false, error };
  }

  let configPayload;
  let documentsPayload;
  let loadError = null;
  try {
    setBusy(true);
    setMessage("Loading package options...", false);
    [configPayload, documentsPayload] = await Promise.all([
      client.getConfig(),
      client.getDocuments(scope)
    ]);
  } catch (error) {
    loadError = error;
  } finally {
    setBusy(false);
  }
  if (loadError) {
    const payload = resultPayloadForError(loadError);
    setMessage(payload.summary_text, true);
    await showPrepareResult({ root, restoreFocus: options.restoreFocus, payload });
    return { confirmed: false, error: loadError, payload };
  }

  try {
    const workspace = configPayload && configPayload.workspace;
    if (!workspace || workspace.available !== true) {
      throw new Error(packageText(workspace && workspace.message) || "The document-package workspace is unavailable.");
    }
    const scopes = Array.isArray(configPayload.scopes) ? configPayload.scopes : [];
    if (!scopes.some((record) => packageText(record && record.scope) === scope)) {
      throw new Error("The active Docs Viewer scope is unavailable for package preparation.");
    }
    const profiles = Array.isArray(configPayload.profiles) ? configPayload.profiles : [];
    if (!profiles.length) throw new Error("No document-package profiles are available.");
    const documents = Array.isArray(documentsPayload && documentsPayload.records)
      ? documentsPayload.records
      : [];
    const eligibility = documentPackageSelectionEligibility(documents, checkedDocIds);
    if (eligibility.ineligibleDocIds.length) {
      throw new Error(
        "Checked documents are unavailable for package preparation: " + eligibility.ineligibleDocIds.join(", ")
      );
    }

    setMessage("", false);
    const result = await openPrepareOptions({
      root,
      restoreFocus: options.restoreFocus,
      scope,
      checkedDocIds,
      profiles,
      documents,
      activityContext: options.activityContext
    });
    if (!result || !result.confirmed) return { confirmed: false };

    setBusy(true);
    let payload;
    try {
      if (result.externalContext) {
        setMessage("Saving package context...", false);
        await client.saveContext({
          profile_id: packageText(result.profile.profile_id),
          external_context: result.externalContext,
          dry_run: false
        });
      }
      setMessage("Preparing document package...", false);
      payload = await client.prepare(result.request);
      setMessage(packageText(payload && payload.summary_text) || "Document package prepared.", false);
    } catch (error) {
      payload = resultPayloadForError(error);
      setMessage(packageText(payload.summary_text) || "Document package preparation failed.", true);
    } finally {
      setBusy(false);
    }
    await showPrepareResult({ root, restoreFocus: options.restoreFocus, payload });
    return { confirmed: true, ok: payload.ok !== false, payload, request: result.request };
  } catch (error) {
    const payload = resultPayloadForError(error);
    setMessage(payload.summary_text, true);
    await showPrepareResult({ root, restoreFocus: options.restoreFocus, payload });
    return { confirmed: false, error, payload };
  }
}
