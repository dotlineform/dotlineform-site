import { catalogueIndexUrl, seriesIndexUrl, trimBaseurl, workUrl } from '../shared/catalogue-urls.js';
import { fetchJson } from '../shared/fetch-json.js';
import { text, toPositiveInteger } from '../shared/text.js';

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
  return row && Array.isArray(row.works) ? normalizeIds(row.works) : [];
}

function seriesIndexTitle(payload, seriesId) {
  var row = seriesIndexRow(payload, seriesId);
  return row ? text(row.title) : '';
}

function projectSeriesLink(payload, seriesId, baseurl) {
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

function projectBackLink(payload, options) {
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

function projectSeriesNavigation(ids, currentId, options) {
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
  var seriesIndexData = null;
  var currentWorkId = '';
  var primarySeriesId = '';

  function setSeriesLinkTarget(seriesId) {
    var projection = projectSeriesLink(seriesIndexData, seriesId, baseurl);
    if (seriesLinkWrap) seriesLinkWrap.hidden = projection.hidden;
    if (!seriesLink) return;
    seriesLink.textContent = projection.label;
    seriesLink.setAttribute('href', projection.href);
  }

  function setBackLinkLabel(seriesId) {
    if (!backLink) return;
    var projection = projectBackLink(seriesIndexData, {
      seriesId: seriesId,
      seriesFromQuery: seriesFromQuery,
      fromContext: fromContext,
      baseurl: baseurl
    });
    if (!projection) return;
    backLink.setAttribute('data-series-label', projection.seriesLabel);
    if (projection.label) backLink.textContent = projection.label;
    if (projection.href) backLink.setAttribute('href', projection.href);
  }

  function configureNavigation(ids) {
    if (!nav || !prevLink || !nextLink || !seriesFromQuery || !currentWorkId) return;
    var projection = projectSeriesNavigation(ids, currentWorkId, {
      seriesId: seriesFromQuery,
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

  function refresh() {
    if (!seriesIndexData) return;
    if (primarySeriesId) {
      setSeriesLinkTarget(primarySeriesId);
      setBackLinkLabel(primarySeriesId);
    } else if (seriesLinkWrap) {
      seriesLinkWrap.hidden = true;
      setSeriesLinkTarget('');
    }

    if (!seriesFromQuery) {
      if (nav) nav.hidden = true;
      return;
    }
    setBackLinkLabel(seriesFromQuery);
    configureNavigation(seriesIndexWorkIds(seriesIndexData, seriesFromQuery));
  }

  fetchJson(seriesIndexUrl(baseurl))
    .then(function (data) {
      seriesIndexData = data;
      refresh();
    })
    .catch(function () {
      if (seriesLinkWrap) seriesLinkWrap.hidden = true;
      if (nav) nav.hidden = true;
    });

  return {
    update: function (metadata) {
      currentWorkId = text(metadata && (metadata.workId || metadata.work_id));
      primarySeriesId = text(metadata && (metadata.seriesId || metadata.series_id));
      refresh();
    }
  };
}
