(() => {
  const root = document.querySelector("[data-command-summary]");
  if (!root) return;
  const refresh = async () => {
    try {
      const response = await fetch("/command-center/summary", {credentials: "same-origin", cache: "no-store"});
      if (!response.ok) return;
      const data = await response.json();
      Object.entries(data.summary || {}).forEach(([key, value]) => {
        const target = document.querySelector(`[data-summary="${key}"]`);
        if (target) target.textContent = value;
      });
    } catch (_) {}
  };
  refresh();
  window.setInterval(refresh, 30000);
})();
