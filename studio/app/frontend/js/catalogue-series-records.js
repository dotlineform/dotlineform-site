function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

/** Search canonical Series IDs and titles, keeping the browser's bounded ID order. */
export function getSeriesSearchMatches(seriesById, rawQuery) {
  const query = normalizeText(rawQuery).toLowerCase();
  if (!query) return [];
  const matches = [];
  for (const [seriesId, record] of seriesById) {
    if (seriesId.includes(query) || normalizeText(record.title).toLowerCase().includes(query)) {
      matches.push({ seriesId, record });
    }
  }
  matches.sort((a, b) => a.seriesId.localeCompare(b.seriesId, undefined, { numeric: true, sensitivity: "base" }));
  return matches.slice(0, 20);
}

/** Suggest the next numeric ID from a fresh lookup; creation still checks for collisions. */
export function suggestNextSeriesId(seriesItems) {
  let maxNumericId = 0;
  for (const record of seriesItems) {
    const seriesId = normalizeText(record.series_id);
    if (/^\d+$/.test(seriesId)) maxNumericId = Math.max(maxNumericId, Number(seriesId));
  }
  return String(maxNumericId + 1).padStart(3, "0");
}
