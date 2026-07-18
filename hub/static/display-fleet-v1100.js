document.addEventListener('DOMContentLoaded', () => {
  const panel = document.querySelector('[data-add-display]');
  document.querySelectorAll('[data-toggle-add-display]').forEach((button) => {
    button.addEventListener('click', () => {
      if (!panel) return;
      panel.hidden = !panel.hidden;
      if (!panel.hidden) panel.querySelector('input')?.focus();
    });
  });
});
