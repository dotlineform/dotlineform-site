(function () {
  if (window.__dlfPublicCatalogueRuntime) return;

  var workRecordCache = {};

  function text(value) {
    return String(value == null ? '' : value).trim();
  }

  function trimBaseurl(value) {
    return text(value).replace(/\/$/, '');
  }

  function toNumber(value) {
    var number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function toPositiveInteger(value) {
    var number = Number(value);
    return Number.isFinite(number) && number > 0 ? Math.floor(number) : 0;
  }

  function normalizePositiveSizes(raw, fallback) {
    var values = Array.isArray(raw) ? raw : [];
    var sizes = values
      .map(toPositiveInteger)
      .filter(function (value) { return value > 0; });
    return sizes.length ? sizes : (Array.isArray(fallback) ? fallback.slice() : []);
  }

  function slug(value) {
    return text(value)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function fetchJson(url) {
    return fetch(url, { cache: 'default' })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      });
  }

  function buildPath(baseurl, path) {
    var pathText = text(path);
    if (!pathText) return trimBaseurl(baseurl) + '/';
    if (/^https?:\/\//i.test(pathText)) return pathText;
    return trimBaseurl(baseurl) + '/' + pathText.replace(/^\/+/, '');
  }

  function workPayloadUrl(workId, baseurl) {
    return buildPath(baseurl, '/assets/works/index/' + encodeURIComponent(text(workId)) + '.json');
  }

  function seriesPayloadUrl(seriesId, baseurl) {
    return buildPath(baseurl, '/assets/series/index/' + encodeURIComponent(text(seriesId)) + '.json');
  }

  function seriesIndexUrl(baseurl) {
    return buildPath(baseurl, '/assets/data/series_index.json');
  }

  function worksIndexUrl(baseurl) {
    return buildPath(baseurl, '/assets/data/works_index.json');
  }

  function workUrl(workId, baseurl) {
    return buildPath(baseurl, '/works/' + encodeURIComponent(text(workId)) + '/');
  }

  function workDetailUrl(detailUid, baseurl) {
    return buildPath(baseurl, '/work_details/' + encodeURIComponent(text(detailUid)) + '/');
  }

  function thumbUrl(base, id, suffix, size, format) {
    return text(base) + text(id) + '-' + text(suffix) + '-' + text(size) + '.' + text(format);
  }

  function thumbSrcset(base, id, sizes, suffix, format) {
    return (Array.isArray(sizes) ? sizes : [])
      .map(function (size) {
        return thumbUrl(base, id, suffix, size, format) + ' ' + size + 'w';
      })
      .join(', ');
  }

  function getWorkRecord(workId, baseurl) {
    var id = text(workId);
    if (!id) return Promise.resolve(null);
    var key = trimBaseurl(baseurl) + '|' + id;
    if (workRecordCache[key]) return workRecordCache[key];
    workRecordCache[key] = fetchJson(workPayloadUrl(id, baseurl))
      .catch(function () {
        return null;
      });
    return workRecordCache[key];
  }

  window.__dlfPublicCatalogueRuntime = {
    text: text,
    trimBaseurl: trimBaseurl,
    toNumber: toNumber,
    toPositiveInteger: toPositiveInteger,
    normalizePositiveSizes: normalizePositiveSizes,
    slug: slug,
    fetchJson: fetchJson,
    buildPath: buildPath,
    workPayloadUrl: workPayloadUrl,
    seriesPayloadUrl: seriesPayloadUrl,
    seriesIndexUrl: seriesIndexUrl,
    worksIndexUrl: worksIndexUrl,
    workUrl: workUrl,
    workDetailUrl: workDetailUrl,
    thumbUrl: thumbUrl,
    thumbSrcset: thumbSrcset,
    getWorkRecord: getWorkRecord
  };

  if (!window.__dlfGetWorkRecord) {
    window.__dlfGetWorkRecord = getWorkRecord;
  }
})();
