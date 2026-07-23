(() => {
  const root = document.querySelector("[data-deployment-center]");
  if (!root) return;
  const refresh = async () => {
    try {
      const response = await fetch("/api/v1/deployment-center", {cache: "no-store", credentials: "same-origin"});
      if (!response.ok) return;
      const state = await response.json();
      Object.entries(state.summary || {}).forEach(([key, value]) => {
        const node = root.querySelector(`[data-summary="${key}"]`);
        if (node) node.textContent = String(value);
      });
    } catch (_) {}
  };
  window.setInterval(refresh, 15000);
})();
