/** Prepare completed Refresh facts and own search, ordering and TSV projection. */

const SORT_COLLATOR = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
export const COLUMN_MODEL = Object.freeze([
  { id: "work", label: "Work", visibility: "both", sortable: true, copy: "both" },
  { id: "year", label: "Year", visibility: "both", sortable: true, copy: "both" },
  { id: "title", label: "Title", visibility: "both", sortable: true, copy: "both" },
  { id: "series", label: "Series", visibility: "both", sortable: true, copy: "both" },
  { id: "storage", label: "Storage", visibility: "both", sortable: true, copy: "both" },
  { id: "medium", label: "Medium", visibility: "expanded", sortable: false, copy: "expanded" },
  { id: "source", label: "Source image", visibility: "expanded", sortable: false, copy: "expanded" }
].map((column) => Object.freeze(column)));
export const COPY_COLUMN_IDS = Object.freeze(COLUMN_MODEL.filter((column) => column.copy === "both").map((column) => column.id));
export const PRESENTATION_COLUMNS = Object.freeze(COLUMN_MODEL.map((column) => Object.freeze({
  id: column.id, label: column.label, visibility: column.visibility
})));

function visibleString(value) {
  return value.trim().replace(/\s+/g, " ");
}

function searchString(value) {
  return visibleString(value).normalize("NFKC").toLocaleLowerCase("en");
}

function sourceImagePath(value) {
  const folder = value.project_folder;
  const subfolder = value.project_subfolder;
  const filename = value.project_filename;
  if (folder === null || folder === "" || filename === null || filename === "") return "";
  return subfolder === null || subfolder === ""
    ? folder + "/" + filename
    : folder + "/" + subfolder + "/" + filename;
}

/** Trust saved identities/labels; normalize only derived search and sort values. */
export function prepareCatalogueWorksRows(payload) {
  return Object.values(payload.works).map((value) => {
    const series = value.series.map((record) => ({ seriesId: record.series_id, title: record.title }));
    return {
      medium: value.medium,
      searchValues: [value.work_id, value.title, ...series.flatMap((record) => [record.seriesId, record.title])].map(searchString),
      series,
      seriesSortValue: series.map((record) => visibleString(record.title) + " " + record.seriesId).join(" "),
      sourceImagePath: sourceImagePath(value),
      storage: value.storage_location,
      title: value.title,
      workId: value.work_id,
      year: value.year,
      yearDisplay: value.year_display
    };
  });
}

function compareRows(left, right, key) {
  if (key === "year") return left.year - right.year;
  const field = key === "work" ? "workId" : key === "series" ? "seriesSortValue" : key;
  return SORT_COLLATOR.compare(left[field], right[field]);
}

/** A null previous projection explicitly starts a newly loaded dataset. */
export function projectCatalogueWorks(rows, previous, { searchText, sortKey, sortDir }) {
  const query = searchString(searchText);
  const queryChanged = previous === null || previous.query !== query;
  const orderChanged = queryChanged || previous.sortKey !== sortKey || previous.sortDir !== sortDir;
  const matching = queryChanged
    ? (query ? rows.filter((row) => row.searchValues.some((value) => value.includes(query))) : [])
    : (orderChanged ? previous.rows.slice() : previous.rows);
  if (orderChanged) matching.sort((left, right) => {
    const primary = compareRows(left, right, sortKey);
    if (primary !== 0) return sortDir === "asc" ? primary : -primary;
    return SORT_COLLATOR.compare(left.workId, right.workId);
  });
  return { columns: COPY_COLUMN_IDS, rows: matching, query, searchText: visibleString(searchText), sortDir, sortKey, totalCount: rows.length };
}

function seriesCellText(row) {
  return row.series.length
    ? row.series.map((record) => record.title + " [" + record.seriesId + "]").join("; ")
    : "—";
}

function tsvCell(value) {
  return value === null ? "" : value.replace(/\r\n|[\t\r\n]/g, " ");
}

/** Build cell values once per exported row; preserve display text and TSV escaping. */
export function serializeCatalogueWorksTsv(rows, columnIds) {
  const lines = [columnIds.map((id) => COLUMN_MODEL.find((column) => column.id === id).label).join("\t")];
  rows.forEach((row) => {
    const values = {
      work: row.workId, year: row.yearDisplay, title: row.title,
      series: seriesCellText(row), storage: row.storage, medium: row.medium, source: row.sourceImagePath
    };
    lines.push(columnIds.map((id) => tsvCell(values[id])).join("\t"));
  });
  return lines.join("\n");
}
