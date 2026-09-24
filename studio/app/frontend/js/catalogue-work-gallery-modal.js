import { createCatalogueGallery, saveCatalogueGallery, deleteCatalogueGallery } from "./catalogue-editor-service-client.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

/** Load the exact Gallery and membership revision before editing or confirming global removal. */
export async function openWorkGalleryModal(state, { galleryId = "", restoreFocus, onBusyChange } = {}) {
  let lookup = null;
  if (galleryId) {
    lookup = await loadStudioServerReadJson("catalogue_gallery_record", galleryId, { cache: "no-store" });
    if (lookup.gallery_id !== galleryId || lookup.record?.gallery_id !== galleryId
      || typeof lookup.record.title !== "string" || !lookup.record_hash || !Array.isArray(lookup.member_work_ids)) {
      throw new Error("Gallery lookup is missing its exact record, revision or members.");
    }
  }
  return openWorkDefinitionModal(state, {
    kind: "Gallery", id: galleryId, title: lookup?.record.title || "", restoreFocus, onBusyChange,
    deleteMessage: lookup
      ? `Delete “${lookup.record.title}” (${galleryId}) and remove it from all ${lookup.member_work_ids.length} associated Works?`
      : "",
    save: title => galleryId
      ? saveCatalogueGallery({ gallery_id: galleryId, expected_record_hash: lookup.record_hash, title })
      : createCatalogueGallery({ title }),
    remove: () => deleteCatalogueGallery({
      gallery_id: galleryId, expected_record_hash: lookup.record_hash,
      expected_member_work_ids: lookup.member_work_ids
    })
  });
}
