import { text } from '../shared/text.js';

export function renderCatalogueCaption(value, options) {
  var caption = text(value);
  if (!caption) return null;
  var opts = options || {};
  var node = document.createElement(opts.tagName || 'div');
  node.className = ['catalogueCaption', text(opts.className)].filter(Boolean).join(' ');
  node.textContent = caption;
  return node;
}
