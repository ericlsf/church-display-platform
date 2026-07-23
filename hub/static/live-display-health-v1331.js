(() => {
  const root = document.querySelector("[data-live-display]");
  if (!root) return;

  const displayId = root.dataset.liveDisplay;
  const fields = {
    status: root.querySelector("[data-live-status]"),
    statusBadge: root.querySelector("[data-live-status-badge]"),
    version: root.querySelector("[data-live-version]"),
    media: root.querySelector("[data-live-media]"),
    temp: root.querySelector("[data-live-temp]"),
    memory: root.querySelector("[data-live-memory]"),
    storage: root.querySelector("[data-live-storage]"),
    heartbeat: root.querySelector("[data-live-heartbeat]"),
    ip: root.querySelector("[data-live-ip]"),
    hostname: root.querySelector("[data-live-hostname]"),
    uptime: root.querySelector("[data-live-uptime]"),
    player: root.querySelector("[data-live-player]"),
    currentMedia: root.querySelector("[data-live-current-media]"),
    sync: root.querySelector("[data-live-sync]"),
  };

  const present = (value) => value !== null && value !== undefined && value !== "" && String(value).toLowerCase() !== "unknown";
  const text = (value, fallback = "Unknown") => present(value) ? String(value) : fallback;
  const percent = (value) => {
    if (!present(value)) return "Unknown";
    const raw = String(value).trim();
    return raw.includes("%") ? raw : `${raw}%`;
  };
  const temperature = (value) => {
    if (!present(value)) return "Unknown";
    const raw = String(value).trim();
    return /°|c$/i.test(raw) ? raw : `${raw}°C`;
  };
  const statusLabel = (row) => text(row.readiness || row.status || (row.online ? "ready" : "offline"), "Unknown").replaceAll("_", " ");

  const render = (row) => {
    const status = statusLabel(row);
    if (fields.status) fields.status.textContent = status;
    if (fields.statusBadge) {
      fields.statusBadge.textContent = status;
      fields.statusBadge.dataset.state = status.toLowerCase().replaceAll(" ", "-");
    }
    if (fields.version) fields.version.textContent = text(row.version);
    if (fields.media) fields.media.textContent = text(row.media_count ?? row.media?.total, "0");
    if (fields.temp) fields.temp.textContent = temperature(row.cpu_temp ?? row.cpu_temperature);
    if (fields.memory) fields.memory.textContent = percent(row.memory_usage ?? row.memory_percent);
    if (fields.storage) fields.storage.textContent = percent(row.disk_usage ?? row.storage_percent ?? row.disk_percent);
    if (fields.heartbeat) fields.heartbeat.textContent = text(row.heartbeat ?? row.last_heartbeat ?? row.last_seen);
    if (fields.ip) fields.ip.textContent = text(row.ip_address, "Not reported");
    if (fields.hostname) fields.hostname.textContent = text(row.hostname, displayId);
    if (fields.uptime) fields.uptime.textContent = text(row.uptime);
    if (fields.player) fields.player.textContent = text(row.player_state ?? row.display_app_state);
    if (fields.currentMedia) fields.currentMedia.textContent = text(row.current_media, "Nothing reported");
    if (fields.sync) fields.sync.textContent = text(row.sync_state);
  };

  const update = async () => {
    try {
      // This endpoint uses the same normalization as the working All Displays
      // page. Do not use raw /api/v1/fleet-state here: its system metrics are
      // nested and previously overwrote valid values with Unknown.
      const response = await fetch("/displays/api/status", {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Live health unavailable");
      const data = await response.json();
      const row = (data.rows || []).find((item) => item.id === displayId);
      if (row) render(row);
    } catch (_) {
      // Preserve the last successful/server-rendered values.
    }
  };

  update();
  window.setInterval(update, 15000);
})();
