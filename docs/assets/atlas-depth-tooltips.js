/* Website-only enhancement. README badges remain ordinary links to the A–D legend. */
(() => {
  const badges = document.querySelectorAll('a.atlas-depth-badge');
  if (!badges.length) return;

  badges.forEach((badge) => {
    badge.dataset.explanation = badge.getAttribute('title') || '';
    badge.removeAttribute('title');
  });

  let active = null;
  let popover = null;
  const close = () => {
    if (active) active.setAttribute('aria-expanded', 'false');
    if (popover) popover.remove();
    active = null;
    popover = null;
  };

  document.addEventListener('click', (event) => {
    const badge = event.target.closest('a.atlas-depth-badge');
    if (!badge) {
      close();
      return;
    }
    event.preventDefault();
    if (active === badge) {
      close();
      return;
    }
    close();
    active = badge;
    popover = document.createElement('div');
    popover.className = 'atlas-depth-popover';
    popover.id = 'atlas-depth-popover';
    popover.setAttribute('role', 'tooltip');
    popover.textContent = badge.dataset.explanation;
    document.body.appendChild(popover);
    badge.setAttribute('aria-controls', popover.id);
    badge.setAttribute('aria-expanded', 'true');
    const rect = badge.getBoundingClientRect();
    const left = Math.max(10, Math.min(rect.left, window.innerWidth - popover.offsetWidth - 10));
    const top = Math.max(10, Math.min(rect.bottom + 6, window.innerHeight - popover.offsetHeight - 10));
    popover.style.left = `${left}px`;
    popover.style.top = `${top}px`;
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') close();
  });
  window.addEventListener('resize', close);
  window.addEventListener('scroll', close, true);
})();
