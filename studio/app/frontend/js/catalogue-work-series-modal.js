import { createCatalogueSeries, saveCatalogueSeries, applyCatalogueDelete } from "./catalogue-editor-service-client.js";
import { suggestNextSeriesId } from "./catalogue-series-records.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

/** New and Edit each own one Series; Delete is available only for an empty saved Series. */
export async function openWorkSeriesTitleModal(state, { seriesId = "", restoreFocus, onBusyChange } = {}) {
  let lookup = null;
  if (seriesId) {
    lookup = await loadStudioServerReadJson("catalogue_lookup_series_base", seriesId, { cache: "no-store" });
    if (lookup.series?.series_id !== seriesId || !lookup.record_hash || typeof lookup.series.title !== "string"
      || !Array.isArray(lookup.member_works)) {
      throw new Error("Series lookup is missing its record, revision or members.");
    }
  }
  return openWorkDefinitionModal(state, {
    kind: "Series", id: seriesId, title: lookup?.series.title || "", restoreFocus, onBusyChange,
    deleteBlocked: lookup?.member_works.length ? "Only Series with no member Works can be deleted." : "",
    deleteMessage: lookup ? `Delete “${lookup.series.title}” (${seriesId})? This Series has no member Works.` : "",
    async save(title) {
      if (seriesId) {
        return saveCatalogueSeries({ series_id: seriesId, expected_record_hash: lookup.record_hash, record: { title } });
      }
      const search = await loadStudioServerReadJson("catalogue_lookup_series_search", "", { cache: "no-store" });
      if (!Array.isArray(search.items)) throw new Error("Series search lookup is unavailable.");
      return createCatalogueSeries({ series_id: suggestNextSeriesId(search.items), record: { title } });
    },
    remove: () => applyCatalogueDelete({ kind: "series", series_id: seriesId, expected_record_hash: lookup.record_hash })
  });
}
