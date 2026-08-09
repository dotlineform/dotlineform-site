var WORK_ID_PATTERN = /^\d{5}$/;
var DETAIL_ID_PATTERN = /^\d{3}$/;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function catalogueWorkDetailTitle(payload, workId, detailId) {
  var normalizedWorkId = cleanString(workId);
  var normalizedDetailId = cleanString(detailId);
  if (
    !WORK_ID_PATTERN.test(normalizedWorkId)
    || !DETAIL_ID_PATTERN.test(normalizedDetailId)
    || !payload
    || typeof payload !== "object"
  ) return "";
  var detail = payload.work_detail && typeof payload.work_detail === "object"
    ? payload.work_detail
    : {};
  var detailUid = normalizedWorkId + "-" + normalizedDetailId;
  if (
    cleanString(detail.work_id) !== normalizedWorkId
    || cleanString(detail.detail_id) !== normalizedDetailId
    || cleanString(detail.detail_uid) !== detailUid
  ) return "";
  var title = cleanString(detail.title);
  return title && !/[\r\n]/.test(title) ? title : "";
}

export function loadCatalogueWorkDetailTitle(workId, detailId, options = {}) {
  var normalizedWorkId = cleanString(workId);
  var normalizedDetailId = cleanString(detailId);
  var studioBaseUrl = cleanString(options.studioBaseUrl).replace(/\/+$/, "");
  if (
    !WORK_ID_PATTERN.test(normalizedWorkId)
    || !DETAIL_ID_PATTERN.test(normalizedDetailId)
    || !studioBaseUrl
  ) return Promise.resolve("");
  var detailUid = normalizedWorkId + "-" + normalizedDetailId;
  var fetchImpl = options.fetch || window.fetch.bind(window);
  return fetchImpl(
    studioBaseUrl
      + "/studio/api/catalogue/read?key=catalogue_work_detail_record&record_id="
      + encodeURIComponent(detailUid),
    {
      headers: { Accept: "application/json" }
    }
  ).then(function (response) {
    if (!response || !response.ok) return null;
    return response.json();
  }).then(function (payload) {
    return catalogueWorkDetailTitle(payload, normalizedWorkId, normalizedDetailId);
  }).catch(function () {
    return "";
  });
}
