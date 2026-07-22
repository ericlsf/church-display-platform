(() => {
  const root = document.querySelector("[data-screenshot-workspace]");
  if (!root) return;

  const displayId = root.dataset.displayId;
  const image = root.querySelector("[data-screenshot-image]");
  const empty = root.querySelector("[data-screenshot-empty]");
  const requestButton = root.querySelector("[data-screenshot-request]");
  const freshness = root.querySelector("[data-screenshot-freshness]");
  const state = root.querySelector("[data-screenshot-state]");
  const message = root.querySelector("[data-screenshot-message]");
  const fullLink = root.querySelector("[data-screenshot-full]");
  const openButton = root.querySelector("[data-screenshot-open]");
  let lastUrl = "";

  const humanAge = (seconds) => {
    if (seconds == null) return "Unavailable";
    if (seconds < 5) return "Just now";
    if (seconds < 60) return `${seconds}s old`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m old`;
    return `${Math.floor(minutes / 60)}h old`;
  };

  const render = (data) => {
    const url = data.preview_url || "";
    const age = data.preview_age_seconds;
    freshness.textContent = humanAge(age);
    freshness.classList.toggle("fresh", age != null && age <= 90);
    freshness.classList.toggle("stale", age != null && age > 90);

    if (url) {
      if (url !== lastUrl) {
        image.src = url;
        lastUrl = url;
      }
      image.hidden = false;
      empty.hidden = true;
      fullLink.href = url;
      fullLink.hidden = false;
      state.textContent = "Latest player capture";
    } else {
      image.hidden = true;
      empty.hidden = false;
      fullLink.hidden = true;
      state.textContent = "No capture received";
    }

    const job = data.latest_job;
    if (job && ["queued", "running"].includes(job.status)) {
      message.textContent = job.status === "running" ? "Capturing screenshot…" : "Screenshot request queued…";
      requestButton.disabled = true;
      root.classList.add("is-loading");
    } else {
      requestButton.disabled = false;
      root.classList.remove("is-loading");
      if (job?.status === "failed") message.textContent = job.message || "Screenshot capture failed.";
      else message.textContent = "Player captures also refresh automatically.";
    }
  };

  const refresh = async () => {
    try {
      const response = await fetch(`/api/v1/displays/${encodeURIComponent(displayId)}/screenshot`, {cache: "no-store", credentials: "same-origin"});
      if (!response.ok) throw new Error("Screenshot status unavailable");
      render(await response.json());
    } catch (error) {
      message.textContent = error.message;
    }
  };

  requestButton.addEventListener("click", async () => {
    requestButton.disabled = true;
    message.textContent = "Queueing screenshot…";
    try {
      const response = await fetch(`/api/v1/displays/${encodeURIComponent(displayId)}/screenshot`, {
        method: "POST",
        credentials: "same-origin",
        headers: {"Accept": "application/json"},
      });
      if (!response.ok) throw new Error("Unable to queue screenshot");
      message.textContent = "Screenshot request queued…";
      window.setTimeout(refresh, 1000);
    } catch (error) {
      requestButton.disabled = false;
      message.textContent = error.message;
    }
  });

  const lightbox = document.createElement("div");
  lightbox.className = "screenshot-lightbox";
  lightbox.hidden = true;
  lightbox.innerHTML = '<button type="button" aria-label="Close screenshot">×</button><img alt="Full-size display screenshot">';
  document.body.appendChild(lightbox);
  const lightboxImage = lightbox.querySelector("img");
  const close = () => { lightbox.hidden = true; };
  lightbox.querySelector("button").addEventListener("click", close);
  lightbox.addEventListener("click", (event) => { if (event.target === lightbox) close(); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(); });
  openButton.addEventListener("click", () => {
    if (!lastUrl) return;
    lightboxImage.src = lastUrl;
    lightbox.hidden = false;
  });

  refresh();
  window.setInterval(refresh, 10000);
})();
