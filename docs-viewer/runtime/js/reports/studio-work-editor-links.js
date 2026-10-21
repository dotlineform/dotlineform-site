/** Resolve local Studio once and build encoded Work/Series entry links without requests. */
export function createStudioWorkEditorLinks(studioBaseUrl) {
  let studio;
  try {
    studio = new URL(studioBaseUrl);
  } catch (error) {
    throw new Error("Local Studio is not configured.", { cause: error });
  }
  if (
    studio.protocol !== "http:"
    || !["127.0.0.1", "localhost", "::1", "[::1]"].includes(studio.hostname)
    || studio.username
    || studio.password
    || studio.pathname !== "/"
    || studio.search
    || studio.hash
  ) {
    throw new Error("Local Studio is not configured.");
  }
  const editorUrl = new URL("/studio/catalogue-work/", studio.origin).toString();
  return {
    forWork: workId => editorUrl + "?work=" + encodeURIComponent(workId),
    forSeries: seriesId => editorUrl + "?series=" + encodeURIComponent(seriesId)
  };
}
