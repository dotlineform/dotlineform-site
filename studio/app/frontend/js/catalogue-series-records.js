function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

/** Suggest the next numeric ID from loaded definitions; creation still checks for collisions. */
export function suggestNextSeriesId(seriesItems) {
  let maxNumericId = 0;
  for (const record of seriesItems) {
    const seriesId = normalizeText(record.series_id);
    if (/^\d+$/.test(seriesId)) maxNumericId = Math.max(maxNumericId, Number(seriesId));
  }
  return String(maxNumericId + 1).padStart(3, "0");
}
