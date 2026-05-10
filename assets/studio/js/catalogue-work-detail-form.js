import { displayValue } from "./catalogue-editor-records.js";
import {
  WORK_DETAIL_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_DETAIL_FIELD_DEFINITIONS,
  WORK_DETAIL_READONLY_FIELDS as READONLY_FIELDS,
  normalizeText
} from "./catalogue-work-detail-fields.js";

export const WORK_DETAIL_FORM_FIELDS = Object.freeze([
  WORK_DETAIL_FIELD_DEFINITIONS.work_id,
  WORK_DETAIL_FIELD_DEFINITIONS.detail_id,
  ...EDITABLE_FIELDS
]);

function formText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((text, [token, value]) => {
    return text.replace(new RegExp(`\\{${token}\\}`, "g"), value == null ? "" : String(value));
  }, fallback);
}

function notifyFieldInput(options, fieldKey) {
  if (options && typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  }
}

export function setWorkDetailFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text);
  }
}

export function getWorkDetailFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

function renderField(field, fieldsNode, state, options) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (!field.readonly) wrapper.htmlFor = `catalogueWorkDetailField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.dataset.fieldLabel = field.key;
  label.textContent = formText(options, `field_label_${field.key}`, field.label);
  wrapper.appendChild(label);

  let input;
  if (field.readonly) {
    input = document.createElement("span");
    input.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  } else if (field.type === "select") {
    input = document.createElement("select");
    input.className = "tagStudio__input";
    field.options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue || "(blank)";
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = "text";
  }

  input.id = `catalogueWorkDetailField-${field.key}`;
  input.dataset.field = field.key;
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  if (!field.readonly) {
    input.addEventListener("input", () => notifyFieldInput(options, field.key));
    input.addEventListener("change", () => notifyFieldInput(options, field.key));
  }
  fieldsNode.appendChild(wrapper);
  state.fieldWrappers.set(field.key, wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state, options) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.dataset.fieldLabel = field.key;
  label.textContent = formText(options, `field_label_${field.key}`, field.label);
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.dataset.readonlyField = field.key;
  value.textContent = "—";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

export function renderWorkDetailEditorFields(fieldsNode, state, options = {}) {
  WORK_DETAIL_FORM_FIELDS.forEach((field) => renderField(field, fieldsNode, state, options));
}

export function renderWorkDetailReadonlyFields(readonlyNode, state, options = {}) {
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state, options));
}

export function applyWorkDetailFieldLabels(state, options = {}) {
  [...WORK_DETAIL_FORM_FIELDS, ...READONLY_FIELDS].forEach((field) => {
    const labels = state.root.querySelectorAll(`[data-field-label="${field.key}"]`);
    labels.forEach((label) => {
      label.textContent = formText(options, `field_label_${field.key}`, field.label);
    });
  });
}

export function applyWorkDetailDraftToInputs(state) {
  WORK_DETAIL_FORM_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setWorkDetailFieldNodeValue(node, normalizeText(state.draft[field.key]));
  });
}

export function applyWorkDetailReadonly(state) {
  setWorkDetailReadonlyValues(state, (field) => state.currentRecord ? state.currentRecord[field.key] : "");
}

export function setWorkDetailReadonlyValues(state, valueForField) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (!node) return;
    const value = typeof valueForField === "function" ? valueForField(field) : valueForField;
    node.textContent = displayValue(value);
  });
}

export function setWorkDetailModeFieldAvailability(state) {
  WORK_DETAIL_FORM_FIELDS.forEach((field) => {
    const wrapper = state.fieldWrappers.get(field.key);
    const node = state.fieldNodes.get(field.key);
    const newModeOnly = field.key === "work_id" || field.key === "detail_id";
    if (wrapper) wrapper.hidden = newModeOnly && state.mode !== "new";
    if (!node) return;
    if ("disabled" in node) node.disabled = state.isSaving || state.isBuilding || state.isDeleting;
    if (state.mode === "new" && (field.key === "work_id" || field.key === "status")) {
      if ("disabled" in node) node.disabled = true;
    }
  });
}

export function updateWorkDetailFieldMessages(state, errors, options = {}) {
  WORK_DETAIL_FORM_FIELDS.forEach((field) => {
    const messageNode = state.fieldStatusNodes.get(field.key);
    if (!messageNode) return;
    let message = errors.get(field.key) || "";
    if (!message && state.mode === "bulk" && state.bulkMixedFields.has(field.key) && !state.bulkTouchedFields.has(field.key)) {
      message = formText(options, "bulk_field_mixed", "Mixed values across selection. Leave untouched to preserve per-record values.");
    }
    messageNode.textContent = message;
    messageNode.hidden = !message;
  });
}
