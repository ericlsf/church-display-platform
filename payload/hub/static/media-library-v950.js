(() => {
  const workspace = document.querySelector('[data-media-workspace]');
  if (!workspace) return;
  const grid = workspace.querySelector('[data-library-grid]');
  const search = workspace.querySelector('[data-media-search]');
  const empty = workspace.querySelector('[data-empty-filter]');
  let filter = 'all';

  function applyFilters() {
    if (!grid) return;
    const term = (search?.value || '').trim().toLowerCase();
    let visible = 0;
    grid.querySelectorAll('[data-media-item]').forEach(item => {
      const kind = item.dataset.kind;
      const supported = item.dataset.supported === 'true';
      const filterMatch = filter === 'all' || kind === filter || (filter === 'unsupported' && !supported);
      const searchMatch = !term || item.dataset.name.includes(term);
      item.hidden = !(filterMatch && searchMatch);
      if (!item.hidden) visible += 1;
    });
    grid.classList.toggle('is-filtered', filter !== 'all' || Boolean(term));
    if (empty) empty.hidden = visible !== 0;
  }

  workspace.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    workspace.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('is-active', item === button));
    applyFilters();
  }));
  search?.addEventListener('input', applyFilters);

  workspace.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
    const list = button.dataset.view === 'list';
    grid?.classList.toggle('is-list', list);
    workspace.querySelectorAll('[data-view]').forEach(item => item.classList.toggle('is-active', item === button));
    localStorage.setItem('mediaLibraryView', list ? 'list' : 'grid');
  }));
  const savedView = localStorage.getItem('mediaLibraryView');
  if (savedView === 'list') workspace.querySelector('[data-view="list"]')?.click();

  const playlist = document.getElementById('playlist-list');
  let dragged = null;
  function syncOrder() {
    if (!playlist) return;
    const rows = [...playlist.querySelectorAll('.playlist-item')];
    rows.forEach((row, index) => { const badge = row.querySelector('.playlist-index'); if (badge) badge.textContent = String(index + 1); });
    const value = rows.map(row => row.dataset.path).join('\n');
    const orderField = document.getElementById('playlist-order-field');
    const syncField = document.getElementById('sync-playlist-order-field');
    if (orderField) orderField.value = value;
    if (syncField) syncField.value = value;
  }
  playlist?.addEventListener('click', event => {
    const button = event.target.closest('[data-move]');
    if (!button) return;
    const row = button.closest('.playlist-item');
    const direction = Number(button.dataset.move);
    if (direction < 0 && row.previousElementSibling) playlist.insertBefore(row, row.previousElementSibling);
    if (direction > 0 && row.nextElementSibling) playlist.insertBefore(row.nextElementSibling, row);
    syncOrder();
  });
  playlist?.addEventListener('dragstart', event => { dragged = event.target.closest('.playlist-item'); dragged?.classList.add('dragging'); });
  playlist?.addEventListener('dragend', () => { dragged?.classList.remove('dragging'); dragged = null; syncOrder(); });
  playlist?.addEventListener('dragover', event => {
    if (!dragged) return;
    event.preventDefault();
    const rows = [...playlist.querySelectorAll('.playlist-item:not(.dragging)')];
    const after = rows.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = event.clientY - box.top - box.height / 2;
      return offset < 0 && offset > closest.offset ? { offset, child } : closest;
    }, { offset: Number.NEGATIVE_INFINITY, child: null }).child;
    after ? playlist.insertBefore(dragged, after) : playlist.appendChild(dragged);
  });

  const selectAll = workspace.querySelector('[data-select-all]');
  selectAll?.addEventListener('click', () => {
    const boxes = [...workspace.querySelectorAll('input[name="display_ids"]')];
    const shouldSelect = boxes.some(box => !box.checked);
    boxes.forEach(box => { box.checked = shouldSelect; });
    selectAll.textContent = shouldSelect ? 'Clear all' : 'Select all';
  });
  workspace.querySelector('[data-scroll-to-deploy]')?.addEventListener('click', () => document.getElementById('deploy-playlist')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  syncOrder();
  applyFilters();
})();
