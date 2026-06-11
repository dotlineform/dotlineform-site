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

  function appendQuery(url, params) {
    var query = new URLSearchParams();
    Object.keys(params || {}).forEach(function (key) {
      var value = params[key];
      if (value == null || value === '') return;
      query.set(key, String(value));
    });
    var textQuery = query.toString();
    if (!textQuery) return url;
    return url + (url.indexOf('?') === -1 ? '?' : '&') + textQuery;
  }

  function catalogueIndexUrl(baseurl, options) {
    var opts = options || {};
    var params = {};
    var mode = text(opts.mode).toLowerCase();
    var seriesId = text(opts.series || opts.seriesId);
    var page = toPositiveInteger(opts.seriesPage || opts.series_page);
    var from = text(opts.from).toLowerCase();
    if (seriesId) {
      params.series = seriesId;
    } else if (mode === 'moments') {
      params.mode = 'moments';
    }
    if (page > 0) params.series_page = String(page);
    if (from) params.from = from;
    return appendQuery(buildPath(baseurl, '/series/'), params);
  }

  function worksUrl(baseurl, options) {
    return appendQuery(buildPath(baseurl, '/works/'), options || {});
  }

  function workUrl(workId, baseurl, options) {
    var id = text(workId);
    var params = Object.assign({}, options || {});
    if (id) params.work = id;
    return worksUrl(baseurl, params);
  }

  function workDetailUrl(detailUid, baseurl, options) {
    var id = text(detailUid);
    var params = Object.assign({}, options || {});
    if (id) params.detail = id;
    return appendQuery(buildPath(baseurl, '/work-details/'), params);
  }

  function momentUrl(momentId, baseurl, options) {
    var id = text(momentId);
    var params = Object.assign({}, options || {});
    if (id) params.moment = id;
    return appendQuery(buildPath(baseurl, '/moments/'), params);
  }

  function momentsRecoveryUrl(baseurl) {
    return buildPath(baseurl, '/moments/');
  }

  function notFoundRecoveryUrl(baseurl) {
    return catalogueIndexUrl(baseurl);
  }

  function parseRouteState(locationLike) {
    var source = locationLike || {};
    var params = new URLSearchParams(source.search || '');
    return {
      mode: text(params.get('mode')).toLowerCase() === 'moments' ? 'moments' : 'works',
      series: text(params.get('series')).toLowerCase(),
      work: text(params.get('work')),
      detail: text(params.get('detail')),
      moment: text(params.get('moment')),
      seriesPage: toPositiveInteger(params.get('series_page')),
      from: text(params.get('from')).toLowerCase()
    };
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

  function momentsIndexUrl(baseurl) {
    return buildPath(baseurl, '/assets/data/moments_index.json');
  }

  function seriesIndexUrl(baseurl) {
    return buildPath(baseurl, '/assets/data/series_index.json');
  }

  function worksIndexUrl(baseurl) {
    return buildPath(baseurl, '/assets/data/works_index.json');
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
      href: catalogueIndexUrl(baseurl, { series: id }),
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
      href = catalogueIndexUrl(baseurl, { series: seriesId });
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
    var navOptions = { series: seriesId };
    if (page > 0) navOptions.series_page = String(page);
    return {
      hidden: false,
      counterHidden: false,
      prevHref: workUrl(workIds[(index - 1 + workIds.length) % workIds.length], baseurl, navOptions),
      nextHref: workUrl(workIds[(index + 1) % workIds.length], baseurl, navOptions),
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
    appendQuery: appendQuery,
    catalogueIndexUrl: catalogueIndexUrl,
    worksUrl: worksUrl,
    momentUrl: momentUrl,
    momentsRecoveryUrl: momentsRecoveryUrl,
    notFoundRecoveryUrl: notFoundRecoveryUrl,
    parseRouteState: parseRouteState,
    workPayloadUrl: workPayloadUrl,
    seriesPayloadUrl: seriesPayloadUrl,
    momentPayloadUrl: momentPayloadUrl,
    momentsIndexUrl: momentsIndexUrl,
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
