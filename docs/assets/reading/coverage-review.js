(function () {
  'use strict';
  var root = document.querySelector('.coverage-design');
  if (!root) return;
  var announcement = root.querySelector('[data-cov-announcement]');
  var params = new URLSearchParams(window.location.search);
  var requested = params.get('city');
  if (root.dataset.view === 'city') {
    var panels = Array.from(root.querySelectorAll('.cov-city-panel'));
    var buttons = Array.from(root.querySelectorAll('[data-cov-select]'));
    function choose(slug, userAction) {
      if (!panels.some(function (p) { return p.dataset.city === slug; })) slug = 'urbana-champaign';
      panels.forEach(function (p) { p.hidden = p.dataset.city !== slug; });
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.covSelect === slug)); });
      var panel = panels.find(function (p) { return p.dataset.city === slug; });
      if (announcement) announcement.textContent = panel.querySelector('h3').textContent + ': evidence and scope shown in six stage groups.';
      if (userAction) {
        var next = new URL(window.location.href); next.searchParams.set('city', slug);
        window.history.replaceState(null, '', next.href);
        if (window.matchMedia('(max-width: 620px)').matches) {
          var heading = panel.querySelector('h3'); heading.focus({preventScroll: true});
          panel.scrollIntoView({block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
        }
      }
    }
    buttons.forEach(function (button) { button.addEventListener('click', function () { choose(button.dataset.covSelect, true); }); });
    choose(requested, false);
  } else {
    var selector = root.querySelector('[data-cov-filter]');
    var cards = Array.from(root.querySelectorAll('.cov-stage-city'));
    function filter() {
      var value = selector.value;
      cards.forEach(function (card) { card.hidden = value !== 'all' && card.dataset.city !== value && card.dataset.cohort !== value; });
      root.querySelectorAll('.cov-group-count').forEach(function (count) {
        var shown = Array.from(count.closest('.cov-group').querySelectorAll('.cov-stage-city')).filter(function (card) { return !card.hidden; }).length;
        count.textContent = shown === 9 ? '9 cases' : shown + ' of 9 cases';
      });
      if (announcement) announcement.textContent = 'Coverage filtered to ' + selector.options[selector.selectedIndex].textContent;
    }
    if (selector) {
      if (Array.from(selector.options).some(function (o) { return o.value === requested; })) selector.value = requested;
      selector.addEventListener('change', filter); filter();
    }
  }
  root.dataset.ready = 'true';
})();
