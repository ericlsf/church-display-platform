document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const bulk = document.querySelector('[data-bulk-form]');
  const count = document.querySelector('[data-selected-count]');
  const liveState = document.querySelector('[data-live-state]');
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

  function titleCase(value) {
    return String(value || 'unknown').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function refreshPreview(image, url) {
    if (!image || !url) return;
    const separator = url.includes('?') ? '&' : '?';
    image.src = `${url}${separator}live=${Date.now()}`;
  }

  function updateCard(row) {
    const card = document.querySelector(`[data-display-card][data-display-id="${CSS.escape(row.id)}"]`);
    if (!card) return;
    const wasOnline = card.classList.contains('is-online');
    card.classList.toggle('is-online', row.online);
    card.classList.toggle('is-offline', !row.online);
    card.querySelector('[data-status-text]')?.replaceChildren(document.createTextNode(row.online ? 'Online' : 'Offline'));
    const media = card.querySelector('[data-current-media]');
    if (media) { media.textContent = row.current_media || 'Nothing playing'; media.title = row.current_media || ''; }
    const heartbeat = card.querySelector('[data-heartbeat]'); if (heartbeat) heartbeat.textContent = row.heartbeat || 'Unknown';
    const version = card.querySelector('[data-version]'); if (version) version.textContent = row.version || 'Unknown';
    const sync = card.querySelector('[data-sync-state]'); if (sync) sync.textContent = titleCase(row.sync_state);
    const mediaCount = card.querySelector('[data-media-count]'); if (mediaCount) mediaCount.textContent = row.media_count ?? 0;
    const cpu = card.querySelector('[data-cpu-temp]'); if (cpu) cpu.textContent = row.cpu_temp || 'Unknown';
    const disk = card.querySelector('[data-disk-usage]'); if (disk) disk.textContent = row.disk_usage || 'Unknown';
    const memory = card.querySelector('[data-memory-usage]'); if (memory) memory.textContent = row.memory_usage || 'Unknown';
    card.classList.toggle('needs-attention', Boolean(row.attention));

    const appHealth = card.querySelector('[data-app-health]');
    if (appHealth) {
      appHealth.textContent = `Player ${row.display_app_running ? 'running' : 'stopped'}`;
      appHealth.className = `health-chip ${row.display_app_running ? 'healthy' : 'critical'}`;
    }
    const updateHealth = card.querySelector('[data-update-health]');
    if (updateHealth) updateHealth.hidden = !row.update_available;
    const jobHealth = card.querySelector('[data-job-health]');
    if (jobHealth) {
      const job = row.job || {};
      if (job.active_count) {
        jobHealth.textContent = `${titleCase(job.type)} · ${job.progress || 0}%`;
        jobHealth.className = 'health-chip working';
      } else if (job.failed_count) {
        jobHealth.textContent = `${job.failed_count} failed job${job.failed_count === 1 ? '' : 's'}`;
        jobHealth.className = 'health-chip critical';
      } else {
        jobHealth.textContent = 'No active jobs';
        jobHealth.className = 'health-chip muted-chip';
      }
    }

    const inspector = document.getElementById(`display-inspector-${row.id}`);
    if (inspector) {
      const status = inspector.querySelector('[data-inspector-status]'); if (status) status.textContent = row.online ? 'Online' : 'Offline';
      const player = inspector.querySelector('[data-inspector-player]'); if (player) player.textContent = titleCase(row.display_app_state);
      const inspectorSync = inspector.querySelector('[data-inspector-sync]'); if (inspectorSync) inspectorSync.textContent = titleCase(row.sync_state);
      const inspectorCpu = inspector.querySelector('[data-inspector-cpu]'); if (inspectorCpu) inspectorCpu.textContent = row.cpu_temp || 'Unknown';
      const inspectorDisk = inspector.querySelector('[data-inspector-disk]'); if (inspectorDisk) inspectorDisk.textContent = row.disk_usage || 'Unknown';
      const progressWrap = inspector.querySelector('[data-inspector-job]');
      const job = row.job || {};
      if (progressWrap) {
        progressWrap.hidden = !job.active_count;
        const jobName = progressWrap.querySelector('[data-inspector-job-name]'); if (jobName) jobName.textContent = titleCase(job.type);
        const jobProgress = progressWrap.querySelector('[data-inspector-job-progress]'); if (jobProgress) jobProgress.textContent = `${job.progress || 0}%`;
        const jobBar = progressWrap.querySelector('[data-inspector-job-bar]'); if (jobBar) jobBar.value = job.progress || 0;
      }
    }
    refreshPreview(card.querySelector('[data-live-preview]'), row.preview_url);
    if (wasOnline !== row.online) {
      card.classList.remove('live-updated'); void card.offsetWidth; card.classList.add('live-updated');
    }
  }

  let refreshTimer = null;
  async function refreshFleet() {
    if (document.hidden) return;
    liveState?.classList.remove('is-stale');
    liveState?.classList.add('is-refreshing');
    try {
      const response = await fetch('/displays/api/status', { headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      data.rows?.forEach(updateCard);
      const online = document.querySelector('[data-online-count]'); if (online) online.textContent = data.online;
      const offline = document.querySelector('[data-offline-count]'); if (offline) offline.textContent = data.offline;
      const attention = document.querySelector('[data-attention-count]'); if (attention) attention.textContent = data.attention ?? 0;
      const activeJobs = document.querySelector('[data-active-jobs]'); if (activeJobs) activeJobs.textContent = data.active_jobs ?? 0;
      if (liveState) liveState.lastChild.textContent = ' Live';
    } catch (error) {
      console.warn('Fleet live refresh failed', error);
      liveState?.classList.add('is-stale');
      if (liveState) liveState.lastChild.textContent = ' Paused';
    } finally {
      liveState?.classList.remove('is-refreshing');
    }
  }

  function scheduleRefresh() {
    window.clearInterval(refreshTimer);
    refreshTimer = window.setInterval(refreshFleet, 15000);
  }
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) { refreshFleet(); scheduleRefresh(); }
  });
  scheduleRefresh();
});
