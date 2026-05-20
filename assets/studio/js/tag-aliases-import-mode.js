import {
  probeStudioHealth
} from "./studio-transport.js";
import {
  normalize
} from "./tag-aliases-domain.js";
import {
  hideTagAliasesImportModal
} from "./tag-aliases-modals.js";

export function syncTagAliasesImportModeFromControl(state) {
  const mode = normalize(state.refs.importMode.value);
  if (mode === "replace") {
    state.importMode = "replace";
  } else if (mode === "merge") {
    state.importMode = "merge";
  } else {
    state.importMode = "add";
  }
}

export function closeTagAliasesImportModal(state, options = {}) {
  hideTagAliasesImportModal(state);
  if (typeof options.onModalStateChange === "function") {
    options.onModalStateChange();
  }
}

export async function probeTagAliasesImportMode(state, options = {}) {
  const ok = await probeStudioHealth(500);
  state.saveMode = ok ? "post" : "patch";
  state.importAvailable = ok;
  if (typeof options.onImportAvailabilityChange === "function") {
    options.onImportAvailabilityChange();
  }
  if (typeof options.onRouteStateChange === "function") {
    options.onRouteStateChange();
  }
}

export function renderTagAliasesImportAvailability(state, options = {}) {
  const available = Boolean(state.importAvailable && state.saveMode === "post");
  state.importAvailable = available;
  if (state.refs.openImportModal) state.refs.openImportModal.disabled = !available;
  if (state.refs.importButton) state.refs.importButton.disabled = !available;
  if (!available && state.importModalOpen) {
    closeTagAliasesImportModal(state, options);
  }
}
