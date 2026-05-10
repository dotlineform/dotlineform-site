import { displayValue } from "./catalogue-editor-records.js";
import {
  MOMENT_EDITABLE_FIELDS as EDITABLE_FIELDS,
  MOMENT_READONLY_FIELDS as READONLY_FIELDS,
  normalizeText
} from "./catalogue-moment-fields.js";

function notifyFieldInput(options, fieldKey) {
  if (options && typeof options.onFieldInput === "function") {
    options.onFieldInput(fieldKey);
  }
}

function renderField(field, fieldsNode, state, options) {
  const wrapper = document.createElement(field.readonly ? "div" : "label");
  wrapper.className = "tagStudioForm__field catalogueWorkForm__field";
  if (!field.readonly) wrapper.htmlFor = `catalogueMomentField-${field.key}`;

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
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
      option.textContent = optionValue;
      input.appendChild(option);
    });
  } else {
    input = document.createElement("input");
    input.className = "tagStudio__input";
    input.type = field.type === "date" ? "date" : "text";
    input.spellcheck = false;
    input.autocomplete = "off";
  }

  input.id = `catalogueMomentField-${field.key}`;
  input.dataset.field = field.key;
  if (!field.readonly) {
    input.addEventListener("input", () => notifyFieldInput(options, field.key));
    input.addEventListener("change", () => notifyFieldInput(options, field.key));
  }
  wrapper.appendChild(input);

  const message = document.createElement("span");
  message.className = "catalogueWorkForm__fieldStatus";
  message.dataset.fieldStatus = field.key;
  wrapper.appendChild(message);

  fieldsNode.appendChild(wrapper);
  state.fieldNodes.set(field.key, input);
  state.fieldStatusNodes.set(field.key, message);
}

function renderReadonlyField(field, readonlyNode, state) {
  const wrapper = document.createElement("div");
  wrapper.className = "tagStudioForm__field";

  const label = document.createElement("span");
  label.className = "tagStudioForm__label";
  label.textContent = field.label;
  wrapper.appendChild(label);

  const value = document.createElement("div");
  value.className = "tagStudio__input tagStudio__input--readonlyDisplay";
  value.textContent = "-";
  wrapper.appendChild(value);

  readonlyNode.appendChild(wrapper);
  state.readonlyNodes.set(field.key, value);
}

export function renderMomentEditorFields(fieldsNode, state, options = {}) {
  EDITABLE_FIELDS.forEach((field) => renderField(field, fieldsNode, state, options));
}

export function renderMomentReadonlyFields(readonlyNode, state) {
  READONLY_FIELDS.forEach((field) => renderReadonlyField(field, readonlyNode, state));
}

export function setMomentFieldNodeValue(node, value) {
  const text = normalizeText(value);
  if ("value" in node) {
    node.value = text;
  } else {
    node.textContent = displayValue(text, { emptyText: "-" });
  }
}

export function getMomentFieldNodeValue(node) {
  if ("value" in node) return node.value;
  return normalizeText(node.textContent);
}

export function applyMomentRecordToInputs(state, record) {
  const source = record || {};
  EDITABLE_FIELDS.forEach((field) => {
    const node = state.fieldNodes.get(field.key);
    if (!node) return;
    setMomentFieldNodeValue(node, normalizeText(source[field.key]));
  });
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = displayValue(source[field.key], { emptyText: "-" });
  });
}

export function clearMomentReadonly(state) {
  READONLY_FIELDS.forEach((field) => {
    const node = state.readonlyNodes.get(field.key);
    if (node) node.textContent = "-";
  });
}

export function clearMomentFieldMessages(state, options = {}) {
  state.fieldStatusNodes.forEach((node) => {
    if (options && typeof options.setTextWithState === "function") {
      options.setTextWithState(node, "");
    } else {
      node.textContent = "";
      delete node.dataset.state;
    }
  });
}

export function updateMomentFieldMessages(state, errors, options = {}) {
  clearMomentFieldMessages(state, options);
  errors.forEach((message, key) => {
    const node = state.fieldStatusNodes.get(key);
    if (!node) return;
    if (options && typeof options.setTextWithState === "function") {
      options.setTextWithState(node, message, "error");
    } else {
      node.textContent = message;
      node.dataset.state = "error";
    }
  });
}
