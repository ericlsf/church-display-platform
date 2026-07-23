document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const bulk = document.querySelector('[data-bulk-form]');
  const count = document.querySelector('[data-selected-count]');
  const selected = () => [...document.querySelectorAll('[data-display-select]:checked')];

  function updateBulk() {
    if (!bulk) return;
    const items = selected();
    bulk.hidden = items.length === 0;
    if (count) count.textContent = items.length;
    bulk.querySelectorAll('input[name="display_ids"]').forEach((node) => node.remove());
    items.forEach((item) => {
      const hidden = document.createElement('input');
      hidden.type = 'hidden'; hidden.name = 'display_ids'; hidden.value = item.value;
      bulk.appendChild(hidden);
    });
  }
  document.querySelectorAll('[data-display-select]').forEach((input) => input.addEventListener('change', updateBulk));
  document.querySelector('[data-clear-selection]')?.addEventListener('click', () => {
    document.querySelectorAll('[data-display-select]').forEach((input) => { input.checked = false; });
    updateBulk();
  });

  document.querySelectorAll('[data-toggle-add-display]').forEach((button) => button.addEventListener('click', () => {
    const panel = document.querySelector('[data-add-display]');
    if (panel) panel.hidden = !panel.hidden;
  }));

  let activeInspector = null;
  function openInspector(id) {
    const inspector = document.getElementById(`display-inspector-${id}`);
    if (!inspector) return;
    closeInspector();
    activeInspector = inspector;
    inspector.classList.add('is-open');
    inspector.setAttribute('aria-hidden', 'false');
    body.classList.add('no-scroll');
    inspector.querySelector('.inspector-close')?.focus();
  }
  function closeInspector() {
    if (!activeInspector) return;
    activeInspector.classList.remove('is-open');
    activeInspector.setAttribute('aria-hidden', 'true');
    activeInspector = null;
    body.classList.remove('no-scroll');
  }
  document.querySelectorAll('[data-open-inspector]').forEach((button) => button.addEventListener('click', () => openInspector(button.dataset.openInspector)));
  document.querySelectorAll('[data-close-inspector]').forEach((button) => button.addEventListener('click', closeInspector));
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeInspector(); });
});
