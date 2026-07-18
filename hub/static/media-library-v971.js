(() => {
  const workspace = document.querySelector('[data-media-workspace]');
  if (!workspace) return;

  const grid = workspace.querySelector('[data-library-grid]');
  const search = workspace.querySelector('[data-media-search]');
  const empty = workspace.querySelector('[data-empty-filter]');
  const visibleCount = workspace.querySelector('[data-visible-count]');
  const drawer = workspace.querySelector('[data-details-drawer]');
  const backdrop = workspace.querySelector('[data-details-backdrop]');
  const playlist = document.getElementById('playlist-list');
  const picked = new Set();
  let filter = 'all';
  let activeCard = null;
  let draggedPlaylistRow = null;

  const allCards = () => [...(grid?.querySelectorAll('[data-media-item]') || [])];
  const playableCards = () => allCards().filter(card => card.dataset.supported === 'true' && card.dataset.kind !== 'folder');
  const visibleCards = () => allCards().filter(card => !card.hidden);

  function applyFilters() {
    if (!grid) return;
    const term = (search?.value || '').trim().toLowerCase();
    let visible = 0;
    allCards().forEach(item => {
      const kind = item.dataset.kind;
      const supported = item.dataset.supported === 'true';
      const filterMatch = filter === 'all' || kind === filter || (filter === 'unsupported' && !supported);
      const searchMatch = !term || item.dataset.name.includes(term);
      item.hidden = !(filterMatch && searchMatch);
      if (!item.hidden) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
    if (visibleCount) visibleCount.textContent = String(visible);
    if (activeCard?.hidden) closeDetails();
  }

  function formatModified(value) {
    if (!value) return 'Not available';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: 'numeric', minute: '2-digit'
    }).format(date);
  }

  function setDrawerValue(selector, value, options = {}) {
    const element = drawer?.querySelector(selector);
    if (!element) return;
    const normalized = String(value || '').trim();
    const unavailable = !normalized || normalized === '—' || /available after sync|unknown|not available/i.test(normalized);
    element.textContent = unavailable ? (options.fallback || 'Not available') : normalized;
    element.classList.toggle('is-status-pill', Boolean(options.status && unavailable));
    element.classList.toggle('is-pending', Boolean(options.status && unavailable));
  }

  function closeDetails({ restoreFocus = false } = {}) {
    if (!drawer?.classList.contains('is-open')) return;
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    if (backdrop) backdrop.hidden = true;
    document.body.classList.remove('media-drawer-open');
    const previous = activeCard;
    activeCard?.classList.remove('is-selected');
    activeCard = null;
    if (restoreFocus) previous?.focus();
  }

  function openDetails(item) {
    if (!drawer || item.dataset.kind === 'folder') return;
    if (activeCard === item && drawer.classList.contains('is-open')) {
      closeDetails({ restoreFocus: true });
      return;
    }

    activeCard?.classList.remove('is-selected');
    activeCard = item;
    activeCard.classList.add('is-selected');

    setDrawerValue('[data-details-title]', item.dataset.title);
    setDrawerValue('[data-details-type]', item.dataset.type);
    setDrawerValue('[data-details-size]', item.dataset.size);
    setDrawerValue('[data-details-modified]', formatModified(item.dataset.modified));
    setDrawerValue('[data-details-mime]', item.dataset.mime);
    setDrawerValue('[data-details-resolution]', item.dataset.resolution, { status: true, fallback: 'Pending sync' });
    setDrawerValue('[data-details-path]', item.dataset.path);

    const preview = drawer.querySelector('[data-details-preview]');
    const source = item.querySelector('.media-card-preview img');
    if (preview) {
      preview.replaceChildren();
      if (source) {
        const img = document.createElement('img');
        img.src = source.src;
        img.alt = item.dataset.title || 'Media preview';
        preview.appendChild(img);
      } else {
        const icon = document.createElement('span');
        icon.textContent = item.dataset.kind === 'video' ? '▶' : '📄';
        icon.setAttribute('aria-hidden', 'true');
        preview.appendChild(icon);
      }
    }

    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    if (backdrop) backdrop.hidden = false;
    document.body.classList.add('media-drawer-open');
  }

  function moveCardFocus(direction) {
    const cards = visibleCards();
    if (!cards.length) return;
    const current = activeCard || document.activeElement.closest?.('[data-media-item]');
    const index = Math.max(0, cards.indexOf(current));
    const nextIndex = (index + direction + cards.length) % cards.length;
    cards[nextIndex].focus();
    if (drawer?.classList.contains('is-open')) openDetails(cards[nextIndex]);
  }

  function updatePicked() {
    playableCards().forEach(card => card.classList.toggle('is-picked', picked.has(card.dataset.path)));
    const count = workspace.querySelector('[data-selected-media-count]');
    const add = workspace.querySelector('[data-add-selected-media]');
    if (count) count.textContent = String(picked.size);
    if (add) add.disabled = picked.size === 0;
  }

  function togglePicked(card) {
    if (!card || card.dataset.supported !== 'true' || card.dataset.kind === 'folder') return;
    picked.has(card.dataset.path) ? picked.delete(card.dataset.path) : picked.add(card.dataset.path);
    updatePicked();
  }

  function playlistPaths() {
    return new Set([...(playlist?.querySelectorAll('.playlist-item') || [])].map(row => row.dataset.path));
  }

  function syncOrder() {
    const rows = [...(playlist?.querySelectorAll('.playlist-item') || [])];
    rows.forEach((row, index) => {
      const indexElement = row.querySelector('.playlist-index');
      if (indexElement) indexElement.textContent = String(index + 1);
    });
    const value = rows.map(row => row.dataset.path).join('\n');
    ['playlist-order-field', 'sync-playlist-order-field'].forEach(id => {
      const field = document.getElementById(id);
      if (field) field.value = value;
    });
    playlist?.classList.toggle('is-empty', rows.length === 0);
  }

  function addCard(card) {
    if (!playlist || playlistPaths().has(card.dataset.path)) return;
    const row = document.createElement('div');
    row.className = 'playlist-item';
    row.draggable = true;
    row.dataset.path = card.dataset.path;
    const image = card.querySelector('.media-card-preview img');
    row.innerHTML = `<span class="playlist-grip">⠿</span><span class="playlist-index"></span><span class="playlist-thumb">${image ? `<img src="${image.src}" alt="">` : '▶'}</span><span class="playlist-details"><strong></strong><small></small></span><span class="playlist-controls"><button type="button" data-move="-1" aria-label="Move up">↑</button><button type="button" data-move="1" aria-label="Move down">↓</button><button type="button" data-remove-playlist aria-label="Remove">×</button></span>`;
    row.querySelector('strong').textContent = card.dataset.title;
    row.querySelector('small').textContent = `${card.dataset.type} · ${card.dataset.size}`;
    playlist.appendChild(row);
    syncOrder();
  }

  search?.addEventListener('input', applyFilters);
  workspace.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    workspace.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('is-active', item === button));
    applyFilters();
  }));
  workspace.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
    grid?.classList.toggle('is-list', button.dataset.view === 'list');
    workspace.querySelectorAll('[data-view]').forEach(item => item.classList.toggle('is-active', item === button));
  }));

  grid?.addEventListener('click', event => {
    const card = event.target.closest('[data-media-item]');
    if (!card) return;
    const selectButton = event.target.closest('[data-select-media]');
    if (selectButton) {
      event.stopPropagation();
      togglePicked(card);
      return;
    }
    if (!event.target.closest('a')) openDetails(card);
  });

  grid?.addEventListener('dblclick', event => {
    const card = event.target.closest('[data-media-item]');
    if (card?.dataset.supported === 'true' && card.dataset.kind !== 'folder') addCard(card);
  });

  grid?.addEventListener('keydown', event => {
    const card = event.target.closest('[data-media-item]');
    if (!card) return;
    if (event.key === 'Enter') {
      event.preventDefault();
      openDetails(card);
    } else if (event.key === ' ') {
      event.preventDefault();
      togglePicked(card);
    } else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      moveCardFocus(1);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      moveCardFocus(-1);
    }
  });

  grid?.addEventListener('dragstart', event => {
    const card = event.target.closest('[data-media-item]');
    if (card?.dataset.supported === 'true' && card.dataset.kind !== 'folder') {
      event.dataTransfer.setData('text/media-path', card.dataset.path);
      event.dataTransfer.effectAllowed = 'copy';
    }
  });

  workspace.querySelector('[data-details-close]')?.addEventListener('click', () => closeDetails({ restoreFocus: true }));
  backdrop?.addEventListener('click', () => closeDetails({ restoreFocus: true }));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeDetails({ restoreFocus: true });
  });

  playlist?.addEventListener('click', event => {
    const remove = event.target.closest('[data-remove-playlist]');
    if (remove) {
      remove.closest('.playlist-item')?.remove();
      syncOrder();
      return;
    }
    const button = event.target.closest('[data-move]');
    if (!button) return;
    const row = button.closest('.playlist-item');
    const direction = Number(button.dataset.move);
    if (direction < 0 && row.previousElementSibling) playlist.insertBefore(row, row.previousElementSibling);
    if (direction > 0 && row.nextElementSibling) playlist.insertBefore(row.nextElementSibling, row);
    syncOrder();
  });

  playlist?.addEventListener('dragstart', event => {
    const row = event.target.closest('.playlist-item');
    if (!row) return;
    draggedPlaylistRow = row;
    row.classList.add('dragging');
  });
  playlist?.addEventListener('dragend', () => {
    draggedPlaylistRow?.classList.remove('dragging');
    draggedPlaylistRow = null;
    playlist.classList.remove('is-drop-target');
    syncOrder();
  });
  playlist?.addEventListener('dragover', event => {
    event.preventDefault();
    const mediaPath = event.dataTransfer.types.includes('text/media-path');
    if (mediaPath && !event.target.closest('.playlist-item')) playlist.classList.add('is-drop-target');
    if (!draggedPlaylistRow) return;
    const rows = [...playlist.querySelectorAll('.playlist-item:not(.dragging)')];
    const after = rows.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = event.clientY - box.top - box.height / 2;
      return offset < 0 && offset > closest.offset ? { offset, child } : closest;
    }, { offset: Number.NEGATIVE_INFINITY, child: null }).child;
    after ? playlist.insertBefore(draggedPlaylistRow, after) : playlist.appendChild(draggedPlaylistRow);
  });
  playlist?.addEventListener('dragleave', event => {
    if (!playlist.contains(event.relatedTarget)) playlist.classList.remove('is-drop-target');
  });
  playlist?.addEventListener('drop', event => {
    const path = event.dataTransfer.getData('text/media-path');
    if (path) {
      event.preventDefault();
      const card = playableCards().find(item => item.dataset.path === path);
      if (card) addCard(card);
    }
    playlist.classList.remove('is-drop-target');
  });

  workspace.querySelector('[data-add-selected-media]')?.addEventListener('click', () => {
    playableCards().filter(card => picked.has(card.dataset.path)).forEach(addCard);
    picked.clear();
    updatePicked();
    playlist?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  workspace.querySelector('[data-clear-media-selection]')?.addEventListener('click', () => {
    picked.clear();
    updatePicked();
  });

  const selectAll = workspace.querySelector('[data-select-all]');
  const displayBoxes = [...workspace.querySelectorAll('input[name="display_ids"]')];
  const displayCount = workspace.querySelector('[data-selected-display-count]');
  const deployButton = workspace.querySelector('[data-deploy-button]');
  function updateDisplayCount() {
    const count = displayBoxes.filter(box => box.checked).length;
    if (displayCount) displayCount.textContent = String(count);
    if (deployButton && displayBoxes.length) deployButton.disabled = count === 0;
    if (selectAll) selectAll.textContent = count === displayBoxes.length && displayBoxes.length ? 'Clear all' : 'Select all';
  }
  displayBoxes.forEach(box => box.addEventListener('change', updateDisplayCount));
  selectAll?.addEventListener('click', () => {
    const shouldSelect = displayBoxes.some(box => !box.checked);
    displayBoxes.forEach(box => { box.checked = shouldSelect; });
    updateDisplayCount();
  });

  workspace.querySelector('[data-scroll-to-deploy]')?.addEventListener('click', () => {
    document.getElementById('deploy-playlist')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  if (playlist) new MutationObserver(syncOrder).observe(playlist, { childList: true });
  syncOrder();
  applyFilters();
  updatePicked();
  updateDisplayCount();
})();
