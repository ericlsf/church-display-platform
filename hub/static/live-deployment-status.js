(() => {
  const page = document.querySelector("[data-live-display]");
  if (!page) return;
  const displayId = page.dataset.liveDisplay;
  if (!displayId) return;

  const qs = (selector) => document.querySelector(selector);

  const setText = (selector, value) => {
    const element = qs(selector);
    if (element && value !== undefined && value !== null) {
      element.textContent = String(value);
    }
  };

  const updateTopCard = (verification) => {
    const card = qs(".update-stat-card");
    if (!card) return;

    const reported = verification.reported_version || "unknown";
    const target = verification.target_version || "";
    const state = verification.state || "idle";
    const job = verification.job || {};
    const progress = Number(job.progress || 0);

    card.dataset.deploymentState = state;

    const label = card.querySelector(
      ".update-available-label, [data-update-label]"
    );
    const strong = card.querySelector("strong");
    const form = card.querySelector("form");

    if (state === "deploying") {
      if (label) label.textContent = "Upgrade in progress";
      if (strong) strong.textContent = `${progress}%`;
      if (form) form.hidden = true;
    } else if (state === "verified") {
      if (label) label.textContent = "Version verified";
      if (strong) strong.textContent = reported;
      if (form) form.hidden = true;
    } else if (state === "verification_failed") {
      if (label) label.textContent = "Verification failed";
      if (strong) {
        strong.textContent = target
          ? `${reported} → ${target}`
          : reported;
      }
      if (form) form.hidden = false;
    } else if (state === "failed") {
      if (label) label.textContent = "Deployment failed";
      if (strong) strong.textContent = reported;
      if (form) form.hidden = false;
    } else {
      if (label) label.textContent = "Software Current";
      if (strong) strong.textContent = reported;
    }
  };

  const updateVerification = (verification) => {
    const root = qs("[data-deployment-verification]");
    if (!root) return;

    const labels = {
      idle: "No recent deployment",
      deploying: "Deployment in progress",
      verified: "Version verified",
      verification_failed: "Verification failed",
      failed: "Deployment failed",
    };

    const state = verification.state || "idle";
    root.dataset.state = state;

    const status = root.querySelector("[data-verification-status]");
    const detail = root.querySelector("[data-verification-detail]");

    if (status) status.textContent = labels[state] || state;
    if (detail) detail.textContent = verification.message || "";
  };

  const updateTimeline = (timeline) => {
    const root = qs("[data-deployment-timeline]");
    if (!root || !Array.isArray(timeline.stages)) return;

    root.innerHTML = timeline.stages.map((stage) => `
      <div class="deployment-stage ${stage.state}">
        <span class="deployment-stage-dot"></span>
        <span>${stage.label}</span>
      </div>
    `).join("");
  };

  const refresh = async () => {
    try {
      const stamp = Date.now();

      const [verificationResponse, timelineResponse] =
        await Promise.all([
          fetch(
            `/display/${encodeURIComponent(displayId)}/deployment-verification?t=${stamp}`,
            {credentials: "same-origin", cache: "no-store"}
          ),
          fetch(
            `/display/${encodeURIComponent(displayId)}/deployment-timeline?t=${stamp}`,
            {credentials: "same-origin", cache: "no-store"}
          ),
        ]);

      if (verificationResponse.ok) {
        const verification = await verificationResponse.json();
        if (verification.ok) {
          updateVerification(verification);
          updateTopCard(verification);
          setText("[data-live-version]", verification.reported_version);
        }
      }

      if (timelineResponse.ok) {
        const timeline = await timelineResponse.json();
        if (timeline.ok) updateTimeline(timeline);
      }
    } catch (_) {
      // Preserve the last successfully rendered state.
    }
  };

  refresh();
  window.setInterval(refresh, 5000);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refresh();
  });

  window.addEventListener("focus", refresh);
})();
