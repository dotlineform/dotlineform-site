(function () {
  var button = document.getElementById('themeToggle');
  if (!button) return;

  function getTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      if (theme === 'auto') {
        localStorage.removeItem('theme');
      } else {
        localStorage.setItem('theme', theme);
      }
    } catch (e) {}
    button.textContent = theme;
  }

  function nextTheme(theme) {
    if (theme === 'auto') return 'light';
    if (theme === 'light') return 'dark';
    return 'auto';
  }

  setTheme(getTheme());

  button.addEventListener('click', function () {
    setTheme(nextTheme(getTheme()));
  });
})();
