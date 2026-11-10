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

/** Edit a Gallery in the current browse context or confirm removal of an empty Gallery. */
export async function openWorkGalleryModal(state, { galleryId = "", restoreFocus, onBusyChange, deleteEmpty = false } = {}) {
  const browsingGallery = state.browseKind === "gallery";
  const seriesId = browsingGallery || deleteEmpty ? null : state.draft.series_id || null;
  const series = seriesId ? state.seriesById.get(seriesId) : null;
  if (seriesId && (!series || series.series_id !== seriesId || typeof series.title !== "string")) {
    throw new Error("The displayed Series context is unavailable. Reload the Work before editing a Gallery.");
  }
  let title = "";
  let relatedToSeries = false;
  if (galleryId && seriesId) {
    const lookup = await loadStudioServerReadJson("catalogue_gallery_record", galleryId, { cache: "no-store" });
    if (lookup.gallery_id !== galleryId || lookup.record?.gallery_id !== galleryId
      || typeof lookup.record.title !== "string"
      || !Array.isArray(lookup.related_series_ids)) {
      throw new Error("Gallery lookup is missing its exact record or Series associations.");
    }
    title = lookup.record.title;
    relatedToSeries = lookup.related_series_ids.includes(seriesId);
  } else if (galleryId) {
    title = state.galleriesById.get(galleryId).title;
  }
  const canDelete = Boolean(galleryId) && (deleteEmpty || !browsingGallery);
  let deleteMessage = "";
  if (deleteEmpty) {
    deleteMessage = `Your Work changes were saved. “${title}” (${galleryId}) now has no Works. Deleting it also removes any Series-wide relevance for this Gallery.`;
  } else if (canDelete) {
    deleteMessage = () => {
      const count = savedGalleryMemberCount(state.workSearchById, galleryId);
      return `Delete “${title}” (${galleryId})? This removes it from ${count} Works.`;
    };
  }
  let deleteError = null;
  const result = await openWorkDefinitionModal(state, {
    kind: "Gallery", id: galleryId, title, restoreFocus, onBusyChange, deleteMessage,
    deleteOnly: deleteEmpty, cancelLabel: deleteEmpty ? "Keep Gallery" : "Cancel",
    checkbox: deleteEmpty ? null : {
      label: "Relates to all works in this series",
      context: browsingGallery ? "Edit Series-wide relevance in Series view."
        : series ? `Series: ${series.title} (${seriesId})` : "Choose a Series for this Work to enable this option.",
      checked: relatedToSeries,
      disabled: !series
    },
    save: (savedTitle, related) => {
      const payload = { gallery_id: galleryId || nextGalleryId(state.galleriesById), title: savedTitle,
        series_id: seriesId, related_to_series: Boolean(seriesId && related) };
      return galleryId ? saveCatalogueGallery(payload) : createCatalogueGallery(payload);
    },
    remove: canDelete ? async () => {
      try {
        return await deleteCatalogueGallery({ gallery_id: galleryId });
      } catch (error) {
        deleteError = error;
        throw error;
      }
    } : undefined
  });
  if (deleteEmpty && deleteError && !result.confirmed) throw deleteError;
  return result;
}
