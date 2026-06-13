import { text } from './text.js';

export function thumbUrl(base, id, suffix, size, format) {
  var thumbId = text(id);
  if (!thumbId) return '';
  return text(base) + thumbId + '-' + text(suffix) + '-' + text(size) + '.' + text(format);
}

export function thumbSrcset(base, id, sizes, suffix, format) {
  var thumbId = text(id);
  if (!thumbId) return '';
  return (Array.isArray(sizes) ? sizes : [])
    .map(function (size) {
      return thumbUrl(base, thumbId, suffix, size, format) + ' ' + String(size) + 'w';
    })
    .join(', ');
}
