(function () {
  var button = document.getElementById('themeToggle');
  if (!button) return;

  var LIGHT_THEME = 'light';
  var DARK_THEME = 'dark';

  function normalizeTheme(theme) {
    return theme === DARK_THEME ? DARK_THEME : LIGHT_THEME;
  }

  function getTheme() {
    return normalizeTheme(document.documentElement.getAttribute('data-theme'));
  }

  function setTheme(theme) {
    var activeTheme = normalizeTheme(theme);
    var isDark = activeTheme === DARK_THEME;
    var nextLabel = isDark ? 'Switch to light mode' : 'Switch to dark mode';
    document.documentElement.setAttribute('data-theme', activeTheme);
    try {
      localStorage.setItem('theme', activeTheme);
    } catch (e) {}
    button.setAttribute('aria-label', nextLabel);
    button.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    button.title = nextLabel;
    button.querySelectorAll('[data-theme-icon]').forEach(function (icon) {
      if (icon.dataset.themeIcon === activeTheme) {
        icon.removeAttribute('hidden');
      } else {
        icon.setAttribute('hidden', '');
      }
    });
  }

  function nextTheme(theme) {
    return normalizeTheme(theme) === DARK_THEME ? LIGHT_THEME : DARK_THEME;
  }

  setTheme(getTheme());

  button.addEventListener('click', function () {
    setTheme(nextTheme(getTheme()));
  });
})();
