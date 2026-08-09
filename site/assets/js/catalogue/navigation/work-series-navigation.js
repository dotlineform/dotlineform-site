import { catalogueIndexUrl, seriesPayloadUrl, trimBaseurl, workUrl } from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { text, toPositiveInteger } from '../shared/text.js';

function normalizeIds(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map(function (id) { return text(id); }).filter(Boolean);
}

function exactSeriesRecord(payload, seriesId) {
  var expectedId = text(seriesId);
  var series = payload && payload.series && typeof payload.series === 'object' ? payload.series : null;
  if (!expectedId || !series) return null;
  if (text(series.series_id) !== expectedId || text(series.status).toLowerCase() !== 'published') return null;
  return series;
}

export function exactSeriesWorkIds(payload, seriesId) {
  if (!exactSeriesRecord(payload, seriesId)) return [];
  var memberWorks = Array.isArray(payload && payload.member_works) ? payload.member_works : [];
  return normalizeIds(memberWorks.map(function (work) {
    return work && typeof work === 'object' ? work.work_id : '';
  }));
}

export function exactSeriesTitle(payload, seriesId) {
  var series = exactSeriesRecord(payload, seriesId);
  return series ? text(series.title) : '';
}

export function projectExactSeriesLink(payload, seriesId, currentWorkId, baseurl) {
  var id = text(seriesId);
  var workId = text(currentWorkId);
  var ids = exactSeriesWorkIds(payload, id);
  var title = exactSeriesTitle(payload, id);
  if (!id || !workId || !title || ids.indexOf(workId) === -1) {
    return {
      label: '',
      href: trimBaseurl(baseurl) + '/series/',
      hidden: true
    };
  }
  return {
    label: title,
    href: catalogueIndexUrl(baseurl, { series: id }),
    hidden: ids.length <= 1
  };
}

export function projectExactSeriesBackLink(payload, options) {
  var seriesId = text(options && options.seriesId);
  var currentWorkId = text(options && options.currentWorkId);
  var ids = exactSeriesWorkIds(payload, seriesId);
  var label = exactSeriesTitle(payload, seriesId);
  if (!seriesId || !currentWorkId || !label || ids.indexOf(currentWorkId) === -1) return null;
  var fromSeriesId = text(options && options.seriesFromQuery);
  var fromContext = text(options && options.fromContext).toLowerCase();
  if (fromSeriesId && fromSeriesId !== seriesId) return null;
  if (!fromSeriesId && fromContext) return null;
  return {
    label: '\u2190 ' + label,
    seriesLabel: label,
    href: catalogueIndexUrl(options && options.baseurl, {
      series: seriesId,
      seriesPage: options && options.seriesPage
    })
  };
}

export function projectSeriesNavigation(ids, currentId, options) {
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

export function createSelectedWorkSeriesNavigation(options) {
  var opts = options || {};
  var baseurl = trimBaseurl(opts.baseurl);
  var routeState = opts.routeState || {};
  var nav = opts.navElement || null;
  var prevLink = opts.prevLinkElement || null;
  var nextLink = opts.nextLinkElement || null;
  var counter = opts.counterElement || null;
  var seriesLinkWrap = opts.seriesLinkWrapElement || null;
  var seriesLink = opts.seriesLinkElement || null;
  var backLink = opts.backLinkElement || null;
  var seriesFromQuery = text(routeState.series);
  var seriesPage = toPositiveInteger(routeState.seriesPage);
  var fromContext = text(routeState.from).toLowerCase();
  var currentWorkId = '';
  var primarySeriesId = '';
  var currentSeriesIds = [];
  var refreshRevision = 0;
  var payloadPromises = new Map();

  function hideNavigation() {
    if (nav) nav.hidden = true;
    if (counter) {
      counter.textContent = '';
      counter.hidden = true;
    }
  }

  function loadExactSeries(seriesId) {
    var id = text(seriesId);
    if (!id) return Promise.resolve(null);
    if (!payloadPromises.has(id)) {
      payloadPromises.set(id, fetchJson(seriesPayloadUrl(id, baseurl)).then(function (payload) {
        return exactSeriesRecord(payload, id) ? payload : null;
      }).catch(function () {
        return null;
      }));
    }
    return payloadPromises.get(id);
  }

  function setSeriesLinkTarget(payload, seriesId) {
    var projection = projectExactSeriesLink(payload, seriesId, currentWorkId, baseurl);
    if (seriesLinkWrap) seriesLinkWrap.hidden = projection.hidden;
    if (!seriesLink) return;
    seriesLink.textContent = projection.label;
    seriesLink.setAttribute('href', projection.href);
  }

  function setBackLinkTarget(payload, seriesId) {
    if (!backLink) return;
    var projection = projectExactSeriesBackLink(payload, {
      seriesId: seriesId,
      currentWorkId: currentWorkId,
      seriesFromQuery: seriesFromQuery,
      seriesPage: seriesPage,
      fromContext: fromContext,
      baseurl: baseurl
    });
    if (!projection) return;
    backLink.setAttribute('data-series-label', projection.seriesLabel);
    backLink.textContent = projection.label;
    backLink.setAttribute('href', projection.href);
  }

  function configureNavigation(payload, seriesId) {
    if (!nav || !prevLink || !nextLink || !seriesId || !currentWorkId) return;
    var projection = projectSeriesNavigation(exactSeriesWorkIds(payload, seriesId), currentWorkId, {
      seriesId: seriesId,
      seriesPage: seriesPage,
      baseurl: baseurl
    });
    nav.hidden = projection.hidden;
    if (counter) {
      counter.textContent = projection.counterText || '';
      counter.hidden = projection.counterHidden;
    }
    if (projection.hidden) return;
    prevLink.href = projection.prevHref;
    nextLink.href = projection.nextHref;
  }

  async function refresh() {
    var revision = ++refreshRevision;
    hideNavigation();
    if (seriesLinkWrap) seriesLinkWrap.hidden = true;
    if (!currentWorkId) return;

    var primaryTarget = primarySeriesId && currentSeriesIds.indexOf(primarySeriesId) !== -1
      ? primarySeriesId
      : '';
    var queryTarget = seriesFromQuery && currentSeriesIds.indexOf(seriesFromQuery) !== -1
      ? seriesFromQuery
      : '';
    var payloads = await Promise.all([
      primaryTarget ? loadExactSeries(primaryTarget) : Promise.resolve(null),
      queryTarget && queryTarget !== primaryTarget ? loadExactSeries(queryTarget) : Promise.resolve(null)
    ]);
    if (revision !== refreshRevision) return;

    var primaryPayload = payloads[0];
    var queryPayload = queryTarget === primaryTarget ? primaryPayload : payloads[1];
    if (primaryTarget && primaryPayload) setSeriesLinkTarget(primaryPayload, primaryTarget);

    if (seriesFromQuery) {
      if (!queryTarget || !queryPayload) return;
      var queryWorkIds = exactSeriesWorkIds(queryPayload, queryTarget);
      if (queryWorkIds.indexOf(currentWorkId) === -1) return;
      setBackLinkTarget(queryPayload, queryTarget);
      configureNavigation(queryPayload, queryTarget);
      return;
    }

    if (primaryTarget && primaryPayload) setBackLinkTarget(primaryPayload, primaryTarget);
  }

  return {
    update: function (metadata) {
      currentWorkId = text(metadata && (metadata.workId || metadata.work_id));
      primarySeriesId = text(metadata && (metadata.seriesId || metadata.series_id));
      currentSeriesIds = normalizeIds(metadata && (metadata.seriesIds || metadata.series_ids));
      refresh();
    }
  };
}
