function isTypingTarget(element) {
  if (!element) return false;
  var tag = (element.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || element.isContentEditable;
}

function firstUsableLink(ids) {
  for (var i = 0; i < ids.length; i += 1) {
    var link = document.getElementById(ids[i]);
    if (!link || link.hidden) continue;
    var href = String(link.getAttribute('href') || '').trim();
    if (!href || href === '#') continue;
    return link;
  }
  return null;
}

export function bindArrowNavigation(options) {
  var opts = options || {};
  var prevIds = Array.isArray(opts.prevIds) ? opts.prevIds : [];
  var nextIds = Array.isArray(opts.nextIds) ? opts.nextIds : [];
  if (!prevIds.length && !nextIds.length) return null;

  function onKeydown(event) {
    if (event.defaultPrevented) return;
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (isTypingTarget(document.activeElement)) return;

    var prev = firstUsableLink(prevIds);
    var next = firstUsableLink(nextIds);
    if (event.key === 'ArrowLeft' && prev) {
      event.preventDefault();
      window.location.href = prev.href;
      return;
    }
    if (event.key === 'ArrowRight' && next) {
      event.preventDefault();
      window.location.href = next.href;
    }
  }

  document.addEventListener('keydown', onKeydown);
  return {
    destroy: function () {
      document.removeEventListener('keydown', onKeydown);
    }
  };
}
