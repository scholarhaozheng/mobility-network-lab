/* Open retained figure evidence when an existing deep link targets it. */
(function () {
  function targetFrom(hash) {
    try { return document.getElementById(decodeURIComponent(hash.slice(1))); } catch (_) { return null; }
  }
  function reveal(target, scroll) {
    if (!target) return;
    let opened = false;
    for (let node = target.parentElement; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS' && !node.open) { node.open = true; opened = true; }
    }
    if (opened && scroll) requestAnimationFrame(function () {
      if (target.closest('article.case-atlas')) document.dispatchEvent(new Event('reading-card-rows-aligned'));
      else target.scrollIntoView({block: 'start'});
    });
  }
  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[href^="#"]');
    if (link) reveal(targetFrom(link.hash), false);
  }, true);
  window.addEventListener('hashchange', function () { reveal(targetFrom(location.hash), true); });
  window.addEventListener('load', function () { reveal(targetFrom(location.hash), true); });
})();
