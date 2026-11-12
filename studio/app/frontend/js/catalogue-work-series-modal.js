import { saveCatalogueSeries, applyCatalogueDelete } from "./catalogue-editor-service-client.js";
import { openWorkDefinitionModal } from "./catalogue-work-definition-modal.js";

/** Edit one Series; Delete is available only for an empty saved Series. */
export async function openWorkSeriesTitleModal(state, { seriesId, restoreFocus, onBusyChange }) {
  const record = state.seriesById.get(seriesId);
  let hasMembers = false;
  for (const work of state.workSearchById.values()) {
    if (work.series_id === seriesId) {
      hasMembers = true;
      break;
    }
  }
  return openWorkDefinitionModal(state, {
    kind: "Series", id: seriesId, title: record.title, restoreFocus, onBusyChange,
    deleteBlocked: hasMembers ? "Only Series with no member Works can be deleted." : "",
    deleteMessage: `Delete “${record.title}” (${seriesId})? This Series has no member Works.`,
    save: ({ title }) => saveCatalogueSeries({ series_id: seriesId, record: { title } }),
    remove: () => applyCatalogueDelete({ kind: "series", series_id: seriesId })
  });
}
