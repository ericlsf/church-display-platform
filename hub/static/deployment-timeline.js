(() => {
  const root = document.querySelector("[data-deployment-timeline]");
  if (!root) return;
  const displayId = root.dataset.displayId;
  const refresh = async () => {
    try {
      const r = await fetch(`/display/${encodeURIComponent(displayId)}/deployment-timeline`, {credentials:"same-origin",cache:"no-store"});
      if (!r.ok) return;
      const data = await r.json();
      root.innerHTML = (data.stages || []).map(s => `
        <div class="deployment-stage ${s.state}">
          <span class="deployment-stage-dot"></span><span>${s.label}</span>
        </div>`).join("");
    } catch (_) {}
  };
  refresh();
  setInterval(refresh, 15000);
})();
