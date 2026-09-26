/** Read Save-maintained titles as a private static asset; never query Catalogue records. */
export async function loadWorksCollectionSubjectTitles(options) {
  let studio;
  try {
    studio = new URL(options.studioBaseUrl);
  } catch (error) {
    throw new Error("Local Studio is not configured.", { cause: error });
  }
  if (studio.protocol !== "http:"
    || !["127.0.0.1", "localhost", "::1", "[::1]"].includes(studio.hostname)
    || studio.username || studio.password || studio.pathname !== "/" || studio.search || studio.hash) {
    throw new Error("Local Studio is not configured.");
  }
  const response = await (options.fetch || fetch)(new URL("/studio/catalogue-output/reports/works/manifest.json", studio), {
    cache: "no-store", headers: { Accept: "application/json" }
  });
  if (!response.ok) throw new Error("Works subject metadata is unavailable (" + response.status + ").");
  const payload = await response.json();
  if (!payload || Object.keys(payload).sort().join(",") !== "header,series,works"
    || !payload.header || Object.keys(payload.header).sort().join(",") !== "schema,version"
    || payload.header.schema !== "works_collection_metadata_v1"
    || typeof payload.header.version !== "string" || !/^[0-9a-f]{64}$/.test(payload.header.version)) {
    throw new Error("Works subject metadata is invalid.");
  }
  const titles = new Map();
  ["works", "series"].forEach((family) => {
    const rows = payload[family];
    if (!rows || typeof rows !== "object" || Array.isArray(rows)) {
      throw new Error("Works subject title map is invalid.");
    }
    Object.entries(rows).forEach(([key, title]) => {
      if (!(family === "works" ? /^\d{5}$/ : /^\d{3}$/).test(key)
        || typeof title !== "string" || !title.trim()) {
        throw new Error("Works subject title is invalid.");
      }
      titles.set((family === "works" ? "work" : "series") + ":" + key, title);
    });
  });
  return { available: true, titles: titles };
}
