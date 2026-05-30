export function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function buildSaveModeText(config, mode, studioText) {
  const label = mode === "post"
    ? studioText(config, "save_mode_local_server", "Local server")
    : studioText(config, "save_mode_offline", "Offline session");
  return studioText(config, "save_mode_template", "Save mode: {mode}", { mode: label });
}
