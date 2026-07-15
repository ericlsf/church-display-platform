(() => {
  const badge = document.querySelector("[data-notification-badge]");
  const link = document.querySelector("[data-notification-link]");

  if (!badge || !link) {
    return;
  }

  const refresh = async () => {
    try {
      const response = await fetch("/notifications/summary", {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      const unread = Number(data.unread || 0);

      badge.textContent = unread > 99 ? "99+" : String(unread);
      badge.hidden = unread < 1;
      link.setAttribute(
        "aria-label",
        unread
          ? `Notifications, ${unread} unread`
          : "Notifications"
      );
    } catch (_) {
      // Leave existing badge state unchanged.
    }
  };

  refresh();
  window.setInterval(refresh, 30000);
})();
