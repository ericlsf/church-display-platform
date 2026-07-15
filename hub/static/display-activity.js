(() => {
  const container = document.getElementById("display-activity");
  const button = document.getElementById("refresh-display-activity");

  if (!container) {
    return;
  }

  const displayId = container.dataset.displayId;

  const escapeHtml = (value) => {
    const node = document.createElement("div");
    node.textContent = value ?? "";
    return node.innerHTML;
  };

  const load = async () => {
    container.innerHTML = '<p class="muted">Loading recent activity…</p>';

    try {
      const response = await fetch(
        `/operator/activity/${encodeURIComponent(displayId)}`,
        {
          credentials: "same-origin",
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const events = Array.isArray(data.events) ? data.events : [];

      if (!events.length) {
        container.innerHTML =
          '<p class="muted">No activity in the last 10 minutes.</p>';
        return;
      }

      container.innerHTML = events.map((event) => `
        <div class="activity-item">
          <time>${escapeHtml(event.timestamp)}</time>
          <div>
            <strong>${escapeHtml(event.title)}</strong>
            <span class="muted">${escapeHtml(event.message || "")}</span>
          </div>
          <span class="status-pill">${escapeHtml(event.status)}</span>
        </div>
      `).join("");
    } catch (error) {
      container.innerHTML =
        '<p class="offline">Recent activity could not be loaded.</p>';
    }
  };

  button?.addEventListener("click", load);
  load();
  window.setInterval(load, 30000);
})();
