(() => {
  const root = document.querySelector("[data-command-center]");
  if (!root) return;

  const liveDot = root.querySelector("[data-live-dot]");
  const updated = root.querySelector("[data-last-updated]");
  const toastStack = root.querySelector("[data-toast-stack]");
  let lastGeneratedAt = null;
  let knownJobs = new Map();

  const showToast = (message) => {
    if (!toastStack) return;
    const toast = document.createElement("div");
    toast.className = "command-toast";
    toast.textContent = message;
    toastStack.append(toast);
    window.setTimeout(() => toast.remove(), 5000);
  };

  const relativeTime = (iso) => {
    if (!iso) return "Live";
    const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    if (seconds < 5) return "Updated just now";
    if (seconds < 60) return `Updated ${seconds}s ago`;
    return `Updated ${Math.floor(seconds / 60)}m ago`;
  };

  const updateMetrics = (summary) => {
    Object.entries(summary || {}).forEach(([key, value]) => {
      const target = root.querySelector(`[data-summary="${key}"]`);
      if (target) target.textContent = value;
    });
  };

  const checkCompletedJobs = (jobs) => {
    const current = new Map();
    (jobs || []).forEach((job) => current.set(String(job.id), String(job.status || "")));
    knownJobs.forEach((status, id) => {
      if (!current.has(id) && ["running", "queued", "pending", "retrying", "in_progress"].includes(status.toLowerCase())) {
        showToast("A fleet job completed.");
      }
    });
    knownJobs = current;
  };

  const refresh = async () => {
    liveDot?.classList.add("refreshing");
    try {
      const response = await fetch("/command-center/summary", {credentials: "same-origin", cache: "no-store"});
      if (!response.ok) return;
      const data = await response.json();
      updateMetrics(data.summary);
      checkCompletedJobs(data.active_jobs || []);
      lastGeneratedAt = data.generated_at;
      if (updated) updated.textContent = relativeTime(lastGeneratedAt);
    } catch (_) {
      if (updated) updated.textContent = "Refresh unavailable";
    } finally {
      liveDot?.classList.remove("refreshing");
    }
  };

  refresh();
  window.setInterval(refresh, 10000);
  window.setInterval(() => {
    if (updated && lastGeneratedAt) updated.textContent = relativeTime(lastGeneratedAt);
  }, 1000);
})();
