(() => {
  const root = document.querySelector("[data-command-center]");
  if (!root) return;
  const updated = root.querySelector("[data-last-updated]");
  const liveDot = root.querySelector("[data-live-dot]");
  const toastStack = root.querySelector("[data-toast-stack]");
  const drawer = root.querySelector("[data-job-drawer]");
  const palette = root.querySelector("[data-command-palette]");
  const paletteSearch = root.querySelector("[data-command-search]");
  let lastGeneratedAt = null;
  let knownJobs = new Map();

  const showToast = (message) => {
    const toast = document.createElement("div"); toast.className = "command-toast"; toast.textContent = message;
    toastStack?.append(toast); setTimeout(() => toast.remove(), 5000);
  };
  const relativeTime = (iso) => {
    if (!iso) return "Live";
    const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    if (seconds < 5) return "Updated just now"; if (seconds < 60) return `Updated ${seconds}s ago`; return `Updated ${Math.floor(seconds / 60)}m ago`;
  };
  const setOpen = (el, open) => { el?.classList.toggle("open", open); el?.setAttribute("aria-hidden", String(!open)); document.body.style.overflow = open ? "hidden" : ""; };
  root.querySelectorAll("[data-open-jobs]").forEach((b) => b.addEventListener("click", () => setOpen(drawer, true)));
  root.querySelectorAll("[data-close-jobs]").forEach((b) => b.addEventListener("click", () => setOpen(drawer, false)));
  root.querySelectorAll("[data-close-palette]").forEach((b) => b.addEventListener("click", () => setOpen(palette, false)));

  const openPalette = () => { setOpen(palette, true); paletteSearch.value = ""; filterCommands(); setTimeout(() => paletteSearch.focus(), 20); };
  const filterCommands = () => {
    const q = (paletteSearch?.value || "").trim().toLowerCase();
    root.querySelectorAll("[data-command-item]").forEach((item) => item.hidden = q && !item.dataset.search.includes(q));
  };
  paletteSearch?.addEventListener("input", filterCommands);
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openPalette(); }
    if (event.key === "Escape") { setOpen(drawer, false); setOpen(palette, false); }
  });
  document.querySelectorAll("button, a").forEach((el) => {
    if ((el.textContent || "").trim().toLowerCase().includes("commands")) el.addEventListener("click", (e) => { e.preventDefault(); openPalette(); });
  });

  const updateMetrics = (summary) => {
    Object.entries(summary || {}).forEach(([key, value]) => root.querySelectorAll(`[data-summary="${key}"]`).forEach((target) => target.textContent = value));
    const ring = root.querySelector(".health-ring"); if (ring && summary?.health_percent != null) ring.style.setProperty("--health", summary.health_percent);
  };
  const renderJobs = (jobs) => {
    const list = root.querySelector("[data-job-drawer-list]"); if (!list) return;
    if (!jobs?.length) { list.innerHTML = '<div class="command-empty">No active jobs.</div>'; return; }
    list.innerHTML = jobs.map((job) => `<article class="drawer-job"><div><strong>${String(job.type || "job").replaceAll("_", " ")}</strong><span>${job.display_id || "Fleet"}</span></div><span class="status-pill">${job.status || "Running"}</span><div class="drawer-progress"><span style="width:${Number(job.progress || 0)}%"></span></div><small>${Number(job.progress || 0)}%</small></article>`).join("");
  };
  const checkCompletedJobs = (jobs) => {
    const current = new Map(); (jobs || []).forEach((job) => current.set(String(job.id), String(job.status || "")));
    knownJobs.forEach((status, id) => { if (!current.has(id) && ["running","queued","pending","retrying","in_progress"].includes(status.toLowerCase())) showToast("A fleet job completed."); }); knownJobs = current;
  };
  const refresh = async () => {
    liveDot?.classList.add("refreshing");
    try {
      const response = await fetch("/command-center/summary", {credentials:"same-origin",cache:"no-store"}); if (!response.ok) throw new Error();
      const data = await response.json(); updateMetrics(data.summary); checkCompletedJobs(data.active_jobs || []); renderJobs(data.active_jobs || []); lastGeneratedAt = data.generated_at; if (updated) updated.textContent = relativeTime(lastGeneratedAt);
    } catch (_) { if (updated) updated.textContent = "Refresh unavailable"; }
    finally { liveDot?.classList.remove("refreshing"); }
  };
  refresh(); setInterval(refresh, 10000); setInterval(() => { if (updated && lastGeneratedAt) updated.textContent = relativeTime(lastGeneratedAt); }, 1000);
})();
