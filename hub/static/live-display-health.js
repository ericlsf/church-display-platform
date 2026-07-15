(() => {
  const root = document.querySelector("[data-live-display]");
  if (!root) return;

  const displayId = root.dataset.liveDisplay;
  const status = document.querySelector("[data-live-status]");
  const version = document.querySelector("[data-live-version]");
  const media = document.querySelector("[data-live-media]");
  const temp = document.querySelector("[data-live-temp]");
  const storage = document.querySelector("[data-live-storage]");
  const heartbeat = document.querySelector("[data-live-heartbeat]");
  const preview = document.querySelector("[data-live-preview]");

  const update = async () => {
    try {
      const response = await fetch(
        `/api/v1/fleet-state?display_id=${encodeURIComponent(displayId)}`,
        {credentials: "same-origin", cache: "no-store"}
      );
      if (!response.ok) return;

      const data = await response.json();
      const rows = Array.isArray(data.rows)
        ? data.rows
        : Array.isArray(data.displays)
          ? data.displays
          : [];
      const row = rows.find((item) => item.id === displayId) || data.display;
      if (!row) return;

      if (status) status.textContent = (row.readiness || row.status || "unknown").replaceAll("_", " ");
      if (version) version.textContent = row.version || "unknown";
      if (media) media.textContent = row.media_count ?? row.media?.total ?? 0;
      if (temp) temp.textContent = row.cpu_temperature != null ? `${row.cpu_temperature}°C` : "Unknown";
      if (storage) {
        const used = row.storage_percent ?? row.disk_percent;
        storage.textContent = used != null ? `${used}% used` : "Unknown";
      }
      if (heartbeat) heartbeat.textContent = row.last_heartbeat || row.last_seen || "Unknown";

      const previewUrl = row.preview_url || row.screenshot_url;
      if (preview && previewUrl) {
        preview.src = `${previewUrl}${previewUrl.includes("?") ? "&" : "?"}t=${Date.now()}`;
        preview.hidden = false;
        preview.parentElement?.querySelector(".preview-empty")?.setAttribute("hidden", "");
      }
    } catch (_) {
      // Preserve the last successful values.
    }
  };

  update();
  window.setInterval(update, 15000);
})();
