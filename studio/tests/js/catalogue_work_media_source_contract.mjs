import assert from "node:assert/strict";

import {
  buildCreateWorkPayload,
  buildWorkDraftFromRecord,
  buildWorkRecordFromDraft
} from "../../app/frontend/js/catalogue-work-fields.js";
import {
  readProjectMediaFiles,
  readProjectMediaFolders,
  readWorkMediaSources
} from "../../app/frontend/js/catalogue-editor-service-client.js";
import {
  workSaveRequiresMediaPreparation
} from "../../app/frontend/js/catalogue-work-actions.js";


const defaultDraft = buildWorkDraftFromRecord({
  work_id: "00001",
  status: "draft",
  series_ids: [],
  title: "Default source"
});
assert.equal(defaultDraft.media_source_id, "");
assert.equal(buildWorkRecordFromDraft(defaultDraft).media_source_id, null);

const processingDraft = {
  ...defaultDraft,
  work_id: "00002",
  media_source_id: "processing",
  project_folder: "ink-engine",
  project_filename: "frame.jpg",
  title: "Processing source"
};
const processingRecord = buildCreateWorkPayload(processingDraft).record;
assert.equal(processingRecord.media_source_id, "processing");
assert.equal(processingRecord.project_folder, "ink-engine");

assert.equal(workSaveRequiresMediaPreparation({
  created: true,
  record: processingRecord
}), true);
assert.equal(workSaveRequiresMediaPreparation({
  created: true,
  record: { ...processingRecord, project_filename: null }
}), false);
assert.equal(workSaveRequiresMediaPreparation({
  changed_fields: ["title"],
  record: processingRecord
}), false);
assert.equal(workSaveRequiresMediaPreparation({
  changed_fields: ["project_filename"],
  record: processingRecord
}), true);
assert.equal(workSaveRequiresMediaPreparation({
  changed_fields: ["project_filename"],
  record: { ...processingRecord, project_filename: null }
}), false);

const requestedUrls = [];
globalThis.fetch = async (url) => {
  requestedUrls.push(String(url));
  return {
    ok: true,
    status: 200,
    async json() {
      return { ok: true };
    }
  };
};

await readWorkMediaSources();
await readProjectMediaFolders("processing", "ink");
await readProjectMediaFiles({
  mediaSourceId: "processing",
  projectFolder: "ink-engine",
  projectSubfolder: "details",
  query: "frame"
});

assert.deepEqual(requestedUrls, [
  "/studio/api/catalogue/project-media?mode=sources",
  "/studio/api/catalogue/project-media?mode=folders&media_source_id=processing&q=ink",
  "/studio/api/catalogue/project-media?mode=files&media_source_id=processing&project_folder=ink-engine&project_subfolder=details&q=frame"
]);

console.log("catalogue_work_media_source_contract: passed");
