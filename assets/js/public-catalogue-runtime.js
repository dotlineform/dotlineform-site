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

  function momentPayloadUrl(momentId, baseurl) {
    return buildPath(baseurl, '/assets/moments/index/' + encodeURIComponent(text(momentId)) + '.json');
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

  function normalizeIds(raw) {
    if (!Array.isArray(raw)) return [];
    return raw.map(function (id) { return text(id); }).filter(Boolean);
  }

  function seriesIndexRow(payload, seriesId) {
    if (!payload || !payload.series || typeof payload.series !== 'object') return null;
    var row = payload.series[text(seriesId)];
    return row && typeof row === 'object' ? row : null;
  }

  function seriesIndexWorkIds(payload, seriesId) {
    var row = seriesIndexRow(payload, seriesId);
    if (!row || !Array.isArray(row.works)) return [];
    return normalizeIds(row.works);
  }

  function seriesIndexTitle(payload, seriesId) {
    var row = seriesIndexRow(payload, seriesId);
    return row ? text(row.title) : '';
  }

  function projectWorkSeriesLink(payload, seriesId, baseurl) {
    var id = text(seriesId);
    if (!id) {
      return {
        label: '',
        href: trimBaseurl(baseurl) + '/series/',
        hidden: true
      };
    }
    var ids = seriesIndexWorkIds(payload, id);
    return {
      label: seriesIndexTitle(payload, id) || id,
      href: trimBaseurl(baseurl) + '/series/' + encodeURIComponent(id) + '/',
      hidden: ids.length <= 1
    };
  }

  function projectWorkBackLink(payload, options) {
    var seriesId = text(options && options.seriesId);
    if (!seriesId) return null;
    var label = seriesIndexTitle(payload, seriesId);
    if (!label) return null;
    var baseurl = trimBaseurl(options && options.baseurl);
    var fromSeriesId = text(options && options.seriesFromQuery);
    var fromContext = text(options && options.fromContext).toLowerCase();
    var href = '';
    var textValue = '';
    if (fromSeriesId && fromSeriesId === seriesId) {
      textValue = '\u2190 ' + label;
    } else if (!fromSeriesId && !fromContext) {
      textValue = '\u2190 ' + label;
      href = baseurl + '/series/' + encodeURIComponent(seriesId) + '/';
    }
    return {
      label: textValue,
      seriesLabel: label,
      href: href
    };
  }

  function projectWorkSeriesNavigation(ids, currentId, options) {
    var workIds = normalizeIds(ids);
    var current = text(currentId);
    var seriesId = text(options && options.seriesId);
    if (!seriesId || !current) return { hidden: true, counterHidden: true };
    var index = workIds.indexOf(current);
    if (index === -1 || workIds.length < 2) return { hidden: true, counterHidden: true };
    var baseurl = trimBaseurl(options && options.baseurl);
    var page = toPositiveInteger(options && options.seriesPage);
    var qs = '?series=' + encodeURIComponent(seriesId);
    if (page > 0) qs += '&series_page=' + encodeURIComponent(String(page));
    return {
      hidden: false,
      counterHidden: false,
      prevHref: baseurl + '/works/' + workIds[(index - 1 + workIds.length) % workIds.length] + '/' + qs,
      nextHref: baseurl + '/works/' + workIds[(index + 1) % workIds.length] + '/' + qs,
      counterText: String(index + 1) + '/' + String(workIds.length)
    };
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
    momentPayloadUrl: momentPayloadUrl,
    seriesIndexUrl: seriesIndexUrl,
    worksIndexUrl: worksIndexUrl,
    workUrl: workUrl,
    workDetailUrl: workDetailUrl,
    thumbUrl: thumbUrl,
    thumbSrcset: thumbSrcset,
    getWorkRecord: getWorkRecord,
    normalizeIds: normalizeIds,
    seriesIndexRow: seriesIndexRow,
    seriesIndexWorkIds: seriesIndexWorkIds,
    seriesIndexTitle: seriesIndexTitle,
    projectWorkSeriesLink: projectWorkSeriesLink,
    projectWorkBackLink: projectWorkBackLink,
    projectWorkSeriesNavigation: projectWorkSeriesNavigation
  };

  if (!window.__dlfGetWorkRecord) {
    window.__dlfGetWorkRecord = getWorkRecord;
  }
})();
