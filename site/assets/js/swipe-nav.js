(function () {
  if (window.__dlfSwipeNav) return;
  if (typeof window.PointerEvent !== 'function') return;

  var DEFAULTS = {
    minDistance: 72,
    maxVerticalDrift: 56,
    maxDuration: 500,
    horizontalRatio: 1.35
  };

  function text(v) {
    return String(v == null ? '' : v).trim();
  }

  function isHidden(el) {
    if (!el) return true;
    if (el.hidden) return true;
    if (el.closest && el.closest('[hidden]')) return true;
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

  function usableLink(ctrl) {
    if (!ctrl || isHidden(ctrl)) return null;
    var href = text(ctrl.getAttribute('href'));
    if (!href || href === '#') return null;
    return ctrl;
  }

  function usableAction(ctrl) {
    if (!ctrl || isHidden(ctrl)) return null;
    if (ctrl.disabled) return null;
    return ctrl;
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

  function bind(zone, options) {
    if (!zone || zone.__dlfSwipeNavBound) return;

    options = options || {};
    var minDistance = Number(options.minDistance);
    if (!Number.isFinite(minDistance) || minDistance <= 0) minDistance = DEFAULTS.minDistance;
    var maxVerticalDrift = Number(options.maxVerticalDrift);
    if (!Number.isFinite(maxVerticalDrift) || maxVerticalDrift < 0) maxVerticalDrift = DEFAULTS.maxVerticalDrift;
    var maxDuration = Number(options.maxDuration);
    if (!Number.isFinite(maxDuration) || maxDuration <= 0) maxDuration = DEFAULTS.maxDuration;
    var horizontalRatio = Number(options.horizontalRatio);
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
        } catch (e) {
        }
      }
      state.pointerId = null;
      state.startX = 0;
      state.startY = 0;
      state.startTime = 0;
    }

    function onPointerDown(e) {
      var pointerType = text(e.pointerType).toLowerCase();
      if (pointerType !== 'touch' && pointerType !== 'pen') return;
      if (e.isPrimary === false) {
        resetPointer();
        return;
      }
      if (state.pointerId !== null) {
        resetPointer();
        return;
      }
      if (!matchesStartTarget(zone, e.target, options.startWithinSelector)) return;
      if (isIgnoredStartTarget(e.target, zone)) return;

      state.pointerId = e.pointerId;
      state.startX = Number(e.clientX) || 0;
      state.startY = Number(e.clientY) || 0;
      state.startTime = Date.now();

      if (zone.setPointerCapture) {
        try {
          zone.setPointerCapture(e.pointerId);
        } catch (err) {
        }
      }
    }

    function onPointerMove(e) {
      if (e.pointerId !== state.pointerId) return;

      var dx = (Number(e.clientX) || 0) - state.startX;
      var dy = (Number(e.clientY) || 0) - state.startY;
      if (Math.abs(dy) > maxVerticalDrift && Math.abs(dy) >= Math.abs(dx)) {
        resetPointer();
      }
    }

    function onPointerCancel(e) {
      if (e.pointerId !== state.pointerId) return;
      resetPointer();
    }

    function onPointerUp(e) {
      if (e.pointerId !== state.pointerId) return;

      var elapsed = Date.now() - state.startTime;
      var dx = (Number(e.clientX) || 0) - state.startX;
      var dy = (Number(e.clientY) || 0) - state.startY;
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
        ? resolveControl(options.getNext, options.normalizeNext || usableAction)
        : resolveControl(options.getPrev, options.normalizePrev || usableAction);

      state.suppressClickUntil = Date.now() + 700;
      resetPointer();

      if (!control) return;
      navigate(control);
    }

    function onClickCapture(e) {
      if (Date.now() > state.suppressClickUntil) return;
      if (!zone.contains(e.target)) return;
      state.suppressClickUntil = 0;
      e.preventDefault();
      e.stopPropagation();
    }

    zone.addEventListener('pointerdown', onPointerDown);
    zone.addEventListener('pointermove', onPointerMove);
    zone.addEventListener('pointerup', onPointerUp);
    zone.addEventListener('pointercancel', onPointerCancel);
    zone.addEventListener('click', onClickCapture, true);

    zone.__dlfSwipeNavBound = true;
  }

  window.__dlfSwipeNav = {
    bindLinkZone: function (zone, options) {
      options = options || {};
      options.normalizePrev = usableLink;
      options.normalizeNext = usableLink;
      bind(zone, options);
    },
    bindActionZone: function (zone, options) {
      options = options || {};
      options.normalizePrev = usableAction;
      options.normalizeNext = usableAction;
      bind(zone, options);
    }
  };
})();
