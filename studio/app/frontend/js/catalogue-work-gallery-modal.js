import { createCatalogueGallery, saveCatalogueGallery, deleteCatalogueGallery } from "./catalogue-editor-service-client.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

/** Load exact Gallery definitions and saved Series relevance for this Work context. */
export async function openWorkGalleryModal(state, { galleryId = "", restoreFocus, onBusyChange } = {}) {
  const seriesId = state.draft.series_id || null;
  const series = seriesId ? state.seriesById.get(seriesId) : null;
  if (seriesId && (!series || series.series_id !== seriesId || typeof series.title !== "string")) {
    throw new Error("The displayed Series context is unavailable. Reload the Work before editing a Gallery.");
  }
  let lookup = null;
  if (galleryId) {
    lookup = await loadStudioServerReadJson("catalogue_gallery_record", galleryId, { cache: "no-store" });
    if (lookup.gallery_id !== galleryId || lookup.record?.gallery_id !== galleryId
      || typeof lookup.record.title !== "string" || !lookup.record_hash
      || !Array.isArray(lookup.member_work_ids) || !Array.isArray(lookup.related_series_ids)) {
      throw new Error("Gallery lookup is missing its exact record, members or Series associations.");
    }
  }
  return openWorkDefinitionModal(state, {
    kind: "Gallery", id: galleryId, title: lookup?.record.title || "", restoreFocus, onBusyChange,
    checkbox: {
      label: "Relates to all works in this series",
      context: series ? `Series: ${series.title} (${seriesId})` : "Choose a Series for this Work to enable this option.",
      checked: Boolean(galleryId && seriesId && lookup.related_series_ids.includes(seriesId)),
      disabled: !series
    },
    deleteMessage: lookup
      ? `Delete “${lookup.record.title}” (${galleryId})? This removes it from ${lookup.member_work_ids.length} Works and ${lookup.related_series_ids.length} Series associations.`
      : "",
    save: (title, related) => galleryId
      ? saveCatalogueGallery({ gallery_id: galleryId, expected_record_hash: lookup.record_hash,
        title, series_id: seriesId, related_to_series: related })
      : createCatalogueGallery({ title, series_id: seriesId, related_to_series: related }),
    remove: () => deleteCatalogueGallery({
      gallery_id: galleryId, expected_record_hash: lookup.record_hash,
      expected_member_work_ids: lookup.member_work_ids
    })
  });
}
