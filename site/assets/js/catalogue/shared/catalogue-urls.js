import { lowerText, text, toPositiveInteger } from './text.js';

export function trimBaseurl(value) {
  return text(value).replace(/\/$/, '');
}

export function buildPath(baseurl, path) {
  var pathText = text(path);
  if (!pathText) return trimBaseurl(baseurl) + '/';
  if (/^https?:\/\//i.test(pathText)) return pathText;
  return trimBaseurl(baseurl) + '/' + pathText.replace(/^\/+/, '');
}

export function appendQuery(url, params) {
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

export function catalogueIndexUrl(baseurl, options) {
  var opts = options || {};
  var params = {};
  var seriesId = text(opts.series || opts.seriesId);
  var page = toPositiveInteger(opts.seriesPage || opts.series_page);
  var from = lowerText(opts.from);
  if (seriesId) {
    params.series = seriesId;
  }
  if (page > 0) params.series_page = String(page);
  if (from) params.from = from;
  return appendQuery(buildPath(baseurl, '/series/'), params);
}

export function workUrl(workId, baseurl, options) {
  var params = Object.assign({}, options || {});
  var id = text(workId);
  if (id) params.work = id;
  return appendQuery(buildPath(baseurl, '/works/'), params);
}

export function workDetailUrl(detailUid, baseurl, options) {
  var params = Object.assign({}, options || {});
  var id = text(detailUid);
  if (id) params.detail = id;
  return appendQuery(buildPath(baseurl, '/work-details/'), params);
}

export function parseRouteState(locationLike) {
  var source = locationLike || {};
  var params = new URLSearchParams(source.search || '');
  return {
    series: lowerText(params.get('series')),
    work: text(params.get('work')),
    detail: text(params.get('detail')),
    seriesPage: toPositiveInteger(params.get('series_page')),
    from: lowerText(params.get('from')),
    detailsSection: lowerText(params.get('details_section')),
    detailsPage: toPositiveInteger(params.get('details_page'))
  };
}

export function seriesIndexUrl(baseurl) {
  return buildPath(baseurl, '/assets/data/series_index.json');
}

export function worksIndexUrl(baseurl) {
  return buildPath(baseurl, '/assets/data/works_index.json');
}

export function workPayloadUrl(workId, baseurl) {
  return buildPath(baseurl, '/assets/works/index/' + encodeURIComponent(text(workId)) + '.json');
}
