(() => {
  const root = document.querySelector(
    "[data-automatic-rollback]"
  );

  if (!root) return;

  const displayId = root.dataset.displayId;
  const timeout = root.dataset.timeout || "180";

  const escapeHtml = (value) => {
    const element = document.createElement("div");
    element.textContent =
      value === undefined || value === null
        ? ""
        : String(value);
    return element.innerHTML;
  };

  const render = (data) => {
    const verification =
      data.verification || {};
    const state = verification.state || "idle";

    if (
      state !== "verification_failed" &&
      !data.queued
    ) {
      root.hidden = true;
      return;
    }

    root.hidden = false;

    let title = "Automatic rollback protection";
    let detail = data.message || "";
    let status = "Watching";

    if (data.queued) {
      title = "Rollback queued";
      status = "Queued";
    } else if (
      typeof data.seconds_remaining === "number" &&
      data.seconds_remaining > 0
    ) {
      status = `${data.seconds_remaining}s`;
      detail =
        `Waiting ${data.seconds_remaining} seconds for ` +
        "the target heartbeat before rollback.";
    } else if (data.eligible) {
      status = "Due";
    }

    root.innerHTML = `
      <div>
        <strong>${escapeHtml(title)}</strong>
        <p class="muted">${escapeHtml(detail)}</p>
      </div>
      <span class="status-pill">${escapeHtml(status)}</span>
    `;
  };

  const refresh = async () => {
    try {
      const response = await fetch(
        `/display/${encodeURIComponent(displayId)}` +
        `/automatic-rollback?timeout=${encodeURIComponent(timeout)}` +
        `&t=${Date.now()}`,
        {
          credentials: "same-origin",
          cache: "no-store",
        }
      );

      if (!response.ok) return;

      const data = await response.json();
      if (data.ok) render(data);
    } catch (_) {
      // Keep the last rendered state.
    }
  };

  refresh();
  window.setInterval(refresh, 5000);
})();
