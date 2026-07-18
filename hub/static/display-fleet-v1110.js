document.addEventListener('DOMContentLoaded', () => {
  const panel = document.querySelector('[data-add-display]');
  document.querySelectorAll('[data-toggle-add-display]').forEach((button) => {
    button.addEventListener('click', () => {
      if (!panel) return;
      panel.hidden = !panel.hidden;
      if (!panel.hidden) panel.querySelector('input')?.focus();
    });
  });

  const selectors = [...document.querySelectorAll('[data-display-select]')];
  const bulkForm = document.querySelector('[data-bulk-form]');
  const count = document.querySelector('[data-selected-count]');

  function updateBulkBar() {
    if (!bulkForm) return;
    bulkForm.querySelectorAll('input[name="display_ids"]').forEach((input) => input.remove());
    const selected = selectors.filter((input) => input.checked);
    selected.forEach((input) => {
      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'display_ids';
      hidden.value = input.value;
      bulkForm.appendChild(hidden);
    });
    if (count) count.textContent = String(selected.length);
    bulkForm.hidden = selected.length === 0;
  }

  selectors.forEach((input) => input.addEventListener('change', updateBulkBar));
  document.querySelector('[data-clear-selection]')?.addEventListener('click', () => {
    selectors.forEach((input) => { input.checked = false; });
    updateBulkBar();
  });
});
