import { getAnalyticsText } from "./analytics-config.js";
import {
  activateAnalyticsModalFrame,
  renderAnalyticsModalFrame
} from "./analytics-modal.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function contextFieldId(outputPath) {
  return `dataSharingPrepareContextField-${normalizeText(outputPath).replace(/[^A-Za-z0-9_-]+/g, "-")}`;
}

function contextForConfig(config) {
  const context = config && typeof config.external_context === "object" ? config.external_context : {};
  const descriptions = context && typeof context.field_descriptions === "object" ? context.field_descriptions : {};
  return {
    task: String(context.task || ""),
    response_guidance: String(context.response_guidance || ""),
    field_descriptions: descriptions
  };
}

function renderContextFieldRows(config, context) {
  const fields = Array.isArray(config && config.document_fields) ? config.document_fields : [];
  return fields.map((field) => {
    const outputPath = normalizeText(field && field.output_path);
    if (!outputPath) return "";
    const inputId = contextFieldId(outputPath);
    const description = context.field_descriptions && context.field_descriptions[outputPath]
      ? context.field_descriptions[outputPath]
      : "";
    return `
      <label class="analyticsForm__field dataSharingPrepareContextModal__field" for="${escapeHtml(inputId)}">
        <span class="analyticsForm__label">${escapeHtml(outputPath)}</span>
        <textarea
          class="analytics__input dataSharingPrepareContextModal__textarea"
          id="${escapeHtml(inputId)}"
          data-role="context-field-description"
          data-output-path="${escapeHtml(outputPath)}"
          rows="1"
        >${escapeHtml(description)}</textarea>
      </label>
    `;
  }).join("");
}

function renderContextEditorBody(state, config) {
  const context = contextForConfig(config);
  return `
    <label class="analyticsForm__field dataSharingPrepareContextModal__field" for="dataSharingPrepareContextTask">
      <span class="analyticsForm__label">${escapeHtml(getAnalyticsText(state.config, "data_sharing_prepare.context_task_label", "task"))}</span>
      <input
        class="analytics__input"
        id="dataSharingPrepareContextTask"
        data-role="context-task"
        type="text"
        autocomplete="off"
        spellcheck="false"
        value="${escapeHtml(context.task)}"
      >
    </label>
    <label class="analyticsForm__field dataSharingPrepareContextModal__field" for="dataSharingPrepareContextGuidance">
      <span class="analyticsForm__label">${escapeHtml(getAnalyticsText(state.config, "data_sharing_prepare.context_response_guidance_label", "response guidance"))}</span>
      <textarea
        class="analytics__input dataSharingPrepareContextModal__textarea dataSharingPrepareContextModal__textarea--guidance"
        id="dataSharingPrepareContextGuidance"
        data-role="context-response-guidance"
        rows="2"
      >${escapeHtml(context.response_guidance)}</textarea>
    </label>
    <div class="dataSharingPrepareContextModal__fields" role="group" aria-label="${escapeHtml(getAnalyticsText(state.config, "data_sharing_prepare.context_fields_label", "field descriptions"))}">
      ${renderContextFieldRows(config, context)}
    </div>
  `;
}

function readContextEditorPayload(host) {
  const task = normalizeText(host.querySelector('[data-role="context-task"]')?.value);
  const responseGuidance = normalizeText(host.querySelector('[data-role="context-response-guidance"]')?.value);
  const fieldDescriptions = {};
  host.querySelectorAll('[data-role="context-field-description"]').forEach((node) => {
    const outputPath = normalizeText(node.getAttribute("data-output-path"));
    if (!outputPath) return;
    fieldDescriptions[outputPath] = normalizeText(node.value);
  });
  return {
    task,
    response_guidance: responseGuidance,
    field_descriptions: fieldDescriptions
  };
}

function firstBlankField(host) {
  const selectors = [
    '[data-role="context-task"]',
    '[data-role="context-response-guidance"]',
    '[data-role="context-field-description"]'
  ];
  for (const selector of selectors) {
    const nodes = Array.from(host.querySelectorAll(selector));
    const blank = nodes.find((node) => !normalizeText(node.value));
    if (blank) return blank;
  }
  return null;
}

export function showDataSharingPrepareContextModal(state, config, onSave) {
  if (!state || !state.modalHost || !config) return Promise.resolve({ confirmed: false });
  state.modalHost.innerHTML = renderAnalyticsModalFrame({
    hidden: false,
    form: true,
    modalRole: "analytics-modal",
    backdropRole: "modal-cancel",
    titleId: "dataSharingPrepareContextModalTitle",
    title: getAnalyticsText(state.config, "data_sharing_prepare.context_title", "Edit context"),
    meta: config.label || config.id || "",
    size: "wide",
    bodyHtml: renderContextEditorBody(state, config),
    includeStatus: true,
    actions: [
      {
        role: "modal-cancel",
        label: getAnalyticsText(state.config, "data_sharing_prepare.context_cancel", "Cancel")
      },
      {
        role: "modal-primary",
        label: getAnalyticsText(state.config, "data_sharing_prepare.context_save", "Save"),
        primary: true
      }
    ]
  });
  const controller = activateAnalyticsModalFrame(state.modalHost, {
    restoreFocus: state.editContextButton,
    focusSelector: "#dataSharingPrepareContextTask",
    submitOnEnter: false,
    async onSubmit(api) {
      const blank = firstBlankField(api.host);
      if (blank) {
        api.setStatus(
          "error",
          getAnalyticsText(state.config, "data_sharing_prepare.context_required", "Complete every context field.")
        );
        blank.focus();
        return false;
      }
      const submitButton = api.host.querySelector('[data-role="modal-primary"]');
      if (submitButton) submitButton.disabled = true;
      api.setStatus("", getAnalyticsText(state.config, "data_sharing_prepare.context_saving", "Saving context..."));
      try {
        const payload = await onSave(readContextEditorPayload(api.host));
        return {
          externalContext: payload && payload.external_context ? payload.external_context : null
        };
      } catch (error) {
        if (submitButton) submitButton.disabled = false;
        api.setStatus(
          "error",
          normalizeText(error && error.message)
            || getAnalyticsText(state.config, "data_sharing_prepare.context_failed", "Context save failed.")
        );
        return false;
      }
    }
  });
  return controller.promise;
}
