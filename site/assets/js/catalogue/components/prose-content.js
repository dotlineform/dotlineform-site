import { text } from '../shared/text.js';

export function renderProseContent(options) {
  var opts = options || {};
  var root = opts.rootElement || null;
  var content = opts.contentElement || root;
  if (!root || !content) return null;

  var html = typeof opts.html === 'string' ? opts.html : '';
  var hasContent = !!text(html);

  if (!hasContent) {
    content.innerHTML = '';
    if (opts.hideRootWhenEmpty) root.hidden = true;
    return {
      rootElement: root,
      contentElement: content,
      rendered: false
    };
  }

  content.innerHTML = html;
  root.hidden = false;
  return {
    rootElement: root,
    contentElement: content,
    rendered: true
  };
}
