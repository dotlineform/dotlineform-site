import { createCatalogueSeries, saveCatalogueSeries, applyCatalogueDelete } from "./catalogue-editor-service-client.js";
import { suggestNextSeriesId } from "./catalogue-series-records.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

/** New and Edit each own one Series; Delete is available only for an empty saved Series. */
export async function openWorkSeriesTitleModal(state, { seriesId = "", restoreFocus, onBusyChange } = {}) {
  const record = seriesId ? state.seriesById.get(seriesId) : null;
  let hasMembers = false;
  if (seriesId) {
    for (const work of state.workSearchById.values()) {
      if (work.series_id === seriesId) {
        hasMembers = true;
        break;
      }
    }
  }
  return openWorkDefinitionModal(state, {
    kind: "Series", id: seriesId, title: record?.title ?? "", restoreFocus, onBusyChange,
    deleteBlocked: hasMembers ? "Only Series with no member Works can be deleted." : "",
    deleteMessage: record ? `Delete “${record.title}” (${seriesId})? This Series has no member Works.` : "",
    async save(title) {
      if (seriesId) {
        return saveCatalogueSeries({ series_id: seriesId, record: { title } });
      }
      return createCatalogueSeries({ series_id: suggestNextSeriesId(state.seriesById.values()), record: { title } });
    },
    remove: () => applyCatalogueDelete({ kind: "series", series_id: seriesId })
  });
}
