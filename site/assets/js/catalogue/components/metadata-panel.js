import { text } from '../shared/text.js';

function isNode(value) {
  return value && typeof value === 'object' && typeof value.nodeType === 'number';
}

function setOptionalAttribute(node, name, value) {
  var valueText = text(value);
  if (valueText) node.setAttribute(name, valueText);
}

function collectSegmentNodes(segments, nodes) {
  (Array.isArray(segments) ? segments : []).forEach(function (segment) {
    if (isNode(segment)) {
      nodes.push(segment);
      return;
    }
    if (!segment || typeof segment !== 'object') return;
    if (isNode(segment.node)) nodes.push(segment.node);
  });
}

function preserveNodes(rows) {
  var nodes = [];
  (Array.isArray(rows) ? rows : []).forEach(function (row) {
    collectSegmentNodes(row && row.segments, nodes);
  });
  nodes.forEach(function (node) {
    if (node.parentNode) node.parentNode.removeChild(node);
  });
}

function appendLink(parent, linkData) {
  var href = text(linkData && linkData.href);
  var label = text(linkData && linkData.label);
  if (!href || !label) return false;

  var link = document.createElement('a');
  setOptionalAttribute(link, 'id', linkData.id);
  setOptionalAttribute(link, 'class', linkData.className);
  link.href = href;
  link.textContent = label;
  setOptionalAttribute(link, 'target', linkData.target);
  setOptionalAttribute(link, 'rel', linkData.rel);
  parent.appendChild(link);
  return true;
}

function appendLinks(parent, segment) {
  var links = Array.isArray(segment && segment.links) ? segment.links : [];
  var separator = typeof segment.separator === 'string' ? segment.separator : ', ';
  var target = parent;
  if (text(segment && (segment.id || segment.className))) {
    target = document.createElement('span');
    setOptionalAttribute(target, 'id', segment.id);
    setOptionalAttribute(target, 'class', segment.className);
  }
  var count = 0;
  links.forEach(function (link) {
    var holder = document.createElement('span');
    if (!appendLink(holder, link)) return;
    if (count > 0) target.appendChild(document.createTextNode(separator));
    while (holder.firstChild) target.appendChild(holder.firstChild);
    count += 1;
  });
  if (count > 0 && target !== parent) parent.appendChild(target);
  return count > 0;
}

function appendText(parent, value) {
  var valueText = String(value == null ? '' : value);
  if (!valueText) return false;
  parent.appendChild(document.createTextNode(valueText));
  return !!text(valueText);
}

function appendWrappedText(parent, segment) {
  var valueText = text(segment && segment.text);
  if (!valueText) return false;
  var span = document.createElement('span');
  setOptionalAttribute(span, 'id', segment.id);
  setOptionalAttribute(span, 'class', segment.className);
  span.textContent = valueText;
  parent.appendChild(span);
  return true;
}

function appendNode(parent, node) {
  if (!isNode(node)) return false;
  parent.appendChild(node);
  return true;
}

function appendSegment(parent, segment) {
  if (typeof segment === 'string' || typeof segment === 'number') return appendText(parent, segment);
  if (isNode(segment)) return appendNode(parent, segment);
  if (!segment || typeof segment !== 'object') return false;
  if (isNode(segment.node)) return appendNode(parent, segment.node);
  if (segment.link) return appendLink(parent, segment.link);
  if (segment.links) return appendLinks(parent, segment);
  if (Object.prototype.hasOwnProperty.call(segment, 'text')) return appendWrappedText(parent, segment);
  return false;
}

function renderRow(row) {
  var rowData = row || {};
  var segments = Array.isArray(rowData.segments) ? rowData.segments : [];
  var rowEl = document.createElement('div');
  rowEl.className = 'catalogueMetadata__row';
  if (text(rowData.modifier)) rowEl.className += ' catalogueMetadata__row--' + text(rowData.modifier);
  if (text(rowData.className)) rowEl.className += ' ' + text(rowData.className);
  setOptionalAttribute(rowEl, 'id', rowData.id);

  var rendered = false;
  segments.forEach(function (segment) {
    rendered = appendSegment(rowEl, segment) || rendered;
  });

  if (rowData.hidden || (!rendered && rowData.hideWhenEmpty !== false)) return null;
  return rowEl;
}

export function renderMetadataPanel(options) {
  var opts = options || {};
  var root = opts.rootElement || null;
  var rowsElement = opts.rowsElement || root;
  if (!root || !rowsElement) return null;

  var rows = Array.isArray(opts.rows) ? opts.rows : [];
  preserveNodes(rows);
  rowsElement.innerHTML = '';

  var renderedRows = [];
  rows.forEach(function (row) {
    var rowEl = renderRow(row);
    if (!rowEl) return;
    rowsElement.appendChild(rowEl);
    renderedRows.push(rowEl);
  });

  if (opts.hideRootWhenEmpty) root.hidden = renderedRows.length === 0;
  return {
    rootElement: root,
    rowsElement: rowsElement,
    rowElements: renderedRows
  };
}
