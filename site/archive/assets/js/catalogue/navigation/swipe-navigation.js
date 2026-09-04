var DEFAULTS = {
  minDistance: 72,
  maxVerticalDrift: 56,
  maxDuration: 500,
  horizontalRatio: 1.35
};

function stringValue(value) {
  return String(value == null ? '' : value).trim();
}

function isHidden(element) {
  if (!element) return true;
  if (element.hidden) return true;
  if (element.closest && element.closest('[hidden]')) return true;
  return false;
}

function unsupportedBind(zone) {
  if (zone) zone.__dlfSwipeNavUnsupported = true;
  return false;
}

function isIgnoredStartTarget(target, zone) {
  var node = target;
  while (node && node !== zone) {
    if (node.nodeType !== 1) {
      node = node.parentNode;
      continue;
    }
    if (node.hasAttribute('data-swipe-nav-ignore')) return true;
    var tag = (node.tagName || '').toLowerCase();
    if (tag === 'button' || tag === 'input' || tag === 'select' || tag === 'textarea' || tag === 'label') {
      return true;
    }
    if (node.isContentEditable) return true;
    node = node.parentNode;
  }
  return false;
}

function matchesStartTarget(zone, target, selector) {
  if (!selector) return true;
  if (!target || !target.closest) return false;
  var match = target.closest(selector);
  return !!(match && zone.contains(match));
}

function usableLink(control) {
  if (!control || isHidden(control)) return null;
  var href = stringValue(control.getAttribute('href'));
  if (!href || href === '#') return null;
  return control;
}

function usableAction(control) {
  if (!control || isHidden(control)) return null;
  if (control.disabled) return null;
  return control;
}

function resolveControl(getter, normalizer) {
  if (typeof getter !== 'function') return null;
  return normalizer(getter());
}

function navigate(control) {
  var tag = (control.tagName || '').toLowerCase();
  if (tag === 'a') {
    window.location.href = control.href;
    return;
  }
  control.click();
}

function pointerEventsSupported() {
  return typeof window !== 'undefined' && typeof window.PointerEvent === 'function';
}

function bind(zone, options) {
  if (!pointerEventsSupported()) return unsupportedBind(zone);
  if (!zone || zone.__dlfSwipeNavBound) return false;

  var opts = options || {};
  var minDistance = Number(opts.minDistance);
  if (!Number.isFinite(minDistance) || minDistance <= 0) minDistance = DEFAULTS.minDistance;
  var maxVerticalDrift = Number(opts.maxVerticalDrift);
  if (!Number.isFinite(maxVerticalDrift) || maxVerticalDrift < 0) maxVerticalDrift = DEFAULTS.maxVerticalDrift;
  var maxDuration = Number(opts.maxDuration);
  if (!Number.isFinite(maxDuration) || maxDuration <= 0) maxDuration = DEFAULTS.maxDuration;
  var horizontalRatio = Number(opts.horizontalRatio);
  if (!Number.isFinite(horizontalRatio) || horizontalRatio <= 1) horizontalRatio = DEFAULTS.horizontalRatio;

  var state = {
    pointerId: null,
    startX: 0,
    startY: 0,
    startTime: 0,
    suppressClickUntil: 0
  };

  function resetPointer() {
    if (state.pointerId !== null && zone.releasePointerCapture) {
      try {
        if (zone.hasPointerCapture && zone.hasPointerCapture(state.pointerId)) {
          zone.releasePointerCapture(state.pointerId);
        }
      } catch (err) {
      }
    }
    state.pointerId = null;
    state.startX = 0;
    state.startY = 0;
    state.startTime = 0;
  }

  function onPointerDown(event) {
    var pointerType = stringValue(event.pointerType).toLowerCase();
    if (pointerType !== 'touch' && pointerType !== 'pen') return;
    if (event.isPrimary === false) {
      resetPointer();
      return;
    }
    if (state.pointerId !== null) {
      resetPointer();
      return;
    }
    if (!matchesStartTarget(zone, event.target, opts.startWithinSelector)) return;
    if (isIgnoredStartTarget(event.target, zone)) return;

    state.pointerId = event.pointerId;
    state.startX = Number(event.clientX) || 0;
    state.startY = Number(event.clientY) || 0;
    state.startTime = Date.now();

    if (zone.setPointerCapture) {
      try {
        zone.setPointerCapture(event.pointerId);
      } catch (err) {
      }
    }
  }

  function onPointerMove(event) {
    if (event.pointerId !== state.pointerId) return;

    var dx = (Number(event.clientX) || 0) - state.startX;
    var dy = (Number(event.clientY) || 0) - state.startY;
    if (Math.abs(dy) > maxVerticalDrift && Math.abs(dy) >= Math.abs(dx)) {
      resetPointer();
    }
  }

  function onPointerCancel(event) {
    if (event.pointerId !== state.pointerId) return;
    resetPointer();
  }

  function onPointerUp(event) {
    if (event.pointerId !== state.pointerId) return;

    var elapsed = Date.now() - state.startTime;
    var dx = (Number(event.clientX) || 0) - state.startX;
    var dy = (Number(event.clientY) || 0) - state.startY;
    var absX = Math.abs(dx);
    var absY = Math.abs(dy);
    var isSwipe = elapsed <= maxDuration &&
      absX >= minDistance &&
      absY <= maxVerticalDrift &&
      absX >= (absY * horizontalRatio);

    if (!isSwipe) {
      resetPointer();
      return;
    }

    var control = dx < 0
      ? resolveControl(opts.getNext, opts.normalizeNext || usableAction)
      : resolveControl(opts.getPrev, opts.normalizePrev || usableAction);

    state.suppressClickUntil = Date.now() + 700;
    resetPointer();

    if (!control) return;
    navigate(control);
  }

  function onClickCapture(event) {
    if (Date.now() > state.suppressClickUntil) return;
    if (!zone.contains(event.target)) return;
    state.suppressClickUntil = 0;
    event.preventDefault();
    event.stopPropagation();
  }

  zone.addEventListener('pointerdown', onPointerDown);
  zone.addEventListener('pointermove', onPointerMove);
  zone.addEventListener('pointerup', onPointerUp);
  zone.addEventListener('pointercancel', onPointerCancel);
  zone.addEventListener('click', onClickCapture, true);

  zone.__dlfSwipeNavBound = true;
  return true;
}

export function isSwipeNavigationSupported() {
  return pointerEventsSupported();
}

export function bindLinkSwipeZone(zone, options) {
  var opts = Object.assign({}, options || {});
  opts.normalizePrev = usableLink;
  opts.normalizeNext = usableLink;
  return bind(zone, opts);
}

export function bindActionSwipeZone(zone, options) {
  var opts = Object.assign({}, options || {});
  opts.normalizePrev = usableAction;
  opts.normalizeNext = usableAction;
  return bind(zone, opts);
}
