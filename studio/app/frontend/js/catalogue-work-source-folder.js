import { openProjectMediaModal } from "./catalogue-project-media-picker.js";

/**
 * @typedef {Object} BulkSourceFolder
 * @property {string|null} media_source_id Null selects the configured default with canonical omission.
 * @property {string} project_folder Exact picker-selected project folder.
 * @property {string|null} project_subfolder Null selects the project folder itself.
 */

/**
 * Choose a common destination for a nonempty Work selection using loaded filenames.
 * Confirmation records only folder intent; Cancel leaves the draft unchanged.
 * Filenames, prepared media, dimensions and regeneration intent remain untouched.
 * The caller redraws the confirmed draft and owns normal Save/busy behavior.
 */
export async function openBulkWorkSourceFolder(state, options, mediaSourceId) {
  const works = state.bulkWorkIds.map(workId => state.bulkRecords.get(workId));
  const sameSource = mediaSourceId === options.getMediaSourceId();
  const result = await openProjectMediaModal(state, {
    ...options,
    selectionMode: "folder",
    requireSubfolder: false,
    initialSelection: {
      scope: mediaSourceId,
      folder: sameSource ? state.draft.project_folder : "",
      subfolder: sameSource ? state.draft.project_subfolder : "",
      filename: ""
    },
    validateSelection(selection) {
      const filenames = new Set(selection.filenames);
      const missing = works.filter(work => !filenames.has(work.project_filename));
      return missing.length
        ? "Missing source files for selected Works: " + missing.map(work =>
          `${work.work_id}: ${work.project_filename || "(no source filename)"}`
        ).join("; ")
        : "";
    }
  });
  if (!result?.confirmed) return result;
  const selection = result.selection;
  state.bulkSourceFolder = {
    media_source_id: selection.media_source_id === state.workMediaSourceConfig.defaultMediaSourceId
      ? null : selection.media_source_id,
    project_folder: selection.project_folder,
    project_subfolder: selection.project_subfolder || null
  };
  for (const [key, value] of Object.entries(state.bulkSourceFolder)) state.draft[key] = value ?? "";
  return result;
}
