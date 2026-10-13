import { createCatalogueGallery, saveCatalogueGallery, deleteCatalogueGallery } from "./catalogue-editor-service-client.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

function nextGalleryId(galleriesById) {
  let highestId = 0;
  for (const id of galleriesById.keys()) highestId = Math.max(highestId, Number(id));
  return String(highestId + 1).padStart(3, "0");
}

function savedGalleryMemberCount(workSearchById, galleryId) {
  let count = 0;
  for (const work of workSearchById.values()) {
    if (work.gallery_ids.includes(galleryId)) count += 1;
  }
  return count;
}

/** Edit saved Gallery relevance, or confirm UI-detected cleanup from the loaded definition. */
export async function openWorkGalleryModal(state, { galleryId = "", restoreFocus, onBusyChange, deleteEmpty = false } = {}) {
  const seriesId = deleteEmpty ? null : state.draft.series_id || null;
  const series = seriesId ? state.seriesById.get(seriesId) : null;
  if (seriesId && (!series || series.series_id !== seriesId || typeof series.title !== "string")) {
    throw new Error("The displayed Series context is unavailable. Reload the Work before editing a Gallery.");
  }
  let lookup = null;
  if (galleryId && !deleteEmpty) {
    lookup = await loadStudioServerReadJson("catalogue_gallery_record", galleryId, { cache: "no-store" });
    if (lookup.gallery_id !== galleryId || lookup.record?.gallery_id !== galleryId
      || typeof lookup.record.title !== "string"
      || !Array.isArray(lookup.related_series_ids)) {
      throw new Error("Gallery lookup is missing its exact record or Series associations.");
    }
  }
  const gallery = deleteEmpty ? state.galleriesById.get(galleryId) : lookup?.record;
  let deleteError = null;
  const result = await openWorkDefinitionModal(state, {
    kind: "Gallery", id: galleryId, title: gallery ? gallery.title : "", restoreFocus, onBusyChange,
    deleteOnly: deleteEmpty, cancelLabel: deleteEmpty ? "Keep Gallery" : "Cancel",
    checkbox: deleteEmpty ? null : {
      label: "Relates to all works in this series",
      context: series ? `Series: ${series.title} (${seriesId})` : "Choose a Series for this Work to enable this option.",
      checked: Boolean(galleryId && seriesId && lookup.related_series_ids.includes(seriesId)),
      disabled: !series
    },
    deleteMessage: deleteEmpty
      ? `Your Work changes were saved. “${gallery.title}” (${galleryId}) now has no Works. Delete this Gallery?`
      : lookup
      ? `Delete “${lookup.record.title}” (${galleryId})? This removes it from ${savedGalleryMemberCount(state.workSearchById, galleryId)} Works.`
      : "",
    save: (title, related) => galleryId
      ? saveCatalogueGallery({ gallery_id: galleryId, title, series_id: seriesId, related_to_series: related })
      : createCatalogueGallery({ gallery_id: nextGalleryId(state.galleriesById),
        title, series_id: seriesId, related_to_series: related }),
    async remove() {
      try {
        return await deleteCatalogueGallery({ gallery_id: galleryId });
      } catch (error) {
        deleteError = error;
        throw error;
      }
    }
  });
  if (deleteEmpty && deleteError && !result.confirmed) throw deleteError;
  return result;
}
