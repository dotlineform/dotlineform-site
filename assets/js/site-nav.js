(function () {
  var more = document.querySelector('[data-nav-more]');
  if (!more) return;

  var summary = more.querySelector('.nav-more__summary');
  var panel = more.querySelector('.nav-more__panel');
  if (!summary || !panel) return;

  function closeMenu() {
    more.classList.remove('is-open');
    summary.setAttribute('aria-expanded', 'false');
    panel.setAttribute('hidden', '');
  }

  function openMenu() {
    more.classList.add('is-open');
    summary.setAttribute('aria-expanded', 'true');
    panel.removeAttribute('hidden');
  }

  function toggleMenu() {
    if (more.classList.contains('is-open')) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  function closeIfOutside(event) {
    if (more.contains(event.target)) return;
    closeMenu();
  }

  document.addEventListener('pointerdown', closeIfOutside, true);
  document.addEventListener('touchstart', closeIfOutside, true);
  document.addEventListener('mousedown', closeIfOutside, true);
  document.addEventListener('click', closeIfOutside, true);

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    if (!more.classList.contains('is-open')) return;
    closeMenu();
    summary.focus();
  });

  more.addEventListener('click', function (event) {
    var target = event.target;
    if (!target) return;
    if (target.tagName && target.tagName.toLowerCase() === 'a') {
      closeMenu();
    }
  });

  summary.addEventListener('click', function (event) {
    event.preventDefault();
    toggleMenu();
  });
})();
