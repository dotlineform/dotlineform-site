/** Transient selected-image state; Save alone owns persistent media. */

export function workPixelsToCm(pixels) {
  return Math.round(pixels * 2.54 / 300 * 10) / 10;
}

export function clearWorkImagePreview(state) {
  const preview = state.imagePreview;
  state.imagePreview = null;
  if (!preview) return;
  preview.controller.abort();
  if (preview.url) URL.revokeObjectURL(preview.url);
}

/** An abandoned source must not leave its automatic dimensions in the draft. */
export function clearAutomaticWorkDimensions(state) {
  for (const key of state.automaticDimensionFields) {
    state.draft[key] = "";
    state.fieldNodes.get(key).value = "";
  }
  state.automaticDimensionFields.clear();
}

export function noteManualWorkDimension(state, key) {
  if (key !== "width_cm" && key !== "height_cm") return;
  state.manualDimensionFields.add(key);
  state.automaticDimensionFields.delete(key);
}

/** Apply only the current selection's result; metadata remains editable while awaiting it. */
export async function prepareWorkImagePreview(state, selection, { requestPreview, onStateChange }) {
  clearWorkImagePreview(state);
  clearAutomaticWorkDimensions(state);
  const preview = {
    controller: new AbortController(),
    status: "pending",
    filename: selection.project_filename,
    url: ""
  };
  state.imagePreview = preview;
  onStateChange();
  try {
    const result = await requestPreview(selection, { signal: preview.controller.signal });
    if (state.imagePreview !== preview) return;
    preview.url = URL.createObjectURL(result.blob);
    preview.width_px = result.width_px;
    preview.height_px = result.height_px;
    preview.status = "ready";
    for (const [key, pixels] of [["width_cm", result.width_px], ["height_cm", result.height_px]]) {
      if (state.manualDimensionFields.has(key) || state.draft[key] !== "") continue;
      const value = workPixelsToCm(pixels).toFixed(1);
      state.draft[key] = value;
      state.fieldNodes.get(key).value = value;
      state.automaticDimensionFields.add(key);
    }
  } catch (error) {
    if (state.imagePreview !== preview) return;
    preview.status = "error";
    preview.error = `Preview failed for ${preview.filename}: ${error.message}`;
  } finally {
    if (state.imagePreview === preview) onStateChange();
  }
}
